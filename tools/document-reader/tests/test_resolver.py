"""Offline contracts for the direct link path; never call public services in tests."""
import io
from contextlib import redirect_stdout
import json
import tempfile
from pathlib import Path
import shutil
import sys
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(HERE))
import channels_resolver as resolver
import read_channels


class Response(io.BytesIO):
    def __init__(self, content, headers=None, status=200):
        super().__init__(content)
        self.status=status
        self.headers=headers or {}


class ResolverTests(unittest.TestCase):
    def test_share_url_canonicalizes_and_rejects_host_credentials_and_lookalikes(self):
        self.assertEqual(resolver.share_link('https://weixin.qq.com/sph/Ab3?private=omit'),
                         ('Ab3','https://weixin.qq.com/sph/Ab3'))
        for url in ['https://weixin.qq.com.evil.test/sph/a','http://weixin.qq.com/sph/a',
                    'https://user@weixin.qq.com/sph/a','https://weixin.qq.com:123/sph/a',
                    'https://weixin.qq.com/other/a','https://weixin.qq.com/sph/../../a']:
            with self.assertRaises(resolver.ResolverError):
                resolver.share_link(url)

    def test_resolution_uses_explicit_provider_and_rejects_non_tencent_media(self):
        payload={'code':200,'data':{'url':'https://evil.test/video.mp4','title':'fake'}}
        with patch.object(resolver,'open_https',return_value=Response(json.dumps(payload).encode())):
            with self.assertRaises(resolver.ResolverError):
                resolver.resolve('https://weixin.qq.com/sph/test')

    def test_rate_limit_does_not_tight_loop_or_silently_switch_manual_capture(self):
        payload={'code':429,'data':{'retry_after':10}}
        with patch.object(resolver,'open_https',return_value=Response(json.dumps(payload).encode())) as request:
            with self.assertRaisesRegex(resolver.ResolverError,'限流'):
                resolver.resolve('https://weixin.qq.com/sph/test')
        self.assertEqual(request.call_count,1)

    def test_download_validates_length_and_hides_signed_url_in_saved_metadata(self):
        resolution={'id':'abc','source_url':'https://weixin.qq.com/sph/abc',
                    'media_url':'https://finder.video.qq.com/video?secret=DO_NOT_SAVE',
                    'title':'测试','author':'作者','quality':'高清','resolver':'https://example.test/api'}
        with patch.object(resolver,'resolve',return_value=resolution), patch.object(
                resolver,'open_https',return_value=Response(b'video-data',{'Content-Type':'video/mp4','Content-Length':'10'})):
            path,metadata=resolver.download(resolution['source_url'])
        self.addCleanup(shutil.rmtree,path.parent)
        self.assertEqual(path.read_bytes(),b'video-data')
        self.assertNotIn('DO_NOT_SAVE',(path.parent/'download.json').read_text(encoding='utf-8'))
        self.assertNotIn('media_url',metadata)
        self.assertFalse(list(path.parent.glob('*.part')))

    def test_partial_or_over_limit_is_never_returned_as_video(self):
        resolution={'id':'abc','source_url':'https://weixin.qq.com/sph/abc',
                    'media_url':'https://finder.video.qq.com/video','title':'x'}
        for length,limit in [('1000',100),('20',1000)]:
            with patch.object(resolver,'resolve',return_value=resolution), patch.object(
                    resolver,'open_https',return_value=Response(b'short',{'Content-Type':'video/mp4','Content-Length':length})):
                with self.assertRaises(resolver.ResolverError):
                    resolver.download(resolution['source_url'],max_bytes=limit)

    def test_media_redirect_stays_on_approved_https_host(self):
        guard=resolver.RestrictedRedirect(resolver.MEDIA_HOSTS)
        for url in ('http://finder.video.qq.com/video','https://evil.test/video'):
            with self.assertRaises(resolver.ResolverError):
                guard.redirect_request(None,None,302,'',{},url)

    def test_speech_backend_failure_retains_download_and_returns_resumable_result(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); source=root/'video.mp4'; source.write_bytes(b'already-downloaded')
            report={'status':'prepared','output_dir':str(root),'source':str(source),'check_level':'quick'}
            metadata={'duration':1,'video':{'width':10,'height':10}}
            stdout=io.StringIO()
            with patch.object(resolver,'download',return_value=(source,{'source_url':'https://weixin.qq.com/sph/test','title':'x'})) as download, patch.object(
                    read_channels,'inspect_local',side_effect=[(report,metadata),RuntimeError('backend missing')]), redirect_stdout(stdout):
                code=read_channels.main(['https://weixin.qq.com/sph/test','--transcribe'])
            self.assertEqual(code,4)
            result=json.loads(stdout.getvalue())
            self.assertEqual(result['status'],'downloaded_transcription_pending')
            self.assertTrue(source.exists())
            self.assertEqual(download.call_count,1)


if __name__=='__main__':
    unittest.main()
