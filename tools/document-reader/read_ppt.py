#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PPT 读取 —— 转成 PDF 再交给 AI 视觉读取，保住排版、图片、图表。

为什么不抽纯文字：PPT 的信息量大半在版面里（位置关系、配色、图表、分栏）。
抽成 txt 会丢掉一半意思，读出来是一堆碎词。所以默认转 PDF 视觉读。

引擎自动降级（详见 engine.py）：Microsoft Office → WPS Office → LibreOffice。
一个都没有时用 --text 兜底抽纯文字，聊胜于无。

用法：
    python read_ppt.py <PPT>                # 转 PDF（默认，最常用）
    python read_ppt.py <PPT> --png          # 再逐页导出 PNG（放大看小字）
    python read_ppt.py <PPT> --png --dpi 200
    python read_ppt.py <PPT> --pages 3,5-7  # 只导指定页的 PNG
    python read_ppt.py <PPT> --text         # 只抽纯文字（无引擎时的兜底）
    python read_ppt.py <PPT> --text --maxchars 0   # 兜底抽文字且不截断（默认截 12000）
    python read_ppt.py <PPT> --out 目标.pdf
    python read_ppt.py <PPT> --engine wps   # 指定引擎（仍会自动降级）

输出：默认落系统临时目录 docread/，不往源目录（本库在微盘实时同步）拉产物。
      要放别处用 --out。

注意：默认（转 PDF）模式只打印一个路径，本身就省 token，没有截断的事。
      只有 --text 兜底抽文字会一次吐一大坨，那条路默认截断 12000 字，
      **截断会明确告知剩多少字**，不是静默丢内容；要全文加 --maxchars 0。
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # 保证能 import engine
import engine

EXTS = ('.ppt', '.pptx', '.pptm', '.dps')  # .dps 是 WPS 演示自家格式


def parse_pages(spec):
    """把 "3,5-7" 解析成 [2,4,5,6]（转成 0 基页号）"""
    if not spec:
        return None
    out = []
    for part in spec.replace('，', ',').split(','):
        part = part.strip()
        if not part:
            continue
        if '-' in part:
            a, b = part.split('-', 1)
            out.extend(range(int(a) - 1, int(b)))
        else:
            out.append(int(part) - 1)
    return sorted(set(out))


def main():
    engine.fix_console()
    args = list(sys.argv[1:])
    want_png = engine.take_flag(args, '--png')
    want_text = engine.take_flag(args, '--text')
    maxchars = engine.take_opt(args, '--maxchars', int, 12000)
    dpi = engine.take_opt(args, '--dpi', int, 150)
    pages = parse_pages(engine.take_opt(args, '--pages'))
    out = engine.take_opt(args, '--out')
    eng = engine.take_opt(args, '--engine')

    if not args:
        print('用法: python read_ppt.py <PPT> [--png] [--dpi 150] [--pages 3,5-7] '
              '[--text] [--maxchars 12000] [--out 目标.pdf] '
              '[--engine mso|wps|soffice]')
        sys.exit(1)

    src = args[0]
    if not os.path.exists(src):
        print(f'文件不存在: {src}')
        print('排查：微盘"按需下载"的占位符读不了，先在资源管理器里双击下载到本地。')
        sys.exit(1)

    ext = os.path.splitext(src)[1].lower()
    if ext not in EXTS:
        print(f'不支持的格式: {ext}（本工具处理 {"/".join(EXTS)}）')
        sys.exit(1)

    if want_text:
        try:
            print(engine.clip(engine.markitdown_text(src), maxchars))
            return
        except Exception as exc:
            print(f'抽文字失败: {type(exc).__name__}: {exc}')
            sys.exit(1)

    try:
        pdf, used = engine.office_to_pdf(src, out=out, prefer=eng)
    except Exception as exc:
        print(f'转换失败: {exc}')
        print('\n没有任何转换引擎时，可用 --text 抽纯文字兜底（丢版面，只保内容）。')
        sys.exit(1)

    import fitz
    with fitz.open(pdf) as d:
        n = len(d)
    print(f'PDF 已生成（{n} 页，引擎 {engine.ENGINE_NAME[used]}）：\n{pdf}')
    print('→ AI 直接 Read 这个 PDF 即可视觉读取。')

    if want_png:
        try:
            d, made = engine.pdf_to_png(pdf, dpi=dpi, pages=pages)
            print(f'\nPNG 已导出 {len(made)} 张（{dpi}dpi）到：\n{d}')
        except Exception as exc:
            print(f'\nPNG 导出失败: {type(exc).__name__}: {exc}', file=sys.stderr)


if __name__ == '__main__':
    main()
