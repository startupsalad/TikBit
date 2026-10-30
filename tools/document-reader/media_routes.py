"""Small, dependency-free URL classifier shared by the media entry."""
from pathlib import PurePosixPath
from urllib.parse import urlsplit

MEDIA_EXTENSIONS = {'.mp4', '.m4v', '.mov', '.mkv', '.webm', '.avi', '.flv', '.wmv',
                    '.ts', '.mts', '.m2ts', '.mpg', '.mpeg', '.mp3', '.wav', '.m4a',
                    '.aac', '.flac', '.ogg', '.opus', '.aiff', '.wma'}

def url_kind(url):
    try:
        parts = urlsplit(url)
        host = (parts.hostname or '').lower()
        if parts.scheme.lower() not in ('http', 'https') or parts.username or parts.password:
            return 'web'
    except ValueError:
        return 'web'
    path = parts.path
    if host == 'weixin.qq.com' and path.startswith('/sph/'):
        return 'channels'
    if host == 'mp.weixin.qq.com':
        return 'article'
    if PurePosixPath(path).suffix.lower() in MEDIA_EXTENSIONS:
        return 'video'
    if host in ('youtu.be', 'b23.tv', 'v.douyin.com', 'v.kuaishou.com') and path.strip('/'):
        return 'video'
    host = host.removeprefix('www.').removeprefix('m.')
    if host in ('youtube.com', 'music.youtube.com') and (path == '/watch' or path.startswith(('/shorts/', '/live/', '/embed/'))):
        return 'video'
    if host == 'bilibili.com' and path.startswith(('/video/', '/bangumi/play/')):
        return 'video'
    if host in ('douyin.com', 'kuaishou.com') and path.startswith(('/video/', '/short-video/')):
        return 'video'
    if host in ('tiktok.com', 'x.com', 'twitter.com') and ('/video/' in path or '/status/' in path):
        return 'video'
    if host == 'vimeo.com' and path.strip('/').isdigit():
        return 'video'
    return 'web'
