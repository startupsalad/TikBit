import base64
import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "embed_images.py"
SPEC = importlib.util.spec_from_file_location("embed_images", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class EmbedImagesTest(unittest.TestCase):
    def test_embeds_local_and_preserves_remote_and_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            image = root / "配图.png"
            payload = b"\x89PNG\r\n\x1a\nfixture"
            image.write_bytes(payload)
            html = (
                '<img src="配图.png">'
                '<img src="https://example.com/remote.png">'
                '<img src="data:image/png;base64,already">'
            )
            result, count, warnings = MODULE.embed_html(html, root)

            expected = base64.b64encode(payload).decode("ascii")
            self.assertEqual(count, 1)
            self.assertEqual(warnings, [])
            self.assertIn(f'data:image/png;base64,{expected}', result)
            self.assertIn('src="https://example.com/remote.png"', result)
            self.assertIn('src="data:image/png;base64,already"', result)

    def test_missing_local_image_is_reported_and_unchanged(self):
        result, count, warnings = MODULE.embed_html('<img src="missing.jpg">', Path(tempfile.gettempdir()))
        self.assertEqual(count, 0)
        self.assertEqual(result, '<img src="missing.jpg">')
        self.assertEqual(len(warnings), 1)


if __name__ == "__main__":
    unittest.main()
