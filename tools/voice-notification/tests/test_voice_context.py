"""Offline, silent cross-platform regression. No personal paths or real audio."""
import datetime as dt
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASH = shutil.which("bash")
if os.name == "nt":
    candidate = Path(os.environ.get("ProgramFiles", "")) / "Git/bin/bash.exe"
    BASH = str(candidate) if candidate.is_file() else None
PS = shutil.which("powershell.exe") or shutil.which("pwsh")
MAIN = "01900000-0000-7000-8000-000000000001"
CHILD = "01900000-0000-7000-8000-000000000002"


class VoiceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="voice-public-test-")
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.vault = self.base / "vault [test]"
        self.sessions = self.vault / ".claudian/sessions"
        self.sessions.mkdir(parents=True)
        self.data = self.vault / ".obsidian/plugins/tikbit-claudian/data.json"
        self.data.parent.mkdir(parents=True)
        self.home = self.base / "home"
        self.home.mkdir()
        self.engine = self.base / "engine"
        shutil.copytree(ROOT / "engine", self.engine)
        # Intercept Windows audio in the isolated copy only, before any dispatch.
        win = self.engine / "notify-voice.ps1"
        source = win.read_text(encoding="utf-8-sig")
        marker = "# --- context gate ---" if "# --- context gate ---" in source else "# --- flag-only operation"
        mocks = r'''
function Play-File([string]$mp3) {
  if (-not (Test-Path -LiteralPath $mp3)) { return $false }
  [IO.File]::AppendAllText($env:VOICE_TEST_AUDIO_LOG, ([IO.Path]::GetFileName($mp3) + "`n"))
  return $true
}
function Speak-Sapi([string]$b64) {
  if ($b64) { [IO.File]::AppendAllText($env:VOICE_TEST_AUDIO_LOG, ("say:" + (Dec $b64) + "`n")) }
}
'''
        self.assertIn(marker, source)
        source = source.replace(marker, mocks + "\n" + marker, 1)
        win.write_text(source, encoding="utf-8-sig")
        self.bin = self.base / "bin"
        self.bin.mkdir()
        stubs = {
            "afplay": '#!/bin/bash\nprintf "%s\\n" "$(basename "$1")" >> "$VOICE_TEST_AUDIO_LOG"\n',
            "say": '#!/bin/bash\nif [ "$2" = "?" ]; then echo "Tingting zh_CN"; exit 0; fi\nprintf "say:%s\\n" "$*" >> "$VOICE_TEST_AUDIO_LOG"\n',
            "python3": '#!/bin/bash\nexec "' + shutil.which("python").replace("\\", "/") + '" "$@"\n',
        }
        for name, body in stubs.items():
            path = self.bin / name
            path.write_text(body, encoding="utf-8", newline="\n")
            path.chmod(0o755)
        self.audio = self.base / "audio.log"
        self.env = os.environ.copy()
        for name in ("CODEX_THREAD_ID", "CODEX_SESSION_ID", "CLAUDE_CODE_SESSION_ID", "TIKBIT_VAULT_ROOT", "TIKBIT_VOICE_SUPPRESS", "CODEX_HOME"):
            self.env.pop(name, None)
        self.env.update({"HOME": str(self.home), "USERPROFILE": str(self.home), "CODEX_HOME": str(self.home / ".codex"), "VOICE_TEST_AUDIO_LOG": str(self.audio), "PYTHONUTF8": "1"})
        self.env["PATH"] = str(self.bin) + os.pathsep + self.env["PATH"]
        self.tabs = [{"tabId": f"tab-{i}", "conversationId": f"conv-{i}"} for i in range(1, 12)]
        for i in range(1, 12):
            self.meta(i, {"sessionId": MAIN if i == 9 else f"main-{i}", "providerState": {}})
        self.write_data()
        for key in ("done", "perm", "wait", "ask", "stuck", "error"):
            generic = self.engine / "voice_clips/xiaoxiao" / (key + ".mp3")
            generic.parent.mkdir(parents=True, exist_ok=True)
            generic.write_bytes(b"mock")
            for i in range(1, 11):
                numbered = self.engine / "voice_clips/claudian_multitab" / f"dialog{i}_{key}.mp3"
                numbered.parent.mkdir(parents=True, exist_ok=True)
                numbered.write_bytes(b"mock")

    def meta(self, i, value):
        (self.sessions / f"conv-{i}.meta.json").write_text(json.dumps(value), encoding="utf-8-sig")

    def write_data(self):
        self.data.write_text(json.dumps({"tabManagerState": {"openTabs": self.tabs, "activeTabId": "tab-1"}}), encoding="utf-8-sig")

    def native(self, child=False, corrupt=False, isolated=False):
        tid = CHILD if child else MAIN
        stamp = dt.datetime.fromtimestamp(int(tid.replace("-", "")[:12], 16) / 1000, dt.timezone.utc)
        root = self.home / (".tikbit/codex" if isolated else ".codex")
        folder = root / "sessions" / stamp.strftime("%Y/%m/%d")
        folder.mkdir(parents=True, exist_ok=True)
        payload = {"id": tid, "source": {"subagent": {"thread_spawn": {"parent_thread_id": MAIN}}} if child else "cli"}
        if child:
            payload["parent_thread_id"] = MAIN
        content = "broken" if corrupt else json.dumps({"type": "session_meta", "payload": payload})
        (folder / f"rollout-2000-01-01T00-00-00-{tid}.jsonl").write_text(content + "\n", encoding="utf-8")
        self.env["CODEX_THREAD_ID"] = tid

    def engines(self):
        found = []
        if PS:
            found.append("windows")
        if BASH:
            found.append("mac-script")
        self.assertTrue(found, "Need PowerShell or Bash to run engine tests")
        return found

    def run_engine(self, engine, mode="done", dry=True, extra=None):
        if self.audio.exists():
            self.audio.unlink()
        if engine == "windows":
            args = [PS, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(self.engine / "notify-voice.ps1"), "-Mode", mode]
            if dry:
                args += ["-DryRun"]
            elif extra:
                args += ["-B64", extra]
        else:
            args = [BASH, str(self.engine / "notify-voice.sh"), mode]
            if dry:
                args += ["--dry-run"]
            elif extra:
                args += [extra]
        run = subprocess.run(args, env=self.env, input='{"message":"waiting"}', capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=25)
        self.assertEqual(run.returncode, 0, engine + ": " + run.stderr)
        if dry:
            self.assertFalse(self.audio.exists(), "DryRun played audio")
            return json.loads(run.stdout.strip().lstrip("\ufeff"))
        return self.audio.read_text(encoding="utf-8") if self.audio.exists() else ""

    def assert_context(self, allowed, tab, reason=None):
        for engine in self.engines():
            with self.subTest(engine=engine):
                got = self.run_engine(engine)
                self.assertEqual(got["allowed"], allowed)
                self.assertEqual(got["tab"], tab)
                if reason:
                    self.assertEqual(got["reason"], reason)

    def multitab(self, tid=MAIN):
        self.env["TIKBIT_VAULT_ROOT"] = str(self.vault)
        self.env["CODEX_THREAD_ID"] = tid

    def test_legacy_child_completion_does_not_play(self):
        self.multitab(CHILD)
        for engine in self.engines():
            self.assertEqual(self.run_engine(engine, dry=False), "")

    def test_legacy_fresh_tab_is_not_guessed(self):
        self.multitab(CHILD)
        self.meta(11, {"updatedAt": 9999999})
        for engine in self.engines():
            self.assertEqual(self.run_engine(engine, dry=False), "")

    def test_visible_main9(self):
        self.multitab()
        self.assert_context(True, 9, "exact-visible-tab")

    def test_stale_claude_id_does_not_override_codex(self):
        self.multitab()
        self.env["CLAUDE_CODE_SESSION_ID"] = "main-1"
        self.assert_context(True, 9)

    def test_claude_exact(self):
        self.env.update({"TIKBIT_VAULT_ROOT": str(self.vault), "CLAUDE_CODE_SESSION_ID": "main-2"})
        self.assert_context(True, 2)

    def test_child_all_modes_cannot_bypass(self):
        self.multitab(CHILD)
        flag = self.engine / ".flag"
        flag.write_text("unchanged")
        for engine in self.engines():
            for mode in ("done", "stuck", "wait", "error", "ask", "perm", "say", "notify", "flag", "done-if-flagged", "unknown"):
                with self.subTest(engine=engine, mode=mode):
                    self.assertEqual(self.run_engine(engine, mode, dry=False, extra="10"), "")
                    self.assertEqual(flag.read_text(), "unchanged")

    def test_unknown_id_and_fresh_tab_denied(self):
        self.multitab(CHILD)
        self.meta(11, {"updatedAt": 9999999})
        self.assert_context(False, 0)

    def test_duplicate_claim_denied(self):
        self.multitab()
        self.meta(2, {"sessionId": MAIN})
        self.assert_context(False, 0)

    def test_reorder_uses_real_slot(self):
        self.multitab()
        self.tabs[6], self.tabs[8] = self.tabs[8], self.tabs[6]
        self.write_data()
        self.assert_context(True, 7)

    def test_bad_json_denied(self):
        self.multitab()
        self.data.write_text("broken")
        self.assert_context(False, 0)

    def test_missing_metadata_denied(self):
        self.multitab()
        (self.sessions / "conv-9.meta.json").unlink()
        self.assert_context(False, 0)

    def test_no_identity_opt_in_is_not_generic(self):
        self.env["TIKBIT_VAULT_ROOT"] = str(self.vault)
        self.assert_context(False, 0)

    def test_standalone_no_identity_still_works(self):
        self.assert_context(True, 0, "standalone")
        for engine in self.engines():
            self.assertIn("done.mp3", self.run_engine(engine, dry=False))

    def test_standalone_other_client_claude_still_works(self):
        self.env["CLAUDE_CODE_SESSION_ID"] = "other-client-main"
        self.assert_context(True, 0)

    def test_standalone_codex_main_verified(self):
        self.native()
        self.assert_context(True, 0, "codex-main")

    def test_standalone_codex_child_denied(self):
        self.native(child=True)
        self.assert_context(False, 0, "codex-subagent")
        for engine in self.engines():
            self.assertEqual(self.run_engine(engine, dry=False), "")

    def test_standalone_codex_unknown_denied(self):
        self.env["CODEX_THREAD_ID"] = CHILD
        self.assert_context(False, 0, "codex-context-unverified")

    def test_standalone_codex_corrupt_metadata_denied(self):
        self.native(corrupt=True)
        self.assert_context(False, 0)

    def test_standalone_isolated_codex_home(self):
        self.native(isolated=True)
        self.env.pop("CODEX_HOME")
        self.assert_context(True, 0, "codex-main")

    def test_explicit_branch_suppression(self):
        self.env["TIKBIT_VOICE_SUPPRESS"] = "1"
        self.assert_context(False, 0, "explicit-suppression")

    def test_valid_master_uses_numbered_clip_not_explicit_number(self):
        self.multitab()
        for engine in self.engines():
            audio = self.run_engine(engine, "perm", dry=False, extra="10")
            self.assertIn("dialog9_perm.mp3", audio)
            self.assertNotIn("dialog10", audio)

    def test_real11_falls_back_once(self):
        self.multitab("main-11")
        for engine in self.engines():
            audio = self.run_engine(engine, dry=False)
            self.assertEqual(len(audio.splitlines()), 1)
            self.assertIn("11", audio)

    def test_gate_has_no_history_table_writes(self):
        for name in ("notify-voice.ps1", "notify-voice.sh"):
            text = (ROOT / "engine" / name).read_text(encoding="utf-8-sig")
            self.assertNotIn("session_labels.json", text)
            self.assertNotIn("freshSlot", text)
            self.assertNotIn("fresh_slot", text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
