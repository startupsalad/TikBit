#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
检查环境.py —— 到一台新机器上先跑这个，看能读什么、缺什么

    python 检查环境.py           # 查 Python 库 + 转换引擎
    python 检查环境.py --quick    # 只查 Python 库（不起 COM，秒出）

会告诉你：
  · 哪些格式现在就能读
  · 哪些还差东西，差什么，怎么补
装齐不是必须的。少一样只是少一条路，工具包会自动往下降级。
"""

import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

OK, NO = '[有]', '[缺]'

# (import 名, pip 名, 干什么用, 缺了会怎样)
LIBS = [
    ('fitz', 'pymupdf', 'PDF 抽文字 / PDF 转 PNG', '看不了 PPT 版面，PDF 抽字退到 pypdf'),
    ('docx', 'python-docx', '.docx 直接抽正文', '.docx 要绕 PDF，慢且丢格式'),
    ('openpyxl', 'openpyxl', '.xlsx 抽表格', '.xlsx 读不了'),
    ('PIL', 'pillow', '图片压缩 / 长图切片', 'read_img.py 完全不能用'),
    ('markitdown', 'markitdown[all]', '无引擎时的纯文字兜底', '一个 Office 引擎都没有时彻底读不了'),
    ('pypdf', 'pypdf', 'PDF 抽文字备用', '无所谓，有 pymupdf 就够'),
    ('requests', 'requests', '公众号文章抓取', '读不了 mp.weixin.qq.com 链接'),
    ('bs4', 'beautifulsoup4', '公众号正文解析', '读不了 mp.weixin.qq.com 链接'),
    ('pillow_heif', 'pillow-heif', 'iPhone 的 .heic 照片', '.heic 读不了（改用 .jpg 导出）'),
    ('win32com.client', 'pywin32', '调 Office / WPS 转格式', 'Win 上只剩 LibreOffice 和纯文字兜底'),
]

# 老格式必须靠引擎转，列出来让人知道引擎全缺时的代价
NEED_ENGINE = '.doc .xls .ppt .rtf .wps .et .dps'


def fix_console():
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            pass


def has(mod):
    try:
        __import__(mod)
        return True
    except Exception:
        return False


def check_libs():
    print('=' * 62)
    print(' Python 库')
    print('=' * 62)
    missing = []
    for mod, pip, why, cost in LIBS:
        if has(mod):
            print(f'{OK} {pip:<20} {why}')
        else:
            print(f'{NO} {pip:<20} {why}')
            print(f'     └─ 缺了：{cost}')
            missing.append(pip)
    return missing


def check_engines(quick=False):
    print()
    print('=' * 62)
    print(' 转换引擎（老格式和"看版面"靠它）')
    print('=' * 62)

    try:
        import engine
    except Exception as e:
        print(f'{NO} engine.py 加载失败：{e}')
        return []

    found = []

    soffice = engine.find_soffice()
    if soffice:
        print(f'{OK} LibreOffice   {soffice}')
        found.append('soffice')
    else:
        print(f'{NO} LibreOffice   没装（Mac / Linux 上是主力，Win 上可选）')

    if not engine.IS_WIN:
        print('     非 Windows，MS Office / WPS 的 COM 接口用不了，靠 LibreOffice')
        return found

    if quick:
        print('  （--quick 跳过 COM 探测。起 COM 要几秒，去掉 --quick 才查）')
        return found

    print('  正在探 COM，每个几秒……')
    for eng, label in (('mso', 'MS Office'), ('wps', 'WPS Office')):
        ok = [k for k in ('word', 'excel', 'ppt') if engine.probe(k, eng)]
        if ok:
            names = {'word': 'Word', 'excel': 'Excel', 'ppt': 'PPT'}
            print(f'{OK} {label:<13} 可用：{" / ".join(names[k] for k in ok)}')
            found.append(eng)
        else:
            print(f'{NO} {label:<13} 调不起来（没装，或装了但 COM 注册不全）')

    return found


def summary(missing, engines):
    print()
    print('=' * 62)
    print(' 结论')
    print('=' * 62)

    can, cant = [], []

    (can if has('docx') else cant).append('.docx Word')
    (can if has('openpyxl') else cant).append('.xlsx Excel')
    (can if has('fitz') or has('pypdf') else cant).append('.pdf')
    (can if has('PIL') else cant).append('图片 / 长图')
    (can if has('requests') and has('bs4') else cant).append('公众号文章')
    can.append('网页（curl 内置，无需装库）')

    if engines:
        can.append(f'.pptx 看版面（转 PDF，用 {"/".join(engines)}）')
        can.append(f'老格式 {NEED_ENGINE}')
    elif has('markitdown'):
        cant.append(f'老格式 {NEED_ENGINE}（无引擎，只能靠 markitdown 抠纯文字，丢版面）')
        cant.append('.pptx 看版面（只能出纯文字）')
    else:
        cant.append(f'老格式 {NEED_ENGINE}（无引擎也无 markitdown，读不了）')
        cant.append('.pptx（读不了）')

    for x in can:
        print(f'  能读  {x}')
    for x in cant:
        print(f'  不行  {x}')

    print()
    if missing:
        print('补齐命令：')
        print(f'  pip install {" ".join(missing)}')
    else:
        print('Python 库齐了。')

    if not engines:
        print()
        print('一个转换引擎都没有。装任意一个即可（不用装全）：')
        print('  · Windows：装 MS Office 或 WPS Office（装了就能用，无需额外配置）')
        print('  · Mac / Linux：brew install --cask libreoffice')
        print('    或 https://www.libreoffice.org/download/')

    if not shutil.which('curl'):
        print()
        print('注意：没找到 curl，读网页会失败。Win10 1803+ / Mac 自带，一般不缺。')


def main():
    fix_console()
    quick = '--quick' in sys.argv
    print()
    print(f'Python {sys.version.split()[0]}  |  {sys.platform}')
    print(f'工具包目录 {HERE}')
    missing = check_libs()
    engines = check_engines(quick)
    summary(missing, engines)
    print()
    return 0


if __name__ == '__main__':
    sys.exit(main())
