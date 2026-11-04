#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Automatic WeChat Channels link download/read, plus optional capture sessions.

python read.py URL
python read.py URL --download-only --archive-dir 视频号下载
python read.py URL --transcribe
python read.py URL --doctor
python read.py URL --begin --download-dir DOWNLOADS
python read.py URL --session SESSION --list
python read.py URL --session SESSION --finish --file VIDEO --title TITLE
python read.py URL --session SESSION --check-proxy

Default mode resolves the public share link and downloads from Tencent CDN.
No certificate installation, WeChat UI interaction or proxy change is performed.
"""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

import channels_proxy
import channels_resolver
from media_archive import archive_media, archive_transcripts
from media_routes import MEDIA_EXTENSIONS, url_kind
from read_video import find_binary, inspect_local, probe, url_guidance

HERE = Path(__file__).resolve().parent
CAPTURE_EXTENSIONS = MEDIA_EXTENSIONS - {'.mp3', '.wav', '.m4a', '.aac', '.flac', '.ogg', '.opus', '.aiff', '.wma'}


def stamp():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def scan(directory):
    """Only inspect the explicitly chosen directory, never recurse or follow links."""
    result = {}
    for path in directory.iterdir():
        if path.is_symlink() or not path.is_file():
            continue
        if path.suffix.lower() in CAPTURE_EXTENSIONS | {'.wspkg'}:
            stat = path.stat()
            result[path.name] = {'size': stat.st_size, 'mtime_ns': stat.st_mtime_ns}
    return result


def save(path, value):
    temporary = path.with_suffix('.writing')
    with temporary.open('w', encoding='utf-8', newline='\n') as output:
        json.dump(value, output, ensure_ascii=False, indent=2)
    os.replace(temporary, path)


def load(path, url):
    validate_session_path(path)
    session = json.loads(path.read_text(encoding='utf-8'))
    if session.get('schema') != 'tikbit-channels-1':
        raise ValueError('不是本工具生成的视频号会话')
    if session['source_url'] != url:
        raise ValueError('会话与本次视频号链接不一致；每条链接使用自己的会话')
    return session


def validate_session_path(path):
    path = path.resolve()
    if (not path.is_relative_to(Path(tempfile.gettempdir()).resolve())
            or not path.parent.name.startswith('docread-channels-') or path.name != 'session.json'):
        raise ValueError('会话必须是本工具在系统临时目录生成的session.json，不在知识库创建或清理锁文件')


@contextmanager
def locked(path):
    validate_session_path(path)
    lock = path.with_suffix('.lock')
    try:
        stream = lock.open('x')
    except FileExistsError as error:
        raise ValueError('该会话正在收尾；若上次异常中断，先核查归档及锁文件') from error
    try:
        with stream:
            yield
    finally:
        lock.unlink()  # Only this process's temporary lock, never a vault file.


def doctor():
    paths = [Path.home()/'AppData/Local/Programs/res-downloader/res-downloader.exe',
             Path.home()/'AppData/Local/res-downloader/res-downloader.exe',
             Path.home()/'Applications/res-downloader/res-downloader.exe',
             Path('/Applications/res-downloader.app')]
    found = shutil.which('res-downloader') or next((str(p) for p in paths if p.exists()), None)
    return {'status': 'environment_checked', 'ffmpeg': find_binary('ffmpeg'),
            'ffprobe': find_binary('ffprobe'), 'capture_app': found,
            'capture_app_detection': '仅检查PATH及常见位置；未发现不等于未安装',
            'release_url': 'https://github.com/putyy/res-downloader/releases/latest',
            'certificate': '由用户按官方说明安装并确认信任；本工具不自动安装',
            'proxy_modified': False}


def begin(url, directory):
    directory = Path(directory).expanduser().resolve()
    if not directory.is_dir():
        raise ValueError('请指定res-downloader设置中实际存在的下载目录')
    files = scan(directory)
    session = {'schema': 'tikbit-channels-1', 'source_url': url, 'started': stamp(),
               'download_dir': str(directory), 'before': files,
               'proxy_before': channels_proxy.snapshot(), 'state': 'waiting_for_capture'}
    folder = Path(tempfile.mkdtemp(prefix='docread-channels-'))
    path = folder/'session.json'
    save(path, session)
    return {'status': 'waiting_for_capture', 'session': str(path), 'download_dir': str(directory),
            'proxy_snapshot': session['proxy_before']['status'],
            'guide': str(HERE/'references/video-channels.md'),
            'steps': ['确认自动开启代理关闭；本次基线须在开启抓取前记录。',
                      '手动开启抓取；在电脑微信打开这条链接，播放后选择解密下载。',
                      '手动关闭抓取；告诉AI下载完成，由AI列候选、核对目标并执行收尾。'],
            'downloaded': False, 'proxy_modified': False}


def candidates(session, settle_seconds=1.0):
    directory = Path(session['download_dir'])
    first = scan(directory)
    time.sleep(settle_seconds)
    current = scan(directory)
    videos, caches = [], []
    for name, info in current.items():
        if info == session['before'].get(name):
            continue
        path = directory/name
        stable = first.get(name) == info and info['size'] > 0 and time.time_ns()-info['mtime_ns'] >= 1_000_000_000
        item = {'file': str(path), **info, 'stable': stable}
        if path.suffix.lower() == '.wspkg':
            caches.append(item)
        else:
            if stable:
                try:
                    metadata = probe(path)
                    item.update(duration=metadata['duration'],
                                video=({k: metadata['video'].get(k) for k in ('width', 'height')}
                                       if metadata['video'] else None))
                except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
                    item['inspection_error'] = str(error)[-500:]
            videos.append(item)
    return {'status': 'candidates', 'videos': videos, 'cache_candidates': caches,
            'selection': '必须核对标题/时间/时长并显式指定--file；不自动挑最新或最大的文件。',
            'cache_note': '.wspkg仅为同批缓存候选，未删除；微盘内清理须按待删除规则处理。'}


def proxy_check(session):
    return channels_proxy.compare(session['proxy_before'], channels_proxy.snapshot())


def finish(session_path, session, file, title, archive_dir, frames=8, full=False):
    check = proxy_check(session)
    if session['state'] == 'archived':
        original = Path(session['result']['source'])
        selected = Path(file).expanduser()
        if not selected.is_absolute():
            selected = Path(session['download_dir'])/selected
        if selected.resolve() != original:
            raise ValueError('该会话已归档另一文件；不能将它用于新目标')
        result = dict(session['result'], proxy_check=check, repeated=True)
        result['status'] = 'archived' if check['status'] == 'restored' else 'archived_proxy_review_required'
        return result
    if session['state'] != 'waiting_for_capture':
        raise ValueError('上次收尾中断或归档异常；先核查源文件和候选归档，避免重复复制')
    directory = Path(session['download_dir']).resolve()
    source = Path(file).expanduser()
    source = (directory/source if not source.is_absolute() else source).resolve()
    if source.parent != directory:
        raise ValueError('所选文件不在本会话的下载目录；不跨目录猜测目标')
    listing = candidates(session)
    item = next((v for v in listing['videos'] if Path(v['file']) == source), None)
    if not item:
        raise ValueError('所选文件不是本次新增或变更的视频；请核对会话开始时间及下载目录')
    if not item['stable']:
        raise ValueError('文件尚未稳定或为空；等下载完成再收尾')
    if any(Path(str(source)+suffix).exists() for suffix in ('.part', '.crdownload', '.download', '.tmp')):
        raise ValueError('存在同名下载临时文件；请确认下载完成后再收尾')
    report, metadata = inspect_local(source, frames=frames, full=full)
    if not metadata['video']:
        raise ValueError('所选文件没有视频流，请核对目标')
    after = source.stat()
    if (after.st_size, after.st_mtime_ns) != (item['size'], item['mtime_ns']):
        raise ValueError('源文件仍在变化')
    session['state'] = 'archiving'
    save(session_path, session)
    check = proxy_check(session)
    try:
        archived = archive_media(source, archive_dir, title, session['source_url'], metadata,
                                 report['check_level'], proxy_check=check)
    except Exception:
        session['state'] = 'archive_error'
        save(session_path, session)
        raise
    result = dict(report, archive=archived, proxy_check=check,
                  cache_candidates=listing['cache_candidates'],
                  status='archived' if check['status'] == 'restored' else 'archived_proxy_review_required')
    session.update(state='archived', finished=stamp(), result=result)
    save(session_path, session)
    save(Path(report['output_dir'])/'report.json', result)
    return result


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8', errors='replace')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('url', nargs='?')
    actions = parser.add_mutually_exclusive_group()
    for name in ('doctor', 'begin', 'list', 'finish', 'check-proxy'):
        actions.add_argument('--'+name, action='store_true')
    actions.add_argument('--capture-guide', action='store_true', help='维护分支：显示桌面捕获流程；默认自动解析下载')
    parser.add_argument('--download-dir', type=Path)
    parser.add_argument('--session', type=Path)
    parser.add_argument('--file')
    parser.add_argument('--title')
    parser.add_argument('--archive-dir', type=Path)
    parser.add_argument('--frames', type=int, default=8)
    parser.add_argument('--full-check', action='store_true')
    parser.add_argument('--resolver', help='由维护者配置的HTTPS解析端点；普通用户无需设置')
    parser.add_argument('--download-only', action='store_true', help='只下载校验，不抽帧或转写')
    parser.add_argument('--transcribe', action='store_true', help='调用已有本地转写后端，获取口播文字')
    parser.add_argument('--audio', action='store_true', help='抽出音频供后续读取')
    args = parser.parse_args(argv)
    if not args.doctor and (not args.url or url_kind(args.url) != 'channels'):
        parser.error('需要weixin.qq.com/sph/...视频号链接')
    if not 0 <= args.frames <= 200:
        parser.error('--frames必须在0到200之间')
    try:
        if args.doctor:
            result = doctor()
        elif args.begin:
            if not args.download_dir:
                parser.error('--begin需要--download-dir，不能猜测下载目录')
            result = begin(args.url, args.download_dir)
        elif args.list or args.finish or args.check_proxy:
            if not args.session:
                parser.error('需要--session指定抓取前生成的会话')
            if args.finish and not args.file:
                parser.error('--finish必须显式指定--file')
            with locked(args.session):
                session = load(args.session, args.url)
                if args.list:
                    result = candidates(session)
                elif args.check_proxy:
                    result = {'status': 'proxy_checked', 'proxy_check': proxy_check(session)}
                    session['latest_proxy_check'] = dict(result['proxy_check'], checked_at=stamp())
                    save(args.session, session)
                else:
                    result = finish(args.session, session, args.file, args.title,
                                    args.archive_dir or Path('视频号下载'), args.frames, args.full_check)
        elif args.capture_guide:
            result = url_guidance(args.url)
            result['session_tool'] = str(HERE/'read_channels.py')
            result['next'] = '仅维护分支：先核对实际下载目录，再通过--begin --download-dir开始会话。默认直接给链接即可自动下载读取。'
        else:
            if args.download_dir or args.session or args.file:
                parser.error('桌面抓取参数需配合--begin/--list/--finish；普通链接读取无需这些参数')
            if args.download_only and (args.audio or args.transcribe):
                parser.error('--download-only不能同时请求音频或转写')
            source, downloaded = channels_resolver.download(args.url, args.resolver)
            result, metadata = inspect_local(source, frames=0 if args.download_only else args.frames,
                                             full=args.full_check, extract_audio=args.audio,
                                             transcribe=False)
            result.update(download=downloaded, source_url=downloaded['source_url'],
                          proxy_modified=False, capture_app_required=False,
                          reading='文件已下载校验；AI仍须读取抽帧或文字稿后才能给出内容结论。')
            if args.archive_dir:
                result['archive'] = archive_media(source, args.archive_dir, args.title or downloaded['title'],
                                                  downloaded['source_url'], metadata, result['check_level'],
                                                  proxy_check={'status': 'not_used'})
            if args.transcribe:
                try:
                    speech, _ = inspect_local(source, frames=0, transcribe=True)
                    result['transcripts'] = speech['transcripts']
                except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
                    result.update(status='downloaded_transcription_pending',
                                  transcription_error=str(error)[-1000:],
                                  next='视频已下载保留；AI准备本地转写后端后，对source本地文件继续转写，不重新下载。')
                else:
                    if result.get('archive'):
                        try:
                            result['archive']['transcripts'] = archive_transcripts(result['archive'], speech['transcripts'])
                        except (OSError, ValueError) as error:
                            result.update(status='downloaded_transcript_archive_pending',
                                          transcript_archive_error=str(error)[-1000:],
                                          next='视频与文字稿均已生成；仅文字稿归档待核查，不重新下载或转写。')
            save(Path(result['output_dir'])/'report.json', result)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        check = result.get('proxy_check')
        if result.get('status') in ('downloaded_transcription_pending', 'downloaded_transcript_archive_pending'):
            return 4
        return 3 if check and check['status'] != 'restored' else 0
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print(f'视频号流程未完成：{error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
