#!/usr/bin/env python
"""Install the document routing Skill for Claude and GPT; no dependencies installed."""
import argparse
import os
from pathlib import Path
import shutil
import tempfile
import sys
import sys

HERE = Path(__file__).resolve().parent


def targets(vault=None, engine='both'):
    if vault:
        base=Path(vault).expanduser().resolve()
        if not base.is_dir():
            raise ValueError('知识库目录不存在')
        roots={'claude':base/'.claude/skills','codex':base/'.agents/skills'}
    else:
        roots={'claude':Path(os.environ.get('CLAUDE_CONFIG_DIR',str(Path.home()/'.claude'))).expanduser()/'skills',
               'codex':Path(os.environ.get('CODEX_HOME',str(Path.home()/'.codex'))).expanduser()/'skills'}
    return [root/'文档读取编辑' for name,root in roots.items() if engine in ('both',name)]


def install(vault=None, engine='both', dry_run=False):
    body=(HERE/'skill/SKILL.md').read_text(encoding='utf-8-sig').replace('{{工具包路径}}',HERE.as_posix())
    payload={'SKILL.md':body.encode('utf-8'),'references/video-channels.md':(HERE/'references/video-channels.md').read_bytes()}
    changed=[]
    backup=None
    for target in targets(vault,engine):
        print(f'Skill目标：{target}')
        if dry_run:
            continue
        for relative,data in payload.items():
            destination=target/relative
            if not destination.resolve().is_relative_to(target.resolve()):
                raise ValueError('目标链接越出Skill目录')
            if destination.is_file() and destination.read_bytes()==data:
                continue
            if destination.exists():
                backup=backup or Path(tempfile.mkdtemp(prefix='tikbit-skill-backup-'))
                saved=backup/str(len(changed))/relative
                saved.parent.mkdir(parents=True,exist_ok=True)
                shutil.copy2(destination,saved)
            destination.parent.mkdir(parents=True,exist_ok=True)
            destination.write_bytes(data)
            changed.append(str(destination))
    print(f'已更新{len(changed)}个文件；未安装模型、证书或代理。')
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
    parser.add_argument('--dry-run',action='store_true')
    args=parser.parse_args()
    try:
        install(args.vault,args.engine,args.dry_run)
    except (OSError,ValueError) as error:
        parser.exit(2,f'安装未完成：{error}\n')

if __name__ == '__main__':
    main()
