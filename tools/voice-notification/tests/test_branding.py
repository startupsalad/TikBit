"""Public installation copy uses TikBit; on-disk compatibility names stay stable."""
import contextlib
import importlib.util
import io
from pathlib import Path
import re
import tempfile
import unittest
from unittest import mock
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DOCS = ("INSTALL.md", "给AI的安装指令.md", "📖 使用说明.md")
LEGACY_IDS = (".claudian", "tikbit-claudian", "claudian_multitab")


class BrandingTests(unittest.TestCase):
    def test_only_compatibility_identifiers_keep_legacy_name(self):
        for name in DOCS:
            with self.subTest(document=name):
                text = (ROOT / name).read_text(encoding="utf-8-sig")
                for identifier in LEGACY_IDS:
                    text = text.replace(identifier, "COMPATIBILITY_ID")
                self.assertNotRegex(text, r"(?i)claudian")
                self.assertIn("TikBit", text)

    def test_ai_naming_rule_and_yolo_prompt_are_explicit(self):
        text = (ROOT / "给AI的安装指令.md").read_text(encoding="utf-8-sig")
        self.assertIn("对外名称（必须遵守）", text)
        self.assertIn("TikBit 顶部的 YOLO 开关现在是开着还是关着？", text)
        self.assertIn("不得为了改名重命名目录", text)

    def test_detection_example_uses_tikbit_and_original_paths(self):
        text = (ROOT / "给AI的安装指令.md").read_text(encoding="utf-8-sig")
        snippet = re.search(r"```python\n(.*?)\n```", text, re.S).group(1)
        with tempfile.TemporaryDirectory(prefix="voice-brand-detection-") as folder:
            vault = Path(folder)
            for installed in (False, True):
                with self.subTest(installed=installed):
                    if installed:
                        (vault / ".claudian/sessions").mkdir(parents=True)
                        data = vault / ".obsidian/plugins/tikbit-claudian/data.json"
                        data.parent.mkdir(parents=True)
                        data.write_text("{}", encoding="utf-8")
                    output = io.StringIO()
                    namespace = {}
                    with mock.patch.object(Path, "cwd", return_value=vault), contextlib.redirect_stdout(output):
                        exec(compile(snippet, "installation-example", "exec"), namespace)
                    self.assertEqual(namespace["version"], "tikbit" if installed else "generic")
                    self.assertNotRegex(output.getvalue(), r"(?i)claudian")
                    if installed:
                        self.assertIn("TikBit", output.getvalue())

    def test_related_voice_pack_uses_tikbit(self):
        text = (ROOT.parent / "ai-voice-pack/INSTALL.md").read_text(encoding="utf-8-sig")
        self.assertNotRegex(text, r"(?i)claudian")
        self.assertIn("TikBit", text)

    def test_both_packages_include_current_installation_copy(self):
        spec = importlib.util.spec_from_file_location("voice_brand_builder", ROOT / "build_packages.py")
        builder = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(builder)
        with tempfile.TemporaryDirectory(prefix="voice-brand-packages-") as folder:
            for platform in ("windows", "macos"):
                with self.subTest(platform=platform):
                    info = builder.package(platform, Path(folder))
                    with zipfile.ZipFile(Path(folder) / info["file"]) as archive:
                        for name in DOCS:
                            self.assertEqual(archive.read(builder.TOP + "/" + name), (ROOT / name).read_bytes())


if __name__ == "__main__":
    unittest.main()
