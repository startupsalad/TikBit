"""Explicit copy-only media archive. Existing media/notes are never overwritten."""
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import shutil


def safe_title(value):
    value = re.sub(r'[<>:"/\\|?*\[\]#^\x00-\x1f]+', '_', value)
    value = re.sub(r'_+', '_', value).strip(' ._')[:100].rstrip(' .') or '未命名视频'
    if value.split('.')[0].upper() in {'CON','PRN','AUX','NUL', *(f'COM{i}' for i in range(1,10)), *(f'LPT{i}' for i in range(1,10))}:
        value = '_' + value
    return value


def digest(path):
    result = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b''):
            result.update(chunk)
    return result.hexdigest()


def archive_media(source, destination, title, source_url, metadata, check_level):
    source, destination = Path(source).resolve(), Path(destination).resolve()
    if not source.is_file() or source.stat().st_size == 0:
        raise ValueError('源文件不存在或为空')
    before = source.stat()
    expected = digest(source)
    destination.mkdir(parents=True, exist_ok=True)
    base = safe_title(title or source.stem)
    # Reserve with exclusive creation; no force/replace even under concurrent use.
    for index in range(1, 10001):
        stem = base if index == 1 else f'{base} ({index})'
        target = destination / (stem + source.suffix.lower())
        note = destination / (stem + '.md')
        if target.exists() or note.exists():
            continue
        try:
            output = target.open('xb')
        except FileExistsError:
            continue
        try:
            with output, source.open('rb') as incoming:
                shutil.copyfileobj(incoming, output, 1024*1024)
            after = source.stat()
            if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns) or digest(target) != expected:
                raise ValueError('源文件仍在变化或复制哈希不符')
            day = datetime.now().astimezone().date().isoformat()
            source_url = ' '.join(str(source_url).splitlines()).strip()
            # JSON scalar strings are valid YAML strings; title cannot inject markup.
            front = {'type':'视频归档', 'project':'视频资料', 'created':day, 'updated':day,
                     'source_url':source_url or '【待核实：来源链接】',
                     'sha256':expected, 'check_level':check_level}
            text = '---\n' + ''.join(f'{k}: {json.dumps(v, ensure_ascii=False)}\n' for k,v in front.items()) + '---\n\n'
            text += f'# {stem}\n\n![[{target.name}]]\n\n'
            text += f'- 抓取/归档时间：{datetime.now().astimezone().isoformat(timespec="seconds")}\n'
            text += f'- 时长：{metadata["duration"]:.3f}秒\n'
            video = metadata.get('video')
            if video:
                text += f'- 分辨率：{video.get("width",0)} × {video.get("height",0)}\n'
            coverage = '全片解码通过' if check_level == 'full' else '开头最多5秒试解码通过；不代表全片无损'
            text += f'- 文件核验：{coverage}；归档副本SHA-256一致。\n'
            text += '- 代理恢复：待核对；归档脚本不读取或修改系统代理。\n'
            text += '- 原下载文件保留；摘要、作者及发布日期未自动推断。\n'
            with note.open('x', encoding='utf-8', newline='\n') as stream:
                stream.write(text)
            return {'media':str(target), 'note':str(note), 'sha256':expected, 'source_retained':True}
        except Exception as error:
            # Never delete synchronized files; leave partial output for inspection.
            raise ValueError(f'归档未完成，源文件保留；检查候选文件 {target}：{error}') from error
    raise ValueError('同名文件过多，请换标题或目录')
