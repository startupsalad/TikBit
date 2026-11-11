import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('desktop_publish', ROOT / 'scripts/publish-desktop-tools.py')
PUBLISH = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PUBLISH)
PUBLISHED_CATALOG = PUBLISH.published_catalog


class DesktopPublishTests(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch.object(PUBLISH, 'published_catalog', side_effect=lambda raw: raw))

    def test_uses_official_bytes_despite_local_line_endings_and_rejects_unpublished_changes(self):
        raw = b'{\n  "schemaVersion": 2,\n  "tools": []\n}\n'
        with patch.object(PUBLISH.urllib.request, 'build_opener') as opener:
            response = opener.return_value.open.return_value.__enter__.return_value
            response.status = 200
            response.read.return_value = json.dumps({'encoding': 'base64', 'content': PUBLISH.base64.b64encode(raw).decode()}).encode()
            self.assertEqual(PUBLISHED_CATALOG(raw.replace(b'\n', b'\r\n')), raw)
            with self.assertRaisesRegex(ValueError, 'matching GitHub'):
                PUBLISHED_CATALOG(b'{"schemaVersion":1,"tools":[]}')

    def test_immutable_upload_sends_server_enforced_overwrite_guard(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            file = root / 'package.zip'
            file.write_bytes(b'zip')
            config = root / 'oss.ini'
            config.write_text('[Credentials]\naccessKeyID=example\naccessKeySecret=example-secret\nstsToken=\n', encoding='utf-8')
            with patch.object(PUBLISH.urllib.request, 'build_opener') as opener:
                response = opener.return_value.open.return_value.__enter__.return_value
                response.status = 200
                PUBLISH.upload(file, 'packages/example-1.0.0.zip', True, config)
                request = opener.return_value.open.call_args.args[0]
                self.assertEqual(request.full_url, PUBLISH.BASE + 'packages/example-1.0.0.zip')
                self.assertEqual(request.get_header('X-oss-forbid-overwrite'), 'true')
                self.assertEqual(request.get_header('X-oss-meta-sha256'), PUBLISH.sha(b'zip'))
                self.assertEqual(request.method, 'PUT')
                self.assertEqual(request.data, b'zip')

    def test_published_eighteen_packages_are_checked_before_network_or_upload(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp)
            (output / 'packages').mkdir()
            (output / 'packages/example-1.0.0.zip').write_bytes(b'zip')
            catalog = {'schemaVersion': 2, 'tools': [{'id': 'example', 'install': {
                'version': '1.0.0', 'url': 'https://raw.githubusercontent.com/startupsalad/TikBit/main/desktop/packages/example-1.0.0.zip',
                'bytes': 3, 'sha256': PUBLISH.sha(b'zip')}}]}
            (output / 'catalog.json').write_text(json.dumps(catalog), encoding='utf-8')
            with patch.object(PUBLISH, 'read_remote') as read, patch.object(PUBLISH, 'upload') as upload:
                PUBLISH.publish(output, apply=False)
                read.assert_not_called()
                upload.assert_not_called()
                (output / 'packages/example-1.0.0.zip').write_bytes(b'bad')
                with self.assertRaisesRegex(ValueError, 'integrity'):
                    PUBLISH.publish(output, apply=True)
                read.assert_not_called()
                upload.assert_not_called()

    def test_packages_are_verified_before_catalog_and_collision_never_overwrites(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp)
            (output / 'packages').mkdir()
            (output / 'packages/example-1.0.0.zip').write_bytes(b'zip')
            catalog = {'schemaVersion': 2, 'tools': [{'id': 'example', 'install': {
                'version': '1.0.0', 'url': 'https://github.com/startupsalad/TikBit/releases/download/test/example-1.0.0.zip',
                'bytes': 3, 'sha256': PUBLISH.sha(b'zip')}}]}
            raw = json.dumps(catalog).encode()
            (output / 'catalog.json').write_bytes(raw)
            remote = {}
            events = []

            def read(key, limit):
                events.append(('read', key))
                return remote.get(key)

            def upload(file, key, immutable, ossutil):
                events.append(('upload', key))
                if immutable and key in remote:
                    raise AssertionError('Unexpected overwrite')
                remote[key] = file.read_bytes()

            with patch.object(PUBLISH, 'read_remote', side_effect=read), patch.object(PUBLISH, 'upload', side_effect=upload):
                PUBLISH.publish(output, apply=True)
                self.assertLess(events.index(('read', 'packages/example-1.0.0.zip'), 1),
                                events.index(('upload', 'catalog.json')))
                self.assertEqual(remote['catalog.json'], raw)
                events.clear()
                PUBLISH.publish(output, apply=True)
                self.assertFalse(any(action == 'upload' for action, _ in events))
                remote['packages/example-1.0.0.zip'] = b'changed'
                events.clear()
                with self.assertRaisesRegex(ValueError, 'Immutable'):
                    PUBLISH.publish(output, apply=True)
                self.assertFalse(any(action == 'upload' for action, _ in events))

    def test_failed_package_readback_does_not_publish_catalog(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp)
            (output / 'packages').mkdir()
            (output / 'packages/example-1.0.0.zip').write_bytes(b'zip')
            (output / 'catalog.json').write_text(json.dumps({'schemaVersion': 2, 'tools': [{'id': 'example', 'install': {
                'version': '1.0.0', 'url': 'https://raw.githubusercontent.com/startupsalad/TikBit/main/desktop/packages/example-1.0.0.zip',
                'bytes': 3, 'sha256': PUBLISH.sha(b'zip')}}]}), encoding='utf-8')
            with patch.object(PUBLISH, 'read_remote', side_effect=[None, None, b'bad']), patch.object(PUBLISH, 'upload') as upload:
                with self.assertRaisesRegex(ValueError, 'readback'):
                    PUBLISH.publish(output, apply=True)
                self.assertEqual(upload.call_count, 1)
                self.assertEqual(upload.call_args.args[1], 'packages/example-1.0.0.zip')


if __name__ == '__main__':
    unittest.main()
