"""Capture safety tests: mixed downloads, wrong links, unstable files and retries."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import channels_proxy
import read_channels as channels
from read_video import find_binary

URL = 'https://weixin.qq.com/sph/test'
PROXY = {'status': 'captured', 'platform': 'Windows',
         'settings': {'auto_detect': True, 'pac': '', 'proxy': '', 'bypass': ''}}


class CaptureTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.directory = Path(self.tmp.name)
        self.downloads = self.directory/'downloads'
        self.downloads.mkdir()
        (self.downloads/'old.mp4').write_bytes(b'old')
        with patch.object(channels_proxy, 'snapshot', return_value=PROXY):
            started = channels.begin(URL, self.downloads)
        self.path = Path(started['session'])
        self.addCleanup(shutil.rmtree, self.path.parent)
        self.session = channels.load(self.path, URL)

    def media(self, name, data=b'new'):
        path = self.downloads/name
        path.write_bytes(data)
        os.utime(path, (time.time()-3, time.time()-3))
        return path

    def test_wrong_link_refused(self):
        with self.assertRaisesRegex(ValueError, '不一致'):
            channels.load(self.path, 'https://weixin.qq.com/sph/another')

    def test_mixed_downloads_and_cache_never_auto_selected_or_deleted(self):
        self.media('one.mp4'); self.media('two.mp4'); self.media('cache.wspkg')
        (self.downloads/'incomplete.mp4.part').write_bytes(b'partial')
        with patch.object(channels, 'probe', return_value={'duration': 3, 'video': {'width': 10, 'height': 10}}):
            result = channels.candidates(self.session, settle_seconds=0)
        self.assertEqual(len(result['videos']), 2)
        self.assertEqual(len(result['cache_candidates']), 1)
        self.assertTrue((self.downloads/'cache.wspkg').exists())
        self.assertNotIn('old.mp4', [Path(v['file']).name for v in result['videos']])

    def test_new_file_with_old_timestamp_is_still_detected(self):
        path = self.media('preserved-time.mp4')
        os.utime(path, (1, 1))
        with patch.object(channels, 'probe', side_effect=RuntimeError('not decrypted')):
            result = channels.candidates(self.session, settle_seconds=0)
        self.assertEqual(len(result['videos']), 1)
        self.assertIn('inspection_error', result['videos'][0])

    def test_growing_file_and_empty_file_are_unstable(self):
        self.media('new.mp4'); self.media('empty.mp4', b'')
        actual = channels.scan(self.downloads)
        before = {k: dict(v) for k, v in actual.items()}
        before['new.mp4']['size'] -= 1
        with patch.object(channels, 'scan', side_effect=[before, actual]):
            result = channels.candidates(self.session, settle_seconds=0)
        self.assertTrue(all(not item['stable'] for item in result['videos']))

    def test_old_and_outside_files_rejected_before_archive(self):
        outside = self.directory/'outside.mp4'; outside.write_bytes(b'x')
        with patch.object(channels, 'proxy_check', return_value={'status': 'unknown'}):
            for selected in (outside, self.downloads/'old.mp4'):
                with self.assertRaises(ValueError):
                    channels.finish(self.path, self.session, selected, 'x', self.directory/'vault')
        self.assertFalse((self.directory/'vault').exists())

    def test_lock_blocks_duplicate_finish(self):
        with channels.locked(self.path):
            with self.assertRaisesRegex(ValueError, '正在收尾'):
                with channels.locked(self.path):
                    self.fail('acquired twice')
        self.assertFalse(self.path.with_suffix('.lock').exists())

    def test_session_outside_tool_temp_cannot_create_or_remove_lock(self):
        user_file = self.directory/'session.json'
        user_file.write_text('{}', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, '系统临时目录'):
            with channels.locked(user_file):
                self.fail('should reject arbitrary session path')
        self.assertTrue(user_file.exists())
        self.assertFalse(user_file.with_suffix('.lock').exists())

    def test_proxy_pac_or_auto_detect_difference_is_not_restored(self):
        changed = json.loads(json.dumps(PROXY))
        changed['settings']['auto_detect'] = False
        self.assertEqual(channels_proxy.compare(PROXY, changed)['status'], 'changed')
        changed['settings']['pac'] = 'http://internal/pac?token=SECRET'
        result = channels_proxy.compare(PROXY, changed)
        self.assertNotIn('SECRET', json.dumps(result))
        self.assertEqual(channels_proxy.compare({'status': 'unknown'}, PROXY)['status'], 'unknown')
        self.assertEqual(channels_proxy.compare(PROXY, PROXY)['status'], 'restored')

    def test_cli_requires_explicit_file_and_no_fake_download(self):
        for args in (['--finish', '--session', str(self.path)], ['--file', 'not-selected.mp4']):
            result = subprocess.run([sys.executable, '-B', str(HERE/'read.py'), URL, *args], capture_output=True)
            self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.directory/'vault').exists())


class RealCaptureTests(unittest.TestCase):
    setUp = CaptureTests.setUp
    media = CaptureTests.media

    def test_real_finish_retains_original_and_retry_does_not_duplicate(self):
        ffmpeg = find_binary('ffmpeg')
        if not ffmpeg or not find_binary('ffprobe'):
            self.skipTest('ffmpeg/ffprobe missing')
        video = self.downloads/'真实 [视频].mp4'
        subprocess.run([ffmpeg, '-nostdin', '-v', 'error', '-f', 'lavfi', '-i',
                        'testsrc2=size=160x90:rate=10', '-t', '1', '-c:v', 'mpeg4', str(video)], check=True)
        os.utime(video, (time.time()-3, time.time()-3))
        dest = self.directory/'vault'
        with patch.object(channels_proxy, 'snapshot', return_value=PROXY):
            result = channels.finish(self.path, self.session, video, '测试视频', dest, frames=2, full=True)
            self.addCleanup(shutil.rmtree, result['output_dir'])
            replay = channels.finish(self.path, channels.load(self.path, URL), video, 'x', dest)
        self.assertEqual(result['status'], 'archived')
        self.assertEqual(result['check_level'], 'full')
        self.assertTrue(replay['repeated'])
        self.assertEqual(len(list(dest.glob('*.mp4'))), 1)
        self.assertEqual(video.read_bytes(), Path(result['archive']['media']).read_bytes())
        self.assertIn('抓取前配置一致', Path(result['archive']['note']).read_text(encoding='utf-8'))

    def test_proxy_not_restored_is_reported_even_after_successful_archive(self):
        ffmpeg = find_binary('ffmpeg')
        if not ffmpeg or not find_binary('ffprobe'):
            self.skipTest('ffmpeg/ffprobe missing')
        video = self.downloads/'captured.mp4'
        subprocess.run([ffmpeg, '-nostdin', '-v', 'error', '-f', 'lavfi', '-i',
                        'testsrc2=size=160x90:rate=10', '-t', '1', '-c:v', 'mpeg4', str(video)], check=True)
        os.utime(video, (time.time()-3, time.time()-3))
        changed = json.loads(json.dumps(PROXY))
        changed['settings']['proxy'] = '127.0.0.1:8899'
        with patch.object(channels_proxy, 'snapshot', return_value=changed):
            result = channels.finish(self.path, self.session, video, 'x', self.directory/'vault', frames=0)
        self.addCleanup(shutil.rmtree, result['output_dir'])
        self.assertEqual(result['status'], 'archived_proxy_review_required')
        self.assertEqual(result['proxy_check']['status'], 'changed')
        self.assertTrue(Path(result['archive']['media']).exists())
        self.assertIn('待恢复并复查', Path(result['archive']['note']).read_text(encoding='utf-8'))

    def test_broken_capture_never_creates_archive(self):
        if not find_binary('ffprobe'):
            self.skipTest('ffprobe missing')
        broken = self.media('encrypted.mp4', b'encrypted')
        with patch.object(channels_proxy, 'snapshot', return_value=PROXY):
            with self.assertRaises(RuntimeError):
                channels.finish(self.path, self.session, broken, 'x', self.directory/'vault', frames=0)
        self.assertFalse((self.directory/'vault').exists())
        self.assertTrue(broken.exists())


if __name__ == '__main__':
    unittest.main()
