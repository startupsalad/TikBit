#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
read.py —— 统一入口：丢什么给它都能读

    python read.py 方案.docx
    python read.py 报价表.xlsx
    python read.py 提案.pptx
    python read.py 合同.pdf
    python read.py 长图.png
    python read.py https://startupsalad.com/
    python read.py https://mp.weixin.qq.com/s/xxxx

按扩展名（或网址特征）自动挑底下那个专用脚本，额外参数原样透传过去：

    python read.py 提案.pptx --png --pages 2-3
    python read.py https://xxx.com --links

不确定装了什么引擎，先跑 `python 检查环境.py`。

设计说明
--------
分派用 subprocess 起子进程，不用 import。原因：几个脚本各自管自己的
参数解析和 stdout 编码，直接 import 会把人家的 argv 约定和控制台设置
搅在一起；子进程各跑各的，谁挂了也不带崩整个入口。
"""

import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def fix_console():
    """Win 控制台默认 GBK，中文路径和说明文字会变乱码。这里不 import engine，
    入口脚本尽量零依赖，engine 缺了也得能打出帮助。"""
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            pass


fix_console()

# 扩展名 → 哪个脚本接。同一脚本会出现多次，照抄不合并，方便直接查
ROUTE = {
    # Word 系（含 .doc/.rtf/.wps 老格式，脚本内部会转 PDF 再抽字）
    '.docx': 'read_doc.py', '.docm': 'read_doc.py', '.doc': 'read_doc.py',
    '.rtf': 'read_doc.py', '.wps': 'read_doc.py',
    # Excel 系（.et 是 WPS 表格自家格式）
    '.xlsx': 'read_excel.py', '.xlsm': 'read_excel.py', '.xls': 'read_excel.py',
    '.et': 'read_excel.py',
    # PPT 系（.dps 是 WPS 演示自家格式）
    '.pptx': 'read_ppt.py', '.pptm': 'read_ppt.py', '.ppt': 'read_ppt.py',
    '.dps': 'read_ppt.py',
    # 图片
    '.png': 'read_img.py', '.jpg': 'read_img.py', '.jpeg': 'read_img.py',
    '.gif': 'read_img.py', '.webp': 'read_img.py', '.bmp': 'read_img.py',
    '.tif': 'read_img.py', '.tiff': 'read_img.py',
    '.heic': 'read_img.py', '.heif': 'read_img.py', '.avif': 'read_img.py',
}

# 这些不用工具，Claude 的 Read 直接看就行，别多绕一道
READ_DIRECT = {
    '.pdf': 'PDF 直接用 Read 工具打开即可（能读文字层，也能看版面）',
    '.csv': '纯文本，Read 直接读（别拿 Excel 脚本绕）',
    '.md': '纯文本，Read 直接读',
    '.txt': '纯文本，Read 直接读',
    '.json': '纯文本，Read 直接读',
    '.yaml': '纯文本，Read 直接读', '.yml': '纯文本，Read 直接读',
    '.html': '本地 HTML 用 Read 直接读源码',
    '.htm': '本地 HTML 用 Read 直接读源码',
}


def is_url(s):
    return s.startswith(('http://', 'https://'))


def pick_for_url(url):
    """公众号链接走专用抓取（要解 JS 变量里的正文），其余走通用网页读取"""
    if 'mp.weixin.qq.com' in url:
        return 'fetch_mp_article.py'
    return 'read_web.py'


def run(script, rest):
    path = os.path.join(HERE, script)
    if not os.path.exists(path):
        print(f'缺文件：{script} 不在 {HERE}', file=sys.stderr)
        return 2
    # 子进程继承 stdout，输出直接透传，不中转不缓存
    return subprocess.call([sys.executable, path] + rest)


def main():
    args = sys.argv[1:]
    if not args or args[0] in ('-h', '--help'):
        print(__doc__.strip())
        return 0

    target, rest = args[0], args[1:]

    if is_url(target):
        script = pick_for_url(target)
        print(f'[分派] {script}', file=sys.stderr)
        return run(script, [target] + rest)

    if not os.path.exists(target):
        print(f'找不到文件：{target}', file=sys.stderr)
        return 1

    ext = os.path.splitext(target)[1].lower()

    if ext in READ_DIRECT:
        print(f'{target}\n\n不用这个工具包：{READ_DIRECT[ext]}', file=sys.stderr)
        return 0

    script = ROUTE.get(ext)
    if not script:
        print(f'不认识的格式 {ext or "（无扩展名）"}。\n'
              f'支持：{", ".join(sorted(ROUTE))}\n'
              f'另外 {", ".join(sorted(READ_DIRECT))} 用 Read 直接读。',
              file=sys.stderr)
        return 1

    print(f'[分派] {script}', file=sys.stderr)
    return run(script, [target] + rest)


if __name__ == '__main__':
    sys.exit(main())
