"""Bounded WeChat Channels share-link resolution and Tencent CDN download.

The default adapter uses a public third-party service. No WeChat credentials,
certificate installation, browser interaction or proxy modification is involved.
"""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import tempfile
import time
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

DEFAULT_RESOLVERS = ('https://api.bugpk.com/api/wxsph',
                     'https://api.bugpk.com/api/short_videos')
MEDIA_HOSTS = frozenset({'finder.video.qq.com'})
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36'


class ResolverError(RuntimeError):
    pass


def share_link(value):
    try:
        parts = urlsplit(value)
        if (parts.scheme.lower() != 'https' or parts.hostname != 'weixin.qq.com'
                or parts.username or parts.password or parts.port not in (None, 443)
                or not re.fullmatch(r'/sph/[A-Za-z0-9]+/?', parts.path)):
            raise ValueError()
    except ValueError as error:
        raise ResolverError('请提供有效的https://weixin.qq.com/sph/...视频号分享链接') from error
    identifier = parts.path.strip('/').split('/')[1]
    return identifier, 'https://weixin.qq.com/sph/'+identifier


def checked_https(value, hosts=None):
    try:
        parts = urlsplit(value)
        if (parts.scheme != 'https' or not parts.hostname or parts.username or parts.password
                or parts.port not in (None, 443) or (hosts is not None and parts.hostname not in hosts)):
            raise ValueError()
    except (ValueError, TypeError) as error:
        raise ResolverError('服务返回的下载地址不在允许的HTTPS腾讯视频域名内') from error
    return value


class RestrictedRedirect(HTTPRedirectHandler):
    def __init__(self, hosts):
        self.hosts = hosts
        super().__init__()

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        checked_https(newurl, self.hosts)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def open_https(url, hosts, timeout, referer):
    checked_https(url, hosts)
    request = Request(url, headers={'User-Agent': USER_AGENT, 'Referer': referer})
    return build_opener(RestrictedRedirect(hosts)).open(request, timeout=timeout)


def resolver_endpoints(custom=None):
    configured = custom or os.environ.get('TIKBIT_CHANNELS_RESOLVER_URL')
    endpoints = (configured,) if configured else DEFAULT_RESOLVERS
    for value in endpoints:
        checked_https(value)
    return endpoints


def resolve(value, endpoint=None):
    identifier, canonical = share_link(value)
    failures = []
    for service in resolver_endpoints(endpoint):
        parts = urlsplit(service)
        query = dict(parse_qsl(parts.query))
        query['url'] = canonical
        request_url = urlunsplit(parts._replace(query=urlencode(query), fragment=''))
        host = parts.hostname
        try:
            with open_https(request_url, {host}, 40, 'https://www.baidu.com/') as response:
                raw = response.read(2*1024*1024+1)
            if len(raw) > 2*1024*1024:
                raise ResolverError('解析响应过大')
            payload = json.loads(raw)
            if not isinstance(payload, dict):
                raise ResolverError('解析服务返回格式异常')
            data = payload.get('data')
            if payload.get('code') == 429:
                raise ResolverError('解析服务限流，请稍后在本对话重试')
            if payload.get('code') != 200 or not isinstance(data, dict) or not data.get('url'):
                failures.append('服务未返回视频地址')
                continue
            media_url = checked_https(data['url'], MEDIA_HOSTS)
            author = data.get('author')
            if isinstance(author, dict):
                author = author.get('name', '')
            return {'id': identifier, 'source_url': canonical, 'media_url': media_url,
                    'title': str(data.get('title') or data.get('desc') or '')[:500],
                    'author': str(author or '')[:200], 'quality': str(data.get('quality') or '')[:100],
                    'resolver': urlunsplit(parts._replace(query='', fragment=''))}
        except HTTPError as error:
            if error.code == 429:
                raise ResolverError('解析服务限流，请稍后在本对话重试') from error
            failures.append('HTTP '+str(error.code))
        except (URLError, TimeoutError, OSError, ValueError) as error:
            failures.append(type(error).__name__)
    raise ResolverError('视频号自动解析暂不可用（'+', '.join(failures)+'）；视频尚未下载。')


def download(value, endpoint=None, max_bytes=512*1024*1024, timeout=180):
    resolution = resolve(value, endpoint)
    root = Path(tempfile.mkdtemp(prefix='docread-channels-auto-'))
    partial = root/(resolution['id']+'.part')
    target = root/(resolution['id']+'.mp4')
    total, started = 0, time.monotonic()
    try:
        with open_https(resolution['media_url'], MEDIA_HOSTS, 40, 'https://channels.weixin.qq.com/') as response:
            if response.status != 200:
                raise ResolverError('腾讯视频文件响应不完整')
            content_type = response.headers.get('Content-Type', '').split(';')[0].strip().lower()
            if content_type not in ('video/mp4', 'application/octet-stream'):
                raise ResolverError('下载响应不是视频文件')
            length = response.headers.get('Content-Length')
            expected = int(length) if length is not None else None
            if expected is not None and (expected <= 0 or expected > max_bytes):
                raise ResolverError('视频文件为空或超过下载大小限制')
            with partial.open('xb') as output:
                while True:
                    chunk = response.read(1024*1024)
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > max_bytes or time.monotonic()-started > timeout:
                        raise ResolverError('视频下载达到大小或时长限制，请稍后在本对话重试')
                    output.write(chunk)
        if not total or (expected is not None and total != expected):
            raise ResolverError('视频文件下载不完整；未交付为成品')
        partial.rename(target)
    except (URLError, TimeoutError, OSError, ValueError) as error:
        # Only remove this attempt's partial file in its dedicated system temp dir.
        if partial.exists():
            partial.unlink()
        raise ResolverError('视频号文件下载未完成；可在本对话重试。') from error
    except Exception:
        if partial.exists():
            partial.unlink()
        raise
    metadata = {key: item for key, item in resolution.items() if key != 'media_url'}
    metadata.update(bytes=total, downloaded_at=datetime.now(timezone.utc).isoformat(timespec='seconds'),
                    resolution='第三方解析服务返回；媒体从腾讯CDN下载', proxy_modified=False)
    # Never persist signed CDN addresses or query tokens in notes or reports.
    (root/'download.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding='utf-8')
    return target, metadata
