#!/usr/bin/env python3
"""
微信推文-内容获取工具

用途：抓取微信公众号文章的标题、正文、图片与元数据，保存到热门素材库详情目录
复用：网页抓取工具.py 的 requests+BeautifulSoup+html2text 管道
      小红书-图文学习和分析系统.py 的 vault 根路径推导、按日编号、图片下载与落盘、索引更新模式

使用方法：
    # 抓取单篇微信推文
    python3 "🤖新媒体AI员工/工具箱/微信推文-内容获取工具.py" "https://mp.weixin.qq.com/s/xxx"

    # 批量抓取多篇
    python3 "🤖新媒体AI员工/工具箱/微信推文-内容获取工具.py" URL1 URL2 URL3

依赖（已安装）：
    pip3 install --break-system-packages requests beautifulsoup4 html2text
"""

import argparse
import os
import re
import sys
from datetime import datetime
from urllib.parse import urljoin

import html2text
import requests
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

# ---------------------------------------------------------------------------
# Vault 路径推导（复用小红书脚本模式）
# ---------------------------------------------------------------------------

def get_vault_root():
    """从脚本位置推导 vault 根目录（脚本在 🤖新媒体AI员工/工具箱/ 下）"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(os.path.dirname(script_dir))


VAULT_ROOT = get_vault_root()
DETAIL_BASE = os.path.join(VAULT_ROOT, "🤖新媒体AI员工", "策划总监", "📦热门素材库详情")
INDEX_FILE = os.path.join(VAULT_ROOT, "🤖新媒体AI员工", "策划总监", "2️⃣热门素材库.md")
COLLECTION_FILE = os.path.join(VAULT_ROOT, "🤖新媒体AI员工", "策划总监", "1️⃣热门素材收集箱.md")


# ---------------------------------------------------------------------------
# 编号生成（复用小红书脚本的按日递增模式）
# ---------------------------------------------------------------------------

def next_entry_id(date_str: str) -> str:
    """生成当日递增编号，如 20260424-001, 20260424-002"""
    seq = 1
    if os.path.exists(INDEX_FILE):
        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            matches = re.findall(rf"{date_str}-(\d+)", f.read())
            if matches:
                seq = max(int(m) for m in matches) + 1
    # 也检查详情目录
    if os.path.isdir(DETAIL_BASE):
        for name in os.listdir(DETAIL_BASE):
            m = re.match(rf"{date_str}-(\d+)", name)
            if m:
                seq = max(seq, int(m.group(1)) + 1)
    return f"{date_str}-{seq:03d}"

# ---------------------------------------------------------------------------
# 抓取 & 解析
# ---------------------------------------------------------------------------

def fetch_raw_html(url: str, timeout: int = 20) -> str:
    """抓取原始 HTML"""
    resp = requests.get(url, headers=HEADERS, timeout=timeout)
    resp.raise_for_status()
    # 微信推文通常是 UTF-8，apparent_encoding 有时误判
    resp.encoding = "utf-8"
    return resp.text


def extract_metadata(soup: BeautifulSoup, url: str) -> dict:
    """从微信推文 HTML 提取元数据"""
    meta = {
        "url": url,
        "title": "",
        "author": "不可获取",
        "account_name": "不可获取",
        "publish_date": "不可获取",
        "crawl_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "cover_img": "",
        "metrics": {
            "阅读量": "不可获取（需登录/需Cookie）",
            "点赞量": "不可获取（需登录/需Cookie）",
            "转发量": "不可获取（需登录/需Cookie）",
            "评论量": "不可获取（需登录/需Cookie）",
        },
    }

    # 标题
    title_el = soup.find("h1", class_="rich_media_title") or soup.find("h1")
    if title_el:
        meta["title"] = title_el.get_text(strip=True)

    # 公众号名 / 作者
    account_el = soup.find("a", id="js_name") or soup.find("span", class_="rich_media_meta_nickname")
    if account_el:
        meta["account_name"] = account_el.get_text(strip=True)

    author_el = soup.find("span", class_="rich_media_meta_text")
    if author_el:
        meta["author"] = author_el.get_text(strip=True)

    # 发布日期（从 script 中提取 var ct / publish_time）
    scripts = soup.find_all("script")
    for s in scripts:
        text = s.string or ""
        m = re.search(r'var\s+ct\s*=\s*"(\d+)"', text)
        if m:
            ts = int(m.group(1))
            meta["publish_date"] = datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
            break
        m2 = re.search(r's="(\d{4}-\d{2}-\d{2})"', text)
        if m2:
            meta["publish_date"] = m2.group(1)
            break

    # 封面图（og:image）
    og = soup.find("meta", property="og:image")
    if og and og.get("content"):
        meta["cover_img"] = og["content"]

    return meta

# ---------------------------------------------------------------------------
# 图片提取 & 下载
# ---------------------------------------------------------------------------

def extract_images(soup: BeautifulSoup, base_url: str) -> list[str]:
    """提取正文中所有图片 URL（去重、保序）"""
    content_el = soup.find("div", id="js_content") or soup.find("div", class_="rich_media_content")
    if not content_el:
        return []
    seen = set()
    urls = []
    for img in content_el.find_all("img"):
        src = img.get("data-src") or img.get("src") or ""
        if not src or src in seen:
            continue
        if src.startswith("//"):
            src = "https:" + src
        elif src.startswith("/"):
            src = urljoin(base_url, src)
        # 过滤 1x1 占位图、emoji 等小图
        w = img.get("data-w") or img.get("width") or ""
        if w and w.isdigit() and int(w) < 50:
            continue
        seen.add(src)
        urls.append(src)
    return urls


def download_images(img_urls: list[str], dest_dir: str) -> list[str]:
    """下载图片到 dest_dir，返回本地文件名列表"""
    os.makedirs(dest_dir, exist_ok=True)
    downloaded = []
    for i, url in enumerate(img_urls, 1):
        try:
            resp = requests.get(url, headers={"User-Agent": HEADERS["User-Agent"]}, timeout=15)
            if resp.status_code == 200 and len(resp.content) > 500:
                ext = "jpg"
                ct = resp.headers.get("Content-Type", "")
                if "png" in ct:
                    ext = "png"
                elif "gif" in ct:
                    ext = "gif"
                elif "webp" in ct:
                    ext = "webp"
                fname = f"img_{i:02d}.{ext}"
                with open(os.path.join(dest_dir, fname), "wb") as f:
                    f.write(resp.content)
                downloaded.append(fname)
                print(f"  ✓ 图片 {i}/{len(img_urls)}")
            else:
                print(f"  ✗ 图片 {i} 无效 (status={resp.status_code})")
        except Exception as e:
            print(f"  ✗ 图片 {i} 下载失败: {e}")
    return downloaded

# ---------------------------------------------------------------------------
# 正文转 Markdown（图文混排 / 图片附录两种模式）
# ---------------------------------------------------------------------------

def content_to_markdown_mixed(soup: BeautifulSoup, img_files: list[str], detail_rel: str) -> str:
    """尝试图文混排：按 DOM 顺序输出文字和图片"""
    content_el = soup.find("div", id="js_content") or soup.find("div", class_="rich_media_content")
    if not content_el:
        return ""

    converter = html2text.HTML2Text()
    converter.ignore_links = False
    converter.ignore_images = True  # 我们手动插入图片
    converter.body_width = 0
    converter.unicode_snob = True

    # 给每张 img 打标记，方便后续替换
    img_index = 0
    for img in content_el.find_all("img"):
        src = img.get("data-src") or img.get("src") or ""
        w = img.get("data-w") or img.get("width") or ""
        if w and w.isdigit() and int(w) < 50:
            continue
        if src and img_index < len(img_files):
            img.replace_with(f"__IMG_PLACEHOLDER_{img_index}__")
            img_index += 1

    md = converter.handle(str(content_el)).strip()

    # 替换占位符为 wikilink 图片嵌入
    for i, fname in enumerate(img_files):
        placeholder = f"__IMG_PLACEHOLDER_{i}__"
        embed = f"\n\n![[{detail_rel}/images/{fname}]]\n\n"
        md = md.replace(placeholder, embed)

    return md


def content_to_markdown_appendix(soup: BeautifulSoup, img_files: list[str], detail_rel: str) -> str:
    """退回模式：正文纯文字 + 末尾图片附录"""
    content_el = soup.find("div", id="js_content") or soup.find("div", class_="rich_media_content")
    if not content_el:
        return ""

    converter = html2text.HTML2Text()
    converter.ignore_links = False
    converter.ignore_images = True
    converter.body_width = 0
    converter.unicode_snob = True

    md = converter.handle(str(content_el)).strip()

    if img_files:
        md += "\n\n---\n\n## 图片附录\n\n"
        for fname in img_files:
            md += f"![[{detail_rel}/images/{fname}]]\n\n"

    return md

# ---------------------------------------------------------------------------
# 保存详情目录 & 更新索引
# ---------------------------------------------------------------------------

def save_detail(entry_id: str, meta: dict, body_md: str, img_files: list[str]) -> str:
    """保存到 📦热门素材库详情/YYYYMMDD-编号_标题/ 目录，返回目录相对路径"""
    safe_title = re.sub(r'[\\/:*?"<>|]', '', meta["title"])[:40]
    folder_name = f"{entry_id}_{safe_title}"
    detail_dir = os.path.join(DETAIL_BASE, folder_name)
    os.makedirs(detail_dir, exist_ok=True)

    # 原文.md（含 frontmatter）
    fm = (
        f"---\n"
        f"title: \"{meta['title']}\"\n"
        f"account: \"{meta['account_name']}\"\n"
        f"author: \"{meta['author']}\"\n"
        f"publish_date: \"{meta['publish_date']}\"\n"
        f"crawl_time: \"{meta['crawl_time']}\"\n"
        f"url: \"{meta['url']}\"\n"
        f"entry_id: \"{entry_id}\"\n"
        f"阅读量: \"{meta['metrics']['阅读量']}\"\n"
        f"点赞量: \"{meta['metrics']['点赞量']}\"\n"
        f"转发量: \"{meta['metrics']['转发量']}\"\n"
        f"评论量: \"{meta['metrics']['评论量']}\"\n"
        f"---\n\n"
    )
    with open(os.path.join(detail_dir, "原文.md"), "w", encoding="utf-8") as f:
        f.write(fm + body_md)

    # 图片目录（已由 download_images 创建）
    img_dir = os.path.join(detail_dir, "images")
    os.makedirs(img_dir, exist_ok=True)

    # 返回 vault 内相对路径
    return os.path.relpath(detail_dir, VAULT_ROOT)


def update_index(entry_id: str, meta: dict, detail_rel: str):
    """更新 2️⃣热门素材库.md 索引表格"""
    short_title = meta["title"][:30]
    metrics_avail = "部分可用" if meta["publish_date"] != "不可获取" else "仅基础"

    new_row = (
        f"| {entry_id} | {short_title} | 微信公众号 | "
        f"{meta['account_name']} | {meta['publish_date']} | "
        f"✅已抓取 | 待分析 | — | {metrics_avail} | "
        f"[[{detail_rel}/原文.md\\|详情]] |"
    )

    if not os.path.exists(INDEX_FILE):
        print(f"  ⚠️ 索引文件不存在: {INDEX_FILE}")
        return

    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    # 在表格最后一行后插入
    lines = content.split("\n")
    insert_pos = -1
    for idx, line in enumerate(lines):
        if line.startswith("|") and "编号" not in line and "------" not in line and "状态说明" not in line:
            insert_pos = idx
    if insert_pos >= 0:
        lines.insert(insert_pos + 1, new_row)
    else:
        lines.append(new_row)

    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

def process_one(url: str) -> dict | None:
    """处理单篇微信推文，返回结果摘要"""
    print(f"\n📄 抓取: {url}")

    # 1. 抓取
    try:
        raw_html = fetch_raw_html(url)
    except Exception as e:
        print(f"  ❌ 抓取失败: {e}")
        return None

    soup = BeautifulSoup(raw_html, "html.parser")

    # 2. 提取元数据
    meta = extract_metadata(soup, url)
    print(f"  📝 标题: {meta['title']}")
    print(f"  👤 公众号: {meta['account_name']} | 作者: {meta['author']}")
    print(f"  📅 发布日期: {meta['publish_date']}")

    # 3. 生成编号
    date_str = datetime.now().strftime("%Y%m%d")
    entry_id = next_entry_id(date_str)

    # 4. 提取 & 下载图片
    img_urls = extract_images(soup, url)
    print(f"  🖼️ 发现 {len(img_urls)} 张图片")

    safe_title = re.sub(r'[\\/:*?"<>|]', '', meta["title"])[:40]
    folder_name = f"{entry_id}_{safe_title}"
    img_dest = os.path.join(DETAIL_BASE, folder_name, "images")
    img_files = download_images(img_urls, img_dest) if img_urls else []

    # 封面图单独下载
    if meta["cover_img"]:
        try:
            resp = requests.get(meta["cover_img"], headers={"User-Agent": HEADERS["User-Agent"]}, timeout=15)
            if resp.status_code == 200:
                cover_path = os.path.join(DETAIL_BASE, folder_name, "images", "cover.jpg")
                os.makedirs(os.path.dirname(cover_path), exist_ok=True)
                with open(cover_path, "wb") as f:
                    f.write(resp.content)
                print("  ✓ 封面图已下载")
        except Exception:
            pass

    # 5. 正文转 Markdown
    detail_rel = f"🤖新媒体AI员工/策划总监/📦热门素材库详情/{folder_name}"
    try:
        body_md = content_to_markdown_mixed(soup, img_files, detail_rel)
        if not body_md.strip():
            raise ValueError("混排结果为空")
        print("  ✓ 正文已转换（图文混排模式）")
    except Exception:
        body_md = content_to_markdown_appendix(soup, img_files, detail_rel)
        print("  ⚠️ 混排失败，已退回图片附录模式")

    # 6. 保存详情目录
    detail_rel_actual = save_detail(entry_id, meta, body_md, img_files)

    # 7. 更新索引
    update_index(entry_id, meta, detail_rel_actual)
    print(f"  ✅ 完成: {entry_id}")

    return {
        "entry_id": entry_id,
        "title": meta["title"],
        "account": meta["account_name"],
        "images_count": len(img_files),
        "detail_path": detail_rel_actual,
    }


def main():
    parser = argparse.ArgumentParser(description="微信推文-内容获取工具")
    parser.add_argument("urls", nargs="+", help="微信推文链接（1个或多个）")
    parser.add_argument("--timeout", type=int, default=20, help="请求超时秒数")
    args = parser.parse_args()

    print(f"🚀 开始处理 {len(args.urls)} 篇微信推文\n")
    results = []
    for url in args.urls:
        r = process_one(url)
        if r:
            results.append(r)

    print(f"\n{'='*50}")
    print(f"✅ 全部完成！成功 {len(results)}/{len(args.urls)} 篇")
    print(f"{'='*50}\n")
    for r in results:
        print(f"  {r['entry_id']} | {r['account']} | {r['images_count']}张图 | {r['title']}")
        print(f"    📁 {r['detail_path']}")


if __name__ == "__main__":
    main()
