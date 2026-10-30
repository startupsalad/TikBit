#!/usr/bin/env python
"""Install optional media backend Skills; never install models/certificates/proxies."""
import argparse
import os
from pathlib import Path, PurePosixPath
import shutil
import tempfile
import sys
import sys
import zipfile

HERE=Path(__file__).resolve().parent
SKILLS=('video-catcher','watch','local-transcribe')


def target_roots(vault=None, engine='both'):
    if vault:
        base=Path(vault).expanduser().resolve()
        if not base.is_dir():
            raise ValueError('知识库目录不存在')
        roots={'claude':base/'.claude/skills','codex':base/'.agents/skills'}
    else:
        roots={'claude':Path(os.environ.get('CLAUDE_CONFIG_DIR',str(Path.home()/'.claude'))).expanduser()/'skills',
               'codex':Path(os.environ.get('CODEX_HOME',str(Path.home()/'.codex'))).expanduser()/'skills'}
    return [root for name,root in roots.items() if engine in ('both',name)]


def install(vault=None,engine='both',skills=SKILLS,dry_run=False):
    roots=target_roots(vault,engine)
    backup=None
    changed=[]
    with zipfile.ZipFile(HERE/'视频音频处理工具包.zip') as package:
        selected=[]
        for info in package.infolist():
            path=PurePosixPath(info.filename)
            if path.is_absolute() or '..' in path.parts or any(':' in p for p in path.parts) or "\\" in info.filename:
                raise ValueError('ZIP包含不安全路径')
            if path.name in ('.WeDrive','.DS_Store','Thumbs.db') or info.is_dir():
                continue
            if len(path.parts)<3 or path.parts[0]!='skills' or path.parts[1] not in skills:
                continue
            if (info.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError('ZIP中的链接不允许安装')
            selected.append((Path(*path.parts[1:]),package.read(info)))
        for name in skills:
            if not any(path==Path(name)/'SKILL.md' for path,data in selected):
                raise ValueError(f'ZIP缺少{name}/SKILL.md')
        for root in roots:
            print(f'Skill目标：{root}')
            if dry_run:
                continue
            for relative,data in selected:
                destination=root/relative
                # Resolve before writing to avoid traversing existing linked folders.
                if not destination.resolve().is_relative_to(root.resolve()):
                    raise ValueError('目标链接越出Skill目录')
                if destination.is_file() and destination.read_bytes()==data:
                    continue
                if destination.exists():
                    backup=backup or Path(tempfile.mkdtemp(prefix='tikbit-media-skill-backup-'))
                    saved=backup/str(len(changed))/relative
                    saved.parent.mkdir(parents=True,exist_ok=True)
                    shutil.copy2(destination,saved)
                destination.parent.mkdir(parents=True,exist_ok=True)
                destination.write_bytes(data)
                changed.append(str(destination))
    print(f'已更新{len(changed)}个文件；依赖/模型另按需安装。')
    if backup:
        print(f'旧文件备份：{backup}')
    return changed


def main():
    for stream in (sys.stdout,sys.stderr):
        if hasattr(stream,'reconfigure'):
            stream.reconfigure(encoding='utf-8',errors='replace')
    for stream in (sys.stdout,sys.stderr):
        if hasattr(stream,'reconfigure'):
            stream.reconfigure(encoding='utf-8',errors='replace')
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--vault',type=Path)
    parser.add_argument('--engine',choices=('both','claude','codex'),default='both')
    parser.add_argument('--skill',choices=SKILLS,action='append')
    parser.add_argument('--dry-run',action='store_true')
    args=parser.parse_args()
    try:
        install(args.vault,args.engine,tuple(args.skill or SKILLS),args.dry_run)
    except (OSError,ValueError,zipfile.BadZipFile) as error:
        parser.exit(2,f'安装未完成：{error}\n')

if __name__=='__main__':
    main()
