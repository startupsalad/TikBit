#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
图片预处理 —— 只干一件事：把 AI 读不了的图，变成读得了的图。

AI 本来就能直接看图（Read 工具），所以这个脚本不解析内容、不做 OCR，只补三个短板：

    1. 太大读不了    手机随手拍动辄 4000×3000、十几 MB，超读取上限直接被拒。
                     按长边压到 1568px（再大对识别没增益）。
    2. 格式不认识    iPhone 的 .heic、扫描件 .tiff、老 .bmp 一律不认，转成 PNG/JPEG。
    3. 长条图糊成线  手机端切图、长海报常见 960×41644 这种 43:1 比例。按长边压到
                     1568 会把宽度压成 36px —— 实测过，纯废图，什么都读不出来。
                     所以极端比例改成：保住宽度，沿长轴切片，每片带重叠避免切断文字。

用法：
    python read_img.py <图片>               # 该处理才处理，不需要就原样返回
    python read_img.py *.heic               # 可以跟多个
    python read_img.py <图片> --maxpx 2400  # 自定长边/切片上限（要看小字时调大）
    python read_img.py <图片> --no-slice    # 长图也别切，强行压（一般不用）
    python read_img.py <图片> --force       # 强制重新生成

输出：打印处理后的图片路径（默认落系统临时目录 docread/，不污染源目录），
      AI 拿这些路径去 Read 即可。长图会打印多行，按顺序读。

依赖：Pillow。.heic 另需 pillow-heif（pip install pillow-heif）。
"""

import os
import sys

MAX_PX = 1568           # 长边上限。Claude 视觉侧性价比分辨率，再高只涨体积不涨识别率
MAX_BYTES = 4_000_000   # 单图体积上限，超了必须压
STRIP_RATIO = 2.5       # 长宽比超这个就算"长条图"，走切片而不是压缩
SLICE_W = 1400          # 长条图的目标宽度（只缩不放，原图更窄就保持原宽）
OVERLAP = 80            # 切片重叠像素，防止正好切在文字行中间
MAX_SLICES = 40         # 切片数量上限，超了只出前 N 片并提示
OK_EXT = {'.png', '.jpg', '.jpeg', '.gif', '.webp'}  # Read 能直接吃的格式

def fix_console():
    """Windows 控制台默认 GBK，遇到 emoji / 生僻字会 UnicodeEncodeError"""
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            pass


def tmp_dir():
    """中间产物统一落系统临时目录，别往源目录（本库在微盘实时同步）拉屎"""
    import tempfile
    d = os.path.join(tempfile.gettempdir(), 'docread')
    os.makedirs(d, exist_ok=True)
    return d


def stem(path):
    """出文件名前缀，带上原扩展名。
    否则 图.bmp 和 图.tif 都出 图_read.jpg，后转的静默盖掉前一个。"""
    base, ext = os.path.splitext(os.path.basename(path))
    tag = ext.lstrip('.').lower()
    return f'{base}_{tag}' if tag else base


def _open(path):
    """统一开图入口：注册 heic 解码器 + 放开 PIL 的"解压炸弹"阈值（长图像素数极大）"""
    from PIL import Image
    Image.MAX_IMAGE_PIXELS = 500_000_000  # 默认约 8900 万，41644px 长图会触发告警
    if os.path.splitext(path)[1].lower() in ('.heic', '.heif'):
        try:
            import pillow_heif
            pillow_heif.register_heif_opener()
        except ImportError:
            raise RuntimeError('读 .heic 需要装 pillow-heif：pip install pillow-heif')
    return Image.open(path)


def _flatten(im):
    """转成能存 JPEG/PNG 的模式，有透明通道的保住透明"""
    alpha = im.mode in ('RGBA', 'LA') or (im.mode == 'P' and 'transparency' in im.info)
    return im.convert('RGBA' if alpha else 'RGB'), alpha


def _save(im, dst, alpha):
    """带透明的存 PNG，其余存 JPEG（体积小得多）"""
    if alpha:
        im.save(dst, 'PNG', optimize=True)
    else:
        im.save(dst, 'JPEG', quality=88, optimize=True)
    return dst


def slice_strip(path, width=SLICE_W, overlap=OVERLAP, maxn=MAX_SLICES, tile=MAX_PX):
    """
    长条图沿长轴切片 —— 保住短边不糊，每片带重叠避免正好切断文字行。
    返回 (片路径列表, 说明)。竖长条横切，横长条（条幅）竖切。
    """
    from PIL import Image
    with _open(path) as im:
        ow, oh = im.size          # 原始尺寸，出 with 后还要用来写说明
        w, h = ow, oh
        vertical = h >= w
        im2, alpha = _flatten(im)
        short = w if vertical else h
        if short > width:                      # 只缩不放，原图更窄就保持原宽
            r = width / short
            w, h = max(1, int(w * r)), max(1, int(h * r))
            im2 = im2.resize((w, h), Image.LANCZOS)

        long_px = h if vertical else w
        step = max(1, tile - overlap)
        n = max(1, -(-(long_px - overlap) // step))   # 向上取整
        cut = min(n, maxn)

        base = stem(path)
        ext = '.png' if alpha else '.jpg'
        made = []
        for i in range(cut):
            a = i * step
            b = min(a + tile, long_px)
            box = (0, a, w, b) if vertical else (a, 0, b, h)
            dst = os.path.join(tmp_dir(), f'{base}_s{i + 1:02d}{ext}')
            made.append(_save(im2.crop(box), dst, alpha))
            if b >= long_px:
                break

    keep = w if vertical else h    # 保住的那条边：竖长条保宽、横长条保高
    why = (f'长条图 {ow}×{oh}（比例 {max(ow, oh) / min(ow, oh):.0f}:1）压长边会糊成线，'
           f'改按{"横" if vertical else "竖"}向切 {len(made)} 片'
           f'（{"宽" if vertical else "高"} {keep}px，每片 {tile}px，重叠 {overlap}px）')
    if n > maxn:
        why += f'；原需 {n} 片已截到 {maxn}，要看后段加 --maxpx 调大切片高度'
    return made, why


def prepare(path, maxpx=MAX_PX, force=False, no_slice=False, out=None):
    """
    返回 (可读路径列表, 说明)。不需要处理时原样返回源路径，避免白转一遍。
    长条图返回多片，其余返回单张。
    """
    from PIL import Image
    ext = os.path.splitext(path)[1].lower()
    size = os.path.getsize(path)

    with _open(path) as im:
        w, h = im.size
        ratio = max(w, h) / max(1, min(w, h))
        # 长条图交给 slice_strip，这里先判定，出了 with 再调（避免重复持有句柄）
        if (not no_slice) and ratio > STRIP_RATIO and max(w, h) > maxpx:
            strip = True
        else:
            strip = False
            need = force or ext not in OK_EXT or max(w, h) > maxpx or size > MAX_BYTES
            if not need:
                return [path], f'{w}×{h} {size // 1024}KB 直接可读，未处理'
            im2, alpha = _flatten(im)
            if max(w, h) > maxpx:
                r = maxpx / max(w, h)
                im2 = im2.resize((max(1, int(w * r)), max(1, int(h * r))), Image.LANCZOS)
            dst = out or os.path.join(tmp_dir(),
                                      stem(path) + '_read' + ('.png' if alpha else '.jpg'))
            _save(im2, dst, alpha)
            nw, nh = im2.size

    if strip:
        return slice_strip(path, tile=maxpx)

    why = []
    if ext not in OK_EXT:
        why.append(f'{ext} 格式不支持')
    if max(w, h) > maxpx:
        why.append(f'{w}×{h} 超长边 {maxpx}')
    if size > MAX_BYTES:
        why.append(f'{size // 1024 // 1024}MB 超体积上限')
    return [dst], (f"{'、'.join(why) or '强制重转'} → {nw}×{nh} "
                   f"{os.path.getsize(dst) // 1024}KB")


def main():
    fix_console()
    args = list(sys.argv[1:])
    force = '--force' in args
    no_slice = '--no-slice' in args
    args = [a for a in args if a not in ('--force', '--no-slice')]
    maxpx = MAX_PX
    if '--maxpx' in args:
        i = args.index('--maxpx')
        maxpx = int(args[i + 1])
        del args[i:i + 2]
    out = None
    if '--out' in args:
        i = args.index('--out')
        del args[i]
        if i < len(args) and not args[i].startswith('--'):
            out = args.pop(i)

    if not args:
        print('用法: python read_img.py <图片…> [--maxpx 1568] [--no-slice] [--force]')
        sys.exit(1)

    fail = 0
    for p in args:
        if not os.path.exists(p):
            print(f'[跳过] 文件不存在: {p}', file=sys.stderr)
            fail += 1
            continue
        try:
            paths, why = prepare(p, maxpx, force, no_slice,
                                 out if len(args) == 1 else None)
            print(f'# {os.path.basename(p)} —— {why}')
            for q in paths:
                print(q)
        except Exception as exc:
            print(f'[失败] {p}: {type(exc).__name__}: {exc}', file=sys.stderr)
            fail += 1
    sys.exit(1 if fail and fail == len(args) else 0)


if __name__ == '__main__':
    main()
