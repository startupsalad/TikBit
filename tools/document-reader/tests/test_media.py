"""Offline contract tests; real ffmpeg tests run when binaries are available."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import read as router

class RoutingTests(unittest.TestCase):
    def test_local_extensions(self):
        for ext in ('.mp4', '.mov', '.mkv', '.webm', '.mp3', '.wav', '.m4a'):
            self.assertEqual(router.ROUTE.get(ext), 'read_video.py')

    def test_channels_host_path_and_uppercase(self):
        for url in ('https://weixin.qq.com/sph/abc', 'https://WEIXIN.QQ.COM/sph/abc?x=1'):
            self.assertEqual(router.pick_for_url(url), 'read_video.py')

    def test_article_and_web_regression(self):
        self.assertEqual(router.pick_for_url('https://mp.weixin.qq.com/s/a'), 'fetch_mp_article.py')
        for url in ('https://example.com/?x=mp.weixin.qq.com', 'https://mp.weixin.qq.com.evil.test/s/a',
                    'https://weixin.qq.com.evil.test/sph/a', 'https://weixin.qq.com/other',
                    'https://example.com/a.mp4.txt', 'https://example.com/page'):
            self.assertEqual(router.pick_for_url(url), 'read_web.py')

    def test_known_video_urls(self):
        for url in ('https://youtu.be/a', 'https://www.youtube.com/watch?v=a',
                    'https://www.bilibili.com/video/BV1', 'https://example.com/a.MP4?q=1'):
            self.assertEqual(router.pick_for_url(url), 'read_video.py')
        self.assertEqual(router.pick_for_url('https://www.youtube.com/about'), 'read_web.py')

    def test_channels_cli_never_networks(self):
        result = subprocess.run([sys.executable, '-B', str(HERE/'read.py'),
                                 'https://weixin.qq.com/sph/example'], capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('res-downloader', result.stdout)
        self.assertIn('video-channels.md', result.stdout)

class ArchiveTests(unittest.TestCase):
    def setUp(self):
        import media_archive
        self.archive = media_archive
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root/'original.mp4'
        self.source.write_bytes(b'test-media')
        self.meta = {'duration': 2.0, 'video': {'width': 320, 'height': 180}, 'audio': None}

    def test_safe_names(self):
        self.assertEqual(self.archive.safe_title('hello:/world?'), 'hello_world')
        for title in ('CON', 'nul', 'LPT1', 'COM2'):
            self.assertTrue(self.archive.safe_title(title).startswith('_'))
        self.assertNotIn('..', self.archive.safe_title('../test'))

    def test_copy_collision_source_retained_and_note(self):
        destination = self.root/'知识库'/'视频号下载'
        first = self.archive.archive_media(self.source, destination, '测试标题', 'https://weixin.qq.com/sph/a', self.meta, 'quick')
        second = self.archive.archive_media(self.source, destination, '测试标题', '', self.meta, 'full')
        self.assertNotEqual(first['media'], second['media'])
        self.assertTrue(self.source.exists())
        self.assertEqual(Path(first['media']).read_bytes(), self.source.read_bytes())
        note = Path(first['note']).read_text(encoding='utf-8')
        self.assertIn('![[测试标题.mp4]]', note)
        self.assertIn('https://weixin.qq.com/sph/a', note)
        self.assertIn('5秒', note)
        self.assertIn(hashlib.sha256(self.source.read_bytes()).hexdigest(), note)

    def test_existing_note_is_not_overwritten(self):
        dest = self.root/'out'; dest.mkdir()
        (dest/'title.md').write_text('KEEP', encoding='utf-8')
        result = self.archive.archive_media(self.source, dest, 'title', '', self.meta, 'quick')
        self.assertEqual((dest/'title.md').read_text(), 'KEEP')
        self.assertEqual(Path(result['media']).stem, 'title (2)')

    def test_note_escapes_markup(self):
        dest=self.root/'out'
        result=self.archive.archive_media(self.source,dest,'a]]\n# fake','https://example.com/x\n# fake',self.meta,'quick')
        note=Path(result['note']).read_text(encoding='utf-8')
        self.assertNotIn('\n# fake',note)
        self.assertNotIn('![[a]]',note)

    def test_checksum_failure_keeps_source(self):
        with patch.object(self.archive, 'digest', side_effect=['a','b']):
            with self.assertRaises(ValueError):
                self.archive.archive_media(self.source,self.root/'out','title','',self.meta,'quick')
        self.assertTrue(self.source.exists())
        self.assertFalse(list((self.root/'out').glob('*.md')))

class LocalMediaTests(unittest.TestCase):
    def test_missing_binary_and_invalid_count(self):
        import read_video
        with patch.object(read_video, 'find_binary', return_value=None):
            with self.assertRaisesRegex(RuntimeError, 'ffprobe'):
                read_video.probe(Path('file.mp4'))
        result=subprocess.run([sys.executable,'-B',str(HERE/'read_video.py'),'missing.mp4','--frames','201'],capture_output=True,text=True,encoding='utf-8')
        self.assertNotEqual(result.returncode,0)

    def test_channels_rejects_archive_options(self):
        result=subprocess.run([sys.executable,'-B',str(HERE/'read_video.py'),'https://weixin.qq.com/sph/a','--archive-dir','should-not-exist'],capture_output=True,text=True,encoding='utf-8')
        self.assertNotEqual(result.returncode,0)



class InstallerTests(unittest.TestCase):
    def load(self,path,name):
        spec=importlib.util.spec_from_file_location(name,path)
        module=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_document_both_engines_idempotent_and_preserves_other_files(self):
        module=self.load(HERE/'install.py','doc_installer')
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            first=module.install(root)
            user=root/'.agents/skills/文档读取编辑/user.txt'; user.write_text('KEEP')
            second=module.install(root)
            self.assertEqual(len(first),4)
            self.assertEqual(second,[])
            self.assertEqual(user.read_text(),'KEEP')
            self.assertNotIn('{{工具包路径}}',(user.parent/'SKILL.md').read_text(encoding='utf-8'))

    def test_isolated_user_roots_and_dry_run(self):
        module=self.load(HERE/'install.py','doc_installer_env')
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            with patch.dict(os.environ,{'CODEX_HOME':str(root/'codex'),'CLAUDE_CONFIG_DIR':str(root/'claude')}):
                self.assertEqual(module.targets(engine='codex'),[root/'codex/skills/文档读取编辑'])
                self.assertEqual(module.install(dry_run=True),[])
            self.assertFalse(list(root.iterdir()))

    def test_media_backend_both_engines(self):
        module=self.load(HERE.parent/'video-audio/install.py','media_installer')
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            first=module.install(root,skills=('local-transcribe',))
            self.assertTrue(first)
            self.assertEqual(module.install(root,skills=('local-transcribe',)),[])
            self.assertTrue((root/'.agents/skills/local-transcribe/scripts/transcribe.py').is_file())
            self.assertTrue((root/'.claude/skills/local-transcribe/references/video-channels.md').is_file())

class RealMediaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import read_video
        cls.media=read_video
        if not read_video.find_binary('ffmpeg') or not read_video.find_binary('ffprobe'):
            raise unittest.SkipTest('Set FFMPEG_PATH/FFPROBE_PATH for real binary tests')
        cls.tmp=tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.tmp.cleanup)
        cls.root=Path(cls.tmp.name)
        cls.video=cls.root/'测试 [video].mp4'
        cls.silent=cls.root/'silent.mp4'
        cls.audio=cls.root/'audio.wav'
        ffmpeg=read_video.find_binary('ffmpeg')
        def make(arguments):
            result=subprocess.run([ffmpeg,'-nostdin','-v','error']+arguments,capture_output=True)
            if result.returncode:
                raise RuntimeError(result.stderr.decode(errors='replace'))
        make(['-f','lavfi','-i','testsrc2=size=320x180:rate=25','-f','lavfi','-i','sine=frequency=440:sample_rate=16000','-t','2','-c:v','mpeg4','-c:a','aac',str(cls.video)])
        make(['-f','lavfi','-i','testsrc2=size=320x180:rate=25','-t','1','-c:v','mpeg4',str(cls.silent)])
        make(['-f','lavfi','-i','sine=frequency=440:sample_rate=16000','-t','1',str(cls.audio)])

    def test_video_full_decode_frames_audio_and_archive(self):
        result,metadata=self.media.inspect_local(self.video,frames=3,full=True,extract_audio=True)
        self.addCleanup(__import__('shutil').rmtree,result['output_dir'])
        self.assertEqual(result['check_level'],'full')
        self.assertEqual(len(result['frames']),3)
        self.assertTrue(Path(result['audio']).is_file())
        from PIL import Image
        for frame in result['frames']:
            with Image.open(frame['path']) as image:
                self.assertEqual(image.size,(320,180))
        from media_archive import archive_media
        saved=archive_media(self.video,self.root/'vault','测试视频','https://weixin.qq.com/sph/example',metadata,'full')
        self.assertEqual(Path(saved['media']).read_bytes(),self.video.read_bytes())

    def test_audio_only(self):
        result,_=self.media.inspect_local(self.audio,frames=8)
        self.addCleanup(__import__('shutil').rmtree,result['output_dir'])
        self.assertEqual(result['frames'],[])
        self.assertTrue(result['has_audio'])
        self.assertIsNone(result['video'])

    def test_transcribe_calls_local_backend_without_cloud(self):
        stub=self.root/'local-transcribe'; (stub/'scripts').mkdir(parents=True,exist_ok=True)
        (stub/'SKILL.md').write_text('stub',encoding='utf-8')
        (stub/'scripts/transcribe.py').write_text("import sys; from pathlib import Path; out=Path(sys.argv[sys.argv.index('--output-dir')+1]); (out/'transcript.md').write_text('local test',encoding='utf-8'); (out/'transcript.srt').write_text('subtitle',encoding='utf-8')",encoding='utf-8')
        with patch.object(self.media,'find_skill',return_value=str(stub/'SKILL.md')):
            result,_=self.media.inspect_local(self.audio,frames=0,transcribe=True)
        self.addCleanup(__import__('shutil').rmtree,result['output_dir'])
        self.assertEqual(Path(result['transcripts'][0]).read_text(),'local test')
        self.assertTrue(Path(result['output_dir'],'transcript.srt').is_file())

    def test_no_audio_cannot_extract(self):
        with self.assertRaisesRegex(ValueError,'没有音轨'):
            self.media.inspect_local(self.silent,extract_audio=True)

    def test_invalid_media_rejected_without_archive(self):
        bad=self.root/'broken.mp4'; bad.write_bytes(b'not decrypted video')
        with self.assertRaises(RuntimeError):
            self.media.inspect_local(bad)

    def test_cli_report_and_repeat_no_overwrite(self):
        for _ in range(2):
            result=subprocess.run([sys.executable,'-B',str(HERE/'read.py'),str(self.video),'--frames','1',
                                   '--archive-dir',str(self.root/'cli-vault'),'--title','CLI'],
                                  capture_output=True,text=True,encoding='utf-8')
            self.assertEqual(result.returncode,0,result.stderr)
            report=json.loads(result.stdout)
            self.addCleanup(__import__('shutil').rmtree,report['output_dir'])
            self.assertTrue(Path(report['output_dir'],'report.json').is_file())
        self.assertEqual(len(list((self.root/'cli-vault').glob('*.mp4'))),2)
        self.assertTrue(self.video.is_file())

if __name__ == '__main__':
    unittest.main()
