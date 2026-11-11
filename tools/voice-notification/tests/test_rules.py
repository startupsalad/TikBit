import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import rules


class RulesTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.voice = self.home / 'voice'

    def writes(self, env=None):
        return rules.rule_writes(self.voice, self.home, env or {})

    def test_targets_real_isolated_homes_and_preserves_personal_text(self):
        claude = self.home / 'isolated-claude'
        codex = self.home / 'isolated-codex'
        claude.mkdir(); codex.mkdir()
        (claude / 'CLAUDE.md').write_bytes(b'Personal identity\n')
        env = {'CLAUDE_CONFIG_DIR': str(claude), 'CODEX_HOME': str(codex)}
        writes = self.writes(env)
        self.assertEqual(set(writes), {claude / 'CLAUDE.md', codex / 'AGENTS.md'})
        text = writes[claude / 'CLAUDE.md'].decode('utf-8')
        self.assertTrue(text.startswith('Personal identity\n'))
        for word in ['done', 'ask', 'perm', 'stuck', 'request_user_input_async']:
            self.assertIn(word, text)

    def test_applies_once_and_check_does_not_modify_anything(self):
        pending = self.writes()
        result = rules.apply_rule_writes(pending, self.voice, check=True)
        self.assertTrue(result['changed'])
        self.assertFalse(self.voice.exists())
        rules.apply_rule_writes(pending, self.voice)
        self.assertEqual(rules.apply_rule_writes(self.writes(), self.voice)['changed'], [])

    def test_rejects_malformed_owned_block_and_relative_explicit_home(self):
        root = self.home / '.claude'; root.mkdir()
        (root / 'CLAUDE.md').write_text('<!-- TIKBIT-VOICE:BEGIN -->\nprivate', encoding='utf-8')
        with self.assertRaises(ValueError):
            self.writes()
        with self.assertRaises(ValueError):
            self.writes({'CLAUDE_CONFIG_DIR': 'relative'})

    def test_rolls_back_first_rule_when_second_write_fails(self):
        writes = self.writes(); targets = list(writes)
        for file in targets:
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_bytes(b'original\r\n')
        real = os.replace
        def replace(source, target):
            if Path(target) == targets[1]:
                raise OSError('simulated write failure')
            return real(source, target)
        with mock.patch.object(rules.os, 'replace', side_effect=replace):
            with self.assertRaises(OSError):
                rules.apply_rule_writes(writes, self.voice)
        for file in targets:
            self.assertEqual(file.read_bytes(), b'original\r\n')

    def test_keeps_bom_and_user_content_outside_owned_rule_exactly(self):
        root = self.home / '.claude'; root.mkdir()
        original = b'\xef\xbb\xbfIdentity\r\n<!-- TIKBIT-VOICE:BEGIN -->\nold\n<!-- TIKBIT-VOICE:END -->\r\nUnique private rule\r\n'
        (root / 'CLAUDE.md').write_bytes(original)
        raw = self.writes()[root / 'CLAUDE.md']
        self.assertTrue(raw.startswith(b'\xef\xbb\xbfIdentity\r\n'))
        self.assertTrue(raw.endswith(b'\r\nUnique private rule\r\n'))
