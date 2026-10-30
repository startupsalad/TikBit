"""Safety checks for script-only updates and unpublished local packages."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, ROOT / file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


updater = load("voice_updater", "update.py")
builder = load("voice_builder", "build_packages.py")
installer = load("voice_installer", "install.py")


class UpdateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="voice-update-test-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.target = self.root / "installed"
        self.target.mkdir()
        self.originals = {}
        for name in updater.BANNERS:
            content = (ROOT / "engine" / name).read_bytes() + b"\n# older public snapshot\n"
            (self.target / name).write_bytes(content)
            self.originals[name] = content
        (self.target / "choice.txt").write_text("yunxi")
        (self.target / ".flag").write_text("preserve")
        (self.target / "settings.json").write_text('{"hooks":{"custom":true}}')
        (self.target / "VERSION").write_text("0.3.0")
        self.originals["VERSION"] = b"0.3.0"
        public_fixture = {name: updater.normalized_sha(content) for name, content in self.originals.items() if name in updater.BANNERS}
        patcher = mock.patch.dict(updater.KNOWN_PUBLIC_HASHES, public_fixture)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_actual_official_oss_legacy_upgrade(self):
        for name in updater.BANNERS:
            raw = (ROOT / "tests/fixtures/oss-20260806" / name).read_bytes()
            self.assertEqual(updater.normalized_sha(raw), updater.KNOWN_OSS_20260806_HASHES[name])
            (self.target / name).write_bytes(raw)
        (self.target / "VERSION").unlink()
        result = updater.update(self.target, check=True)
        self.assertEqual(len(result["changed"]), 3)
        self.assertFalse((self.target / "backups").exists())
        updater.update(self.target)
        self.assertEqual((self.target / "choice.txt").read_text(), "yunxi")
        self.assertEqual(updater.update(self.target)["changed"], [])

    def test_official_oss_legacy_private_edit_refused(self):
        for name in updater.BANNERS:
            raw = (ROOT / "tests/fixtures/oss-20260806" / name).read_bytes()
            (self.target / name).write_bytes(raw + b"\n# private customization\n")
        with self.assertRaisesRegex(ValueError, "private"):
            updater.update(self.target)
        self.assertFalse((self.target / "backups").exists())

    def test_read_only_check(self):
        result = updater.update(self.target, check=True)
        self.assertEqual(result["version"], "0.3.1")
        self.assertEqual(len(result["changed"]), 3)
        self.assertFalse((self.target / "backups").exists())
        self.assertEqual((self.target / "VERSION").read_text(), "0.3.0")

    def test_update_preserves_user_config_and_backups_originals(self):
        result = updater.update(self.target)
        for name, content in self.originals.items():
            self.assertEqual((Path(result["backup"]) / name).read_bytes(), content)
        self.assertEqual((self.target / "choice.txt").read_text(), "yunxi")
        self.assertEqual((self.target / ".flag").read_text(), "preserve")
        self.assertEqual((self.target / "settings.json").read_text(), '{"hooks":{"custom":true}}')
        self.assertEqual((self.target / "VERSION").read_text().strip(), "0.3.1")

    def test_idempotent_no_extra_backup(self):
        updater.update(self.target)
        count = len(list((self.target / "backups/voice-notification").iterdir()))
        result = updater.update(self.target)
        self.assertEqual(result["changed"], [])
        self.assertEqual(len(list((self.target / "backups/voice-notification").iterdir())), count)

    def test_private_fork_refused_without_changes(self):
        (self.target / "notify-voice.ps1").write_text("# custom private engine")
        with self.assertRaisesRegex(ValueError, "private"):
            updater.update(self.target)
        self.assertFalse((self.target / "backups").exists())
        self.assertEqual((self.target / "notify-voice.ps1").read_text(), "# custom private engine")

    def test_private_edits_with_original_banner_are_refused(self):
        path = self.target / "notify-voice.ps1"
        path.write_bytes(path.read_bytes() + b"\n# personal custom change\n")
        with self.assertRaisesRegex(ValueError, "private"):
            updater.update(self.target)
        self.assertFalse((self.target / "backups").exists())

    def test_interrupted_update_rolls_back(self):
        original_replace = updater.os.replace
        calls = 0
        def fail_second(*args):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError("simulated failure")
            return original_replace(*args)
        with mock.patch.object(updater.os, "replace", side_effect=fail_second):
            with self.assertRaisesRegex(OSError, "simulated"):
                updater.update(self.target)
        for name, content in self.originals.items():
            self.assertEqual((self.target / name).read_bytes(), content)
        self.assertEqual(list(self.target.glob(".voice-update-*")), [])

    def test_mac_install_does_not_wire_missing_gate(self):
        config = self.target / "mac-settings.json"
        config.write_text('{"hooks":{"Custom":[{"hooks":[{"command":"keep-me"}]}]}}')
        with mock.patch.object(installer, "DEST", self.target), mock.patch.object(installer, "IS_WIN", False):
            self.assertTrue(installer.wire_settings_json(config, "test"))
        content = config.read_text(encoding="utf-8")
        self.assertNotIn("notify-gate", content)
        self.assertIn("keep-me", content)
        self.assertNotIn('"Stop"', content)
        self.assertIn("notify-voice.sh", content)

    def test_install_copies_version_without_user_choices(self):
        target = self.root / "new-install"
        with mock.patch.object(installer, "DEST", target):
            installer.copy_assets()
        self.assertEqual((target / "VERSION").read_text().strip(), "0.3.1")
        self.assertTrue((target / "notify-voice.ps1").is_file())
        self.assertTrue((target / "notify-voice.sh").is_file())
        self.assertFalse((target / "choice.txt").exists())
    def test_ambiguous_autodetection_refused(self):
        for name in (".claude", ".task-voice"):
            dest = self.root / name
            dest.mkdir()
            (dest / "notify-voice.ps1").write_text(updater.BANNERS["notify-voice.ps1"])
        with mock.patch.object(updater.Path, "home", return_value=self.root):
            with self.assertRaisesRegex(ValueError, "exactly one"):
                updater.installed_target()

    def test_new_install_not_silently_performed(self):
        with self.assertRaises(ValueError):
            updater.update(self.root / "absent")
        self.assertFalse((self.root / "absent").exists())


class PackageTests(unittest.TestCase):
    def test_both_platforms_are_self_contained(self):
        with tempfile.TemporaryDirectory(prefix="voice-package-test-") as directory:
            for platform, wanted, excluded in (("windows", ".ps1", ".sh"), ("macos", ".sh", ".ps1")):
                info = builder.package(platform, Path(directory))
                self.assertEqual(info["version"], "0.3.1")
                with zipfile.ZipFile(Path(directory) / info["file"]) as archive:
                    names = archive.namelist()
                    self.assertIn(builder.TOP + "/update.py", names)
                    self.assertIn(builder.TOP + "/engine/notify-voice" + wanted, names)
                    self.assertNotIn(builder.TOP + "/engine/notify-voice" + excluded, names)
                    self.assertIn(builder.TOP + "/voice_clips/claudian_multitab/dialog10_done.mp3", names)
                    self.assertIsNone(archive.testzip())
                    self.assertEqual(archive.read(builder.TOP + "/engine/notify-voice" + wanted), (ROOT / "engine" / ("notify-voice" + wanted)).read_bytes())
                    if platform == "macos":
                        for name in names:
                            if name.endswith((".sh", ".command")):
                                self.assertNotIn(b"\r\n", archive.read(name))
                        mode = archive.getinfo(builder.TOP + "/engine/notify-voice.sh").external_attr >> 16
                        self.assertTrue(mode & 0o111)

    def test_package_overwrite_is_refused(self):
        with tempfile.TemporaryDirectory(prefix="voice-package-existing-") as directory:
            first = builder.package("windows", Path(directory))
            raw = (Path(directory) / first["file"]).read_bytes()
            with self.assertRaises(ValueError):
                builder.package("windows", Path(directory))
            self.assertEqual((Path(directory) / first["file"]).read_bytes(), raw)

    def test_catalog_version_matches_source(self):
        catalog = json.loads((ROOT.parents[1] / "catalog.json").read_text(encoding="utf-8-sig"))
        voice = next(tool for tool in catalog["tools"] if tool["id"] == "voice-notification")
        self.assertEqual(voice["version"], (ROOT / "VERSION").read_text().strip())


if __name__ == "__main__":
    unittest.main(verbosity=2)
