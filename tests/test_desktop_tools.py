import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('desktop_builder', ROOT / 'scripts/build-desktop-tools.py')
BUILDER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILDER)


class DesktopDistributionTests(unittest.TestCase):
    def test_reproducible_complete_packages_and_immutable_versions(self):
        with tempfile.TemporaryDirectory(prefix='desktop-tools-build-', dir=os.environ.get('TEMP')) as temporary:
            output = Path(temporary)
            core = Path(os.environ['TIKBIT_PPT_CORE']) if os.environ.get('TIKBIT_PPT_CORE') else output / 'fixture-core.zip'
            if not core.exists():
                with zipfile.ZipFile(core, 'w') as archive:
                    archive.writestr('skills/ppt-test/SKILL.md', '---\nname: ppt-test\ndescription: Test presentation packaging\n---\n# PPT test\n')
            BUILDER.build(output, {'ppt-core': core})
            initial = {file.name: file.read_bytes() for file in (output / 'packages').glob('*.zip')}
            BUILDER.build(output, {'ppt-core': core})
            self.assertEqual(initial, {file.name: file.read_bytes() for file in (output / 'packages').glob('*.zip')})
            catalog = json.loads((output / 'catalog.json').read_text(encoding='utf-8'))
            self.assertEqual(len(catalog['tools']), 18)
            installable = [tool for tool in catalog['tools'] if 'install' in tool]
            self.assertEqual(len(installable), 18)
            for tool in installable:
                info = tool['install']
                package = output / 'packages' / info['url'].split('/')[-1]
                self.assertEqual(info['sha256'], hashlib.sha256(package.read_bytes()).hexdigest())
                with zipfile.ZipFile(package) as archive:
                    manifest = json.loads(archive.read('manifest.json'))
                    self.assertEqual(manifest['skills'], info['skills'])
                    self.assertEqual(set(archive.namelist()), {'manifest.json'} | {file['path'] for file in manifest['files']})
                    for file in manifest['files']:
                        data = archive.read(file['path'])
                        self.assertEqual(len(data), file['bytes'])
                        self.assertEqual(hashlib.sha256(data).hexdigest(), file['sha256'])
                    for skill in info['skills']:
                        self.assertIn(f'skills/{skill}/SKILL.md', archive.namelist())
            first = next((output / 'packages').glob('*.zip'))
            first.write_bytes(b'published-other-bytes')
            with self.assertRaisesRegex(ValueError, 'increase VERSION'):
                BUILDER.build(output, {'ppt-core': core})
            self.assertEqual(first.read_bytes(), b'published-other-bytes')

    def test_source_archive_traversal_is_rejected(self):
        with tempfile.TemporaryDirectory(prefix='desktop-tools-source-', dir=os.environ.get('TEMP')) as temporary:
            source = Path(temporary) / 'unsafe.zip'
            with zipfile.ZipFile(source, 'w') as archive:
                archive.writestr('../outside.md', 'Not allowed')
            with self.assertRaisesRegex(ValueError, 'Unsafe source archive'):
                BUILDER.archive_payload(source, {})

    def test_python_launcher_uses_prepared_interpreter_and_isolated_packages(self):
        node = shutil.which('node')
        self.assertIsNotNone(node)
        with tempfile.TemporaryDirectory(prefix='desktop-runtime-', dir=os.environ.get('TEMP')) as temporary:
            root = Path(temporary)
            runtime = root / '.tikbit/tool-runtime'
            site = runtime / 'python-packages'
            site.mkdir(parents=True)
            (runtime / 'runtime.json').write_text(json.dumps({'python': sys.executable}), encoding='utf-8')
            (site / 'tikbit_runtime_probe.py').write_text('VALUE = "prepared-runtime"\n', encoding='utf-8')
            skill = root / 'skill'
            skill.mkdir()
            shutil.copy2(ROOT / 'desktop-skills/python-runner.cjs', skill / 'python.cjs')
            (skill / 'probe.py').write_text('from tikbit_runtime_probe import VALUE\nprint(VALUE)\n', encoding='utf-8')
            result = subprocess.run([node, str(skill / 'python.cjs'), 'probe.py'], cwd=root,
                                    env={**os.environ, 'HOME': str(root), 'USERPROFILE': str(root)},
                                    capture_output=True, text=True, timeout=15,
                                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), 'prepared-runtime')

    def test_voice_launcher_passes_vault_context_and_can_check_silently(self):
        if os.name != 'nt':
            self.skipTest('Windows PowerShell dry-run; macOS playback is a native acceptance step')
        with tempfile.TemporaryDirectory(prefix='desktop-voice-', dir=os.environ.get('TEMP')) as temporary:
            root = Path(temporary)
            with zipfile.ZipFile(ROOT / 'desktop/packages/voice-notification-0.3.2.zip') as archive:
                archive.extractall(root)
            runner = root / 'skills/task-voice-notification/run.cjs'
            result = subprocess.run([shutil.which('node'), str(runner), 'done', '.custom-host', '--dry-run'],
                                    cwd=root, env={**os.environ, 'HOME': str(root), 'USERPROFILE': str(root)},
                                    capture_output=True, text=True, encoding='utf-8-sig', timeout=20,
                                    creationflags=subprocess.CREATE_NO_WINDOW)
            self.assertEqual(result.returncode, 0, result.stderr)
            decision = json.loads(result.stdout)
            self.assertFalse(decision['allowed'])
            self.assertFalse((runner.parent / 'resources/engine/.flag').exists())


if __name__ == '__main__':
    unittest.main()
