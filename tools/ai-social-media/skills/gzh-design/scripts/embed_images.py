#!/usr/bin/env python3
"""Embed local images in a WeChat HTML article as Base64 data URIs.

Remote URLs and existing data URIs are left untouched.  The output is a new
HTML file by default so the source article is never overwritten accidentally.
"""

from __future__ import annotations

import argparse
import base64
import mimetypes
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse


IMG_SRC_RE = re.compile(
    r"(<img\b[^>]*?\bsrc\s*=\s*)([\"'])(.*?)(\2)",
    flags=re.IGNORECASE | re.DOTALL,
)


def local_path(src: str, base_dir: Path) -> Path | None:
    """Resolve a local image reference; return None for remote references."""
    value = unquote(src.strip())
    parsed = urlparse(value)
    if parsed.scheme in {"http", "https", "data", "vscode-cdn"} or value.startswith("//"):
        return None
    if parsed.scheme == "file":
        value = unquote(parsed.path)
        # file:///C:/... has a leading slash that is not part of the drive.
        if re.match(r"^/[A-Za-z]:/", value):
            value = value[1:]
        if parsed.netloc:
            value = f"//{parsed.netloc}{value}"
    elif parsed.scheme:
        return None
    # Strip URL query/fragment suffixes from relative file references.
    if not parsed.scheme and (parsed.query or parsed.fragment):
        value = unquote(parsed.path)
    return Path(value) if Path(value).is_absolute() else base_dir / value


def embed_html(html: str, base_dir: Path) -> tuple[str, int, list[str]]:
    embedded = 0
    warnings: list[str] = []

    def replace(match: re.Match[str]) -> str:
        nonlocal embedded
        prefix, quote, src, closing_quote = match.groups()
        if src.lower().startswith("data:image/"):
            return match.group(0)
        path = local_path(src, base_dir)
        if path is None:
            return match.group(0)
        if not path.is_file():
            warnings.append(f"找不到本地图片，保持原引用: {src}")
            return match.group(0)
        mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        embedded += 1
        return f'{prefix}{quote}data:{mime};base64,{encoded}{closing_quote}'

    return IMG_SRC_RE.sub(replace, html), embedded, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="将公众号 HTML 中的本地图片内嵌为 Base64")
    parser.add_argument("input", type=Path, help="输入 HTML 文件")
    parser.add_argument("output", type=Path, nargs="?", help="输出 HTML 文件，默认追加 _base64")
    parser.add_argument(
        "--base-dir",
        type=Path,
        help="解析相对图片路径的基准目录，默认使用输入 HTML 所在目录",
    )
    args = parser.parse_args()

    source = args.input.expanduser().resolve()
    if not source.is_file():
        print(f"错误：找不到输入文件: {source}", file=sys.stderr)
        return 2
    output = (args.output or source.with_name(f"{source.stem}_base64{source.suffix}")).expanduser()
    base_dir = (args.base_dir or source.parent).expanduser().resolve()

    html = source.read_text(encoding="utf-8")
    result, count, warnings = embed_html(html, base_dir)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(result, encoding="utf-8", newline="")

    print(f"已内嵌 {count} 张本地图片: {output}")
    for warning in warnings:
        print(f"警告：{warning}", file=sys.stderr)
    if output.stat().st_size > 3 * 1024 * 1024:
        print("提示：输出超过 3MB，复制前建议降低图片宽度或 JPEG quality。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
