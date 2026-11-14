import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('web_design_builder', ROOT / 'scripts/build-desktop-tools.py')
BUILDER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILDER)


class WebDesignDistributionTests(unittest.TestCase):
    def test_targeted_build_retains_other_tools_and_bundles_revision_skill(self):
        before = json.loads((ROOT / 'desktop/catalog.json').read_text(encoding='utf-8'))
        with tempfile.TemporaryDirectory(prefix='web-design-build-') as temporary:
            output = Path(temporary)
            BUILDER.build(output, tool_ids=['web-design'])
            after = json.loads((output / 'catalog.json').read_text(encoding='utf-8'))
            old = {entry['id']: entry for entry in before['tools']}
            new = {entry['id']: entry for entry in after['tools']}
            self.assertEqual(set(old), set(new))
            for tool_id in old:
                if tool_id != 'web-design':
                    self.assertEqual(old[tool_id], new[tool_id], tool_id)
            entry = new['web-design']['install']
            self.assertEqual(entry['version'], '0.2.0')
            self.assertEqual(set(entry['skills']), {'frontend-design', 'web-design-engineer', 'unslop'})
            package = output / 'packages' / entry['url'].split('/')[-1]
            raw = package.read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), entry['sha256'])
            self.assertEqual(len(raw), entry['bytes'])
            BUILDER.build(output, tool_ids=['web-design'])
            self.assertEqual(raw, package.read_bytes())
            with zipfile.ZipFile(package) as archive:
                manifest = json.loads(archive.read('manifest.json'))
                self.assertEqual(set(manifest['skills']), set(entry['skills']))
                self.assertEqual(set(archive.namelist()), {'manifest.json'} | {file['path'] for file in manifest['files']})
                required = ['skills/unslop/SKILL.md', 'skills/unslop/LICENSE',
                            'skills/unslop/references/usage-boundaries.md',
                            'skills/unslop/references/signs.md',
                            'skills/unslop/references/tokens.md',
                            'skills/unslop/references/refs/unslop-dashboard-after.webp',
                            'skills/unslop/scripts/snapshot.mjs', 'skills/unslop/scripts/story.mjs']
                for name in required:
                    self.assertIn(name, archive.namelist())
                installs = {}
                for engine, directory in [('claude', '.claude'), ('codex', '.agents')]:
                    target = output / engine / directory
                    for item in manifest['files']:
                        name = item['path']
                        self.assertTrue(name.startswith('skills/'))
                        self.assertFalse({'..', '.git', 'node_modules', '__pycache__'} & set(Path(name).parts))
                        content = archive.read(name)
                        self.assertEqual(len(content), item['bytes'])
                        self.assertEqual(hashlib.sha256(content).hexdigest(), item['sha256'])
                        installed = target / name
                        installed.parent.mkdir(parents=True, exist_ok=True)
                        installed.write_bytes(content)
                    installs[engine] = target
                    for skill in entry['skills']:
                        self.assertTrue((target / 'skills' / skill / 'SKILL.md').is_file())
                    for file in (target / 'skills/unslop').rglob('*.md'):
                        if 'resources' in file.relative_to(target / 'skills/unslop').parts:
                            continue
                        text = file.read_text(encoding='utf-8')
                        self.assertNotIn('公司知识库', text)
                        self.assertNotIn('01_📐规范', text)
                        self.assertNotIn('Administrator', text)
                        self.assertNotIn('WeDrive', text)
                        for href in re.findall(r'\]\(([^)]+)\)', text):
                            if href.startswith(('http:', 'https:', '#')):
                                continue
                            self.assertTrue((file.parent / href.split('#')[0]).is_file(), (file, href))
                    boundary = target / 'skills/unslop/references/usage-boundaries.md'
                    self.assertTrue(boundary.is_file())
                left, right = installs['claude'], installs['codex']
                for item in manifest['files']:
                    self.assertEqual((left / item['path']).read_bytes(), (right / item['path']).read_bytes())
            package.write_bytes(b'published-different-content')
            with self.assertRaisesRegex(ValueError, 'increase VERSION'):
                BUILDER.build(output, tool_ids=['web-design'])


if __name__ == '__main__':
    unittest.main()
