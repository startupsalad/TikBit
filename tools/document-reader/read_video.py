#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Local media inspection, bounded frame extraction and explicit archive.

python read.py video.mp4 --frames 8
python read.py video.mp4 --full-check --archive-dir 视频号下载 --title 标题 --source-url URL
python read.py https://weixin.qq.com/sph/example

URL mode prints backend/capture instructions only; it never fetches a URL,
installs software, invokes cloud APIs or changes a system proxy.
"""
import argparse
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from media_archive import archive_media
from media_routes import url_kind

HERE = Path(__file__).resolve().parent


def find_binary(name):
    configured = os.environ.get(name.upper() + '_PATH')
    if configured and Path(configured).is_file():
        return str(Path(configured).resolve())
    found = shutil.which(name)
    if found:
        return found
    # ffprobe and ffmpeg are commonly installed together, including ~/bin.
    for folder in (Path.home()/'bin', Path.home()/'.local/bin'):
        path = folder / (name + ('.exe' if os.name == 'nt' else ''))
        if path.is_file():
            return str(path)
    return None


def run_tool(command, timeout=120):
    result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=timeout)
    if result.returncode:
        raise RuntimeError(f'{Path(command[0]).name}失败：{result.stderr[-2500:]}')
    return result.stdout


def require_binary(name):
    binary = find_binary(name)
    if not binary:
        raise RuntimeError(f'缺少{name}。请先验证 ffmpeg 和 ffprobe；Mac: brew install ffmpeg；Windows: winget install --id Gyan.FFmpeg --exact；Linux用发行版包管理器。也可设置 FFMPEG_PATH/FFPROBE_PATH 指向已有二进制。')
    return binary


def probe(source):
    binary = require_binary('ffprobe')
    raw = json.loads(run_tool([binary, '-v','error','-protocol_whitelist','file,pipe','-show_format','-show_streams','-of','json',str(source)], 60))
    streams = raw.get('streams', [])
    video = next((s for s in streams if s.get('codec_type') == 'video' and not s.get('disposition',{}).get('attached_pic')), None)
    audio = next((s for s in streams if s.get('codec_type') == 'audio'), None)
    if not video and not audio:
        raise ValueError('没有可解码的音视频流')
    durations = [raw.get('format',{}).get('duration')] + [s.get('duration') for s in streams]
    duration = 0.0
    for value in durations:
        try:
            parsed = float(value)
            if math.isfinite(parsed) and parsed > 0:
                duration = max(duration, parsed)
        except (TypeError, ValueError):
            pass
    if not duration:
        raise ValueError('无法确定有效时长；请确认已解密、下载完成且不是直播流')
    return {'duration':duration, 'video':video, 'audio':audio}


def validate(source, metadata, full=False):
    binary = require_binary('ffmpeg')
    cmd = [binary,'-nostdin','-v','error','-xerror','-protocol_whitelist','file,pipe','-i',str(source),'-map','0:v:0?','-map','0:a:0?']
    if not full:
        cmd += ['-t','5']
    run_tool(cmd+['-f','null','-'], max(120, metadata['duration']*4+60) if full else 120)
    return 'full' if full else 'quick'


def skill_roots():
    values = [Path.cwd()/'.agents/skills', Path.cwd()/'.claude/skills']
    for env in ('CODEX_HOME','CLAUDE_CONFIG_DIR'):
        if os.environ.get(env):
            values.append(Path(os.environ[env]).expanduser()/'skills')
    values += [Path.home()/'.agents/skills',Path.home()/'.codex/skills',Path.home()/'.claude/skills']
    return list(dict.fromkeys(values))


def find_skill(name):
    # A sibling tool installation may carry the unzipped video-audio package.
    for root in skill_roots() + [HERE.parent/'video-audio/skills']:
        path = root/name/'SKILL.md'
        if path.is_file():
            return str(path.resolve())
    return None


def url_guidance(source):
    kind = url_kind(source)
    if kind == 'channels':
        return {'status':'manual_capture_required', 'kind':kind,
                'guide':str(HERE/'references/video-channels.md'),
                'steps':['使用res-downloader，首次按上游说明安装对应平台版本与证书；自动开启代理保持关闭。',
                         '记录原代理和实际下载目录，再开启抓取/启动代理。',
                         '在电脑微信文件传输助手播放；没有捕获时完整退出重开微信。',
                         '选择对应视频，解密下载，或下载后执行视频解密（视频号）。',
                         '停止抓取并核对恢复原代理；拿到本地文件再运行read.py校验归档。'],
                'network_performed':False,'proxy_modified':False,
                'note':'不对视频号分享链接反复尝试curl/yt-dlp；本输出只提供操作流程，视频尚未下载。'}
    backend = find_skill('video-catcher') or find_skill('watch')
    return {'status':'backend_instructions_required' if backend else 'optional_backend_missing',
            'kind':kind, 'backend_skill':backend,
            'install_guide':str(HERE.parent/'video-audio/INSTALL.md'),
            'install_url':'https://github.com/startupsalad/TikBit/tree/main/tools/video-audio',
            'next':'先读取已发现的Skill，按用户的视频下载需求执行；获得本地文件后回到read.py。缺后端时按INSTALL安装，不能声称已经下载。',
            'network_performed':False}


def frame_times(duration, count):
    return [duration*(i+0.5)/count for i in range(count)] if count else []


def inspect_local(source, frames=8, full=False, extract_audio=False, transcribe=False):
    source = Path(source).expanduser().resolve()
    if not source.is_file() or source.stat().st_size == 0:
        raise ValueError('本地文件不存在或为空')
    before = source.stat()
    metadata = probe(source)
    level = validate(source, metadata, full)
    if (extract_audio or transcribe) and not metadata['audio']:
        raise ValueError('文件没有音轨，不能抽音频或转写；可以仅抽帧')
    transcribe_skill = find_skill('local-transcribe') if transcribe else None
    if transcribe and not transcribe_skill:
        raise RuntimeError('缺少local-transcribe；按video-audio/INSTALL.md安装后再加--transcribe。')
    output = Path(tempfile.mkdtemp(prefix='docread-media-'))
    binary = require_binary('ffmpeg')
    result = {'status':'prepared', 'source':str(source), 'duration':metadata['duration'],
              'video':({k:metadata['video'].get(k) for k in ('width','height','codec_name')} if metadata['video'] else None),
              'has_audio':bool(metadata['audio']), 'check_level':level,
              'coverage':'抽帧为稀疏采样；quick仅解码开头最多5秒；prepared不代表AI已阅读全部视频。',
              'output_dir':str(output), 'frames':[]}
    frame_duration=metadata['duration']
    if metadata['video']:
        try:
            video_duration=float(metadata['video'].get('duration',frame_duration))
            if math.isfinite(video_duration) and video_duration>0:
                frame_duration=min(frame_duration,video_duration)
        except (TypeError,ValueError):
            pass
    for index, seconds in enumerate(frame_times(frame_duration, frames if metadata['video'] else 0),1):
        path = output/f'frame_{index:03d}_{seconds:.3f}s.jpg'
        run_tool([binary,'-nostdin','-v','error','-ss',f'{seconds:.6f}','-protocol_whitelist','file,pipe','-i',str(source),
                  '-map',f'0:{metadata["video"]["index"]}', '-frames:v','1',
                  '-vf',"scale=w='min(1280,iw)':h=-2",'-q:v','3',str(path)])
        if not path.is_file() or path.stat().st_size == 0:
            raise ValueError(f'{seconds:.3f}秒抽帧失败；不能将不完整采样当作成功')
        result['frames'].append({'seconds':round(seconds,3), 'path':str(path)})
    if extract_audio:
        audio = output/'audio.wav'
        run_tool([binary,'-nostdin','-v','error','-protocol_whitelist','file,pipe','-i',str(source),'-map','0:a:0','-vn','-ac','1','-ar','16000',str(audio)], max(120,metadata['duration']*2))
        result['audio'] = str(audio)
    if transcribe:
        script = Path(transcribe_skill).parent/'scripts/transcribe.py'
        if not script.is_file():
            raise RuntimeError('local-transcribe脚本不完整，请修复该工具安装')
        print('本地转写已显式启用；首次可能下载约GB级模型，CPU转写可能较慢。',file=sys.stderr)
        env = dict(os.environ, PYTHONIOENCODING='utf-8', PYTHONDONTWRITEBYTECODE='1')
        # No cloud fallback or key access. Transcription can take a long time.
        subprocess.run([sys.executable,str(script),str(source),'--output-dir',str(output)],check=True,stdout=sys.stderr,env=env)
        notes = list(output.glob('*.md'))
        if not notes:
            raise RuntimeError('转写进程结束但没有文字稿，不能当作成功')
        result['transcripts'] = [str(p) for p in notes]
    after = source.stat()
    if (before.st_size,before.st_mtime_ns) != (after.st_size,after.st_mtime_ns):
        raise ValueError('处理期间源文件变化；请等下载完成后重试')
    return result, metadata


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream,'reconfigure'):
            stream.reconfigure(encoding='utf-8',errors='replace')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source')
    parser.add_argument('--frames',type=int,default=8,help='0到200，默认8张带时间戳图片')
    parser.add_argument('--full-check',action='store_true',help='全片解码；默认只试解码开头最多5秒')
    parser.add_argument('--audio',action='store_true',help='显式抽16k单声道WAV到系统临时目录')
    parser.add_argument('--transcribe',action='store_true',help='调用已安装local-transcribe；首次可能下载模型')
    parser.add_argument('--archive-dir',type=Path,help='显式归档到该目录；保留原文件，不覆盖')
    parser.add_argument('--title',help='仅归档时使用；不自动猜视频标题')
    parser.add_argument('--source-url',default='',help='归档笔记的原始来源链接')
    args=parser.parse_args(argv)
    if not 0 <= args.frames <= 200:
        parser.error('--frames必须在0到200之间')
    if args.title and not args.archive_dir:
        parser.error('--title须与--archive-dir一起使用')
    try:
        if args.source.lower().startswith(('http://','https://')):
            if args.archive_dir or args.audio or args.transcribe or args.full_check:
                raise ValueError('链接尚未下载；这些选项须对本地已下载文件执行')
            result = url_guidance(args.source)
        else:
            result, metadata = inspect_local(args.source,args.frames,args.full_check,args.audio,args.transcribe)
            if args.archive_dir:
                result['archive'] = archive_media(args.source,args.archive_dir,args.title,args.source_url,metadata,result['check_level'])
            Path(result['output_dir'],'report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps(result,ensure_ascii=False,indent=2))
        return 0
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print(f'音视频处理未完成：{error}',file=sys.stderr)
        return 2

if __name__ == '__main__':
    sys.exit(main())
