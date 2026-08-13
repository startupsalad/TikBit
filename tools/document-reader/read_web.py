#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""read_web.py — 抓网页正文（AI 内置联网抓取不可用时的替代方案）

三层自动降级：
  1. 本机 curl 抓原始 HTML（快）
  2. 检测是否前端渲染空壳（正文过薄）
  3. 是空壳则改用无头 Chrome 渲染后导出 DOM

用法：
  python read_web.py <url> [<url2> ...]
  python read_web.py <url> --render        # 强制渲染（明知是 SPA 时省一次 curl）
  python read_web.py <url> --no-render     # 只用 curl，不回退渲染
  python read_web.py <url> --raw           # 输出 HTML 源码，不抽正文
  python read_web.py <url> --links         # 附带页面链接清单
  python read_web.py <url> --limit 5000    # 正文截断字数
  python read_web.py <url> --out page.txt  # 写文件（默认只打到 stdout，不落文件）
"""
from __future__ import annotations

import argparse
import html as html_mod
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

SPA_TEXT_FLOOR = 500       # 正文少于这么多字 → 疑似前端渲染空壳
RENDER_BUDGET_MS = 9000    # Chrome 等前端渲染完成的虚拟时间预算

CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
]

def fix_console() -> None:
    """Windows 控制台默认 GBK，遇到 emoji / 生僻字会 UnicodeEncodeError。"""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def find_chrome() -> str | None:
    for name in ("chrome", "msedge", "chromium"):
        found = shutil.which(name)
        if found:
            return found
    for path in CHROME_CANDIDATES:
        if Path(path).is_file():
            return path
    return None


def fetch_curl(url: str, timeout: int = 25) -> str:
    """用本机 curl 抓原始 HTML。返回空串表示失败。"""
    cmd = ["curl", "-sSL", "--compressed", "--max-time", str(timeout),
           "-A", UA, url]
    try:
        res = subprocess.run(cmd, capture_output=True, timeout=timeout + 8)
    except (OSError, subprocess.TimeoutExpired) as exc:
        print(f"[warn] curl 失败：{exc}", file=sys.stderr)
        return ""
    if res.returncode != 0:
        err = res.stderr.decode("utf-8", "replace").strip()
        print(f"[warn] curl 退出码 {res.returncode}：{err}", file=sys.stderr)
        return ""
    return decode_bytes(res.stdout)


def decode_bytes(raw: bytes) -> str:
    """按 meta charset 猜编码，默认 UTF-8。"""
    head = raw[:4096].decode("ascii", "replace").lower()
    m = re.search(r'charset=["\']?\s*([\w-]+)', head)
    if m:
        enc = m.group(1)
        if enc not in ("utf-8", "utf8"):
            try:
                return raw.decode(enc, "replace")
            except LookupError:
                pass
    return raw.decode("utf-8", "replace")


def fetch_rendered(url: str, chrome: str) -> str:
    """无头 Chrome 渲染后导出 DOM。SPA 站点必走这条。"""
    tmpdir = tempfile.mkdtemp(prefix="readweb_")
    cmd = [
        chrome, "--headless=new", "--disable-gpu", "--no-sandbox",
        "--hide-scrollbars", "--mute-audio", "--no-first-run",
        "--disable-extensions", "--disable-dev-shm-usage",
        f"--user-data-dir={tmpdir}",
        f"--virtual-time-budget={RENDER_BUDGET_MS}",
        "--dump-dom", url,
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, timeout=90)
        return decode_bytes(res.stdout)
    except (OSError, subprocess.TimeoutExpired) as exc:
        print(f"[warn] 渲染失败：{exc}", file=sys.stderr)
        return ""
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def meta_info(raw_html: str) -> list[str]:
    """抽 title / description / og:title —— SPA 空壳也有，常含真实定位文案。"""
    out = []
    m = re.search(r"(?is)<title[^>]*>(.*?)</title>", raw_html)
    if m:
        out.append("标题：" + clean_inline(m.group(1)))
    for key in ("description", "og:description", "og:title"):
        attr = "property" if key.startswith("og:") else "name"
        pat = (rf'(?is)<meta[^>]+{attr}=["\']{re.escape(key)}["\']'
               rf'[^>]+content=["\'](.*?)["\']')
        m = re.search(pat, raw_html)
        if m:
            out.append(f"{key}：" + clean_inline(m.group(1)))
    return out


def clean_inline(text: str) -> str:
    return re.sub(r"\s+", " ", html_mod.unescape(text)).strip()


def extract_text(raw_html: str, keep_dupes: bool = False) -> str:
    """HTML → 纯文本正文。"""
    s = re.sub(r"(?is)<(script|style|noscript|svg|template)\b.*?</\1>", " ", raw_html)
    s = re.sub(r"(?is)<!--.*?-->", " ", s)
    # 块级标签转换行，保住段落结构
    s = re.sub(r"(?is)<br\s*/?>", "\n", s)
    s = re.sub(r"(?is)</(p|div|li|h[1-6]|section|article|tr|td|th|"
               r"header|footer|nav|blockquote|figcaption)>", "\n", s)
    s = re.sub(r"(?s)<[^>]+>", " ", s)
    s = html_mod.unescape(s)

    lines, seen = [], set()
    for line in s.split("\n"):
        #   不换行空格、　 全角空格
        line = re.sub(r"[ \t 　]+", " ", line).strip()
        if not line:
            continue
        # 短行去重（导航/按钮反复出现），长行保留避免误删正文
        if not keep_dupes and len(line) < 80:
            if line in seen:
                continue
            seen.add(line)
        lines.append(line)
    return "\n".join(lines)


def link_label(inner_html: str, maxlen: int = 70) -> str:
    """<a> 里可能整块套着 div/svg，必须先剥标签，否则"链接文字"会是一堆 HTML。"""
    s = re.sub(r"(?is)<(script|style|svg)\b.*?</\1>", " ", inner_html)
    alts = re.findall(r'(?is)<img[^>]+alt=["\']([^"\']+)["\']', s)  # 图片链接兜底
    s = clean_inline(re.sub(r"(?s)<[^>]+>", " ", s))
    if not s and alts:
        s = clean_inline(alts[0])
    return s[:maxlen].rstrip() + "…" if len(s) > maxlen else s


def extract_links(raw_html: str, base_url: str, limit: int = 60) -> list[str]:
    from urllib.parse import urljoin
    out, seen = [], set()
    for m in re.finditer(r'(?is)<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',
                         raw_html):
        href, label = m.group(1).strip(), link_label(m.group(2))
        if href.startswith(("#", "javascript:", "mailto:", "tel:")):
            continue
        full = urljoin(base_url, href)
        if full in seen:
            continue
        seen.add(full)
        out.append(f"- {label or '(无文字)'} → {full}")
        if len(out) >= limit:
            break
    return out


def process_url(url: str, args, chrome: str | None) -> str:
    raw, text, used = "", "", "—"
    if not args.render:
        raw = fetch_curl(url)
        text = extract_text(raw, args.keep_dupes) if raw else ""
        used = "curl"

    # 正文过薄 → 疑似 SPA 空壳，回退渲染
    if (args.render or len(text) < SPA_TEXT_FLOOR) and not args.no_render:
        if chrome:
            rendered = fetch_rendered(url, chrome)
            rtext = extract_text(rendered, args.keep_dupes)
            if len(rtext) > len(text):
                raw, text, used = rendered, rtext, "无头Chrome渲染"
        elif args.render:
            print("[warn] 没找到 Chrome/Edge，无法渲染", file=sys.stderr)

    head = [f"=== {url} ===", f"抓取方式：{used} · 正文 {len(text)} 字"]
    head += meta_info(raw)
    body = raw if args.raw else text
    if args.limit and len(body) > args.limit:
        body = body[:args.limit] + f"\n…（已截断，全文 {len(body)} 字，加 --limit 0 看全）"
    parts = head + ["", body]
    if args.links:
        parts += ["", "--- 页面链接 ---"] + extract_links(raw, url)
    return "\n".join(parts)


def main() -> int:
    fix_console()
    ap = argparse.ArgumentParser(
        description="抓网页正文（curl → 检测空壳 → 无头 Chrome 渲染，自动降级）")
    ap.add_argument("urls", nargs="+", help="一个或多个网址")
    ap.add_argument("--render", action="store_true", help="强制渲染，跳过 curl")
    ap.add_argument("--no-render", action="store_true", help="只用 curl，不回退渲染")
    ap.add_argument("--raw", action="store_true", help="输出 HTML 源码，不抽正文")
    ap.add_argument("--links", action="store_true", help="附带页面链接清单")
    ap.add_argument("--keep-dupes", action="store_true", help="不去重复短行")
    ap.add_argument("--limit", type=int, default=12000,
                    help="正文截断字数，0 = 不截断（默认 12000）")
    ap.add_argument("--out", help="写入文件（默认只打到 stdout，不落文件）")
    args = ap.parse_args()

    chrome = None if args.no_render else find_chrome()
    blocks = [process_url(u, args, chrome) for u in args.urls]
    result = "\n\n".join(blocks)

    if args.out:
        Path(args.out).write_text(result, encoding="utf-8")
        print(f"[已写入] {args.out}（{len(result)} 字）")
    else:
        print(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
