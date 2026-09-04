#!/usr/bin/env python3.12
"""
小红书内容抓取与分析脚本
基于"新媒体内容生产线"课程的目标群体

功能：
1. 抓取小红书探索页面热门内容
2. 解析笔记标题、作者、点赞数
3. 抓取单个笔记详细内容
4. 可选：截图保存

使用方法：
  python3.12 小红书受众分析.py              # 抓取探索页
  python3.12 小红书受众分析.py --screenshot  # 抓取+截图
  python3.12 小红书受众分析.py --note URL    # 抓取单个笔记
"""

import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
import json
import re
import os
from datetime import datetime

# 输出目录（脚本所在目录）
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def parse_notes_from_markdown(markdown):
    """从 markdown 中解析笔记信息

    小红书探索页的 markdown 结构（每个笔记3行）：
    第1行：[](笔记链接)[![](封面图)](笔记链接)
    第2行：标题文本
    第3行：[![](头像) 作者名](作者链接)点赞数
    """
    lines = markdown.split('\n')
    notes = []

    for i in range(len(lines) - 2):
        # 第1行：笔记链接
        link_match = re.search(
            r'\(https://www\.xiaohongshu\.com/explore/([a-f0-9]+)',
            lines[i]
        )
        if not link_match:
            continue

        note_id = link_match.group(1)

        # 第2行：标题（纯文本行，不以 [ 或 http 开头）
        title = lines[i+1].strip()
        if not title or title.startswith('[') or title.startswith('http') or len(title) < 3:
            continue

        # 第3行：作者 + 点赞数
        author_match = re.search(
            r'\]\s*([^\]]+)\]\(https://www\.xiaohongshu\.com/user/',
            lines[i+2]
        )
        likes_match = re.search(r'\)(\d+\.?\d*[万千]?)\s*$', lines[i+2])

        author = author_match.group(1).strip() if author_match else "未知"
        likes_raw = likes_match.group(1) if likes_match else "0"

        # 转换点赞数为数字
        likes_num = 0
        if '万' in likes_raw:
            likes_num = float(likes_raw.replace('万', '')) * 10000
        elif '千' in likes_raw:
            likes_num = float(likes_raw.replace('千', '')) * 1000
        else:
            try:
                likes_num = float(likes_raw)
            except:
                likes_num = 0

        notes.append({
            "title": title,
            "author": author,
            "likes_raw": likes_raw,
            "likes_num": int(likes_num),
            "note_id": note_id,
            "url": f"https://www.xiaohongshu.com/explore/{note_id}"
        })

    return notes


async def fetch_explore_page(take_screenshot=False):
    """抓取小红书探索页面"""
    url = 'https://www.xiaohongshu.com/explore'
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    print(f"{'='*60}")
    print(f"小红书探索页面抓取")
    print(f"时间: {timestamp}")
    print(f"{'='*60}\n")

    config = CrawlerRunConfig(
        screenshot=take_screenshot,
        wait_until="networkidle"
    )

    async with AsyncWebCrawler(verbose=False) as crawler:
        result = await crawler.arun(url, config=config)

        print(f"状态码: {result.status_code}")
        print(f"Markdown 长度: {len(result.markdown)} 字符\n")

        # 解析笔记
        notes = parse_notes_from_markdown(result.markdown)

        # 按点赞数排序
        notes.sort(key=lambda x: x['likes_num'], reverse=True)

        # 显示结果
        print(f"🔥 找到 {len(notes)} 个热门笔记（按点赞数排序）\n")
        for i, note in enumerate(notes, 1):
            print(f"{i:2d}. 【{note['likes_raw']:>6s}赞】{note['title']}")
            print(f"    作者: {note['author']}")
            print(f"    链接: {note['url']}\n")

        # 保存 JSON
        json_file = os.path.join(SCRIPT_DIR, f"xiaohongshu_explore_{timestamp}.json")
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump({
                "timestamp": timestamp,
                "source": url,
                "total_notes": len(notes),
                "notes": notes
            }, f, ensure_ascii=False, indent=2)
        print(f"✅ 数据已保存: {json_file}")

        # 保存 Markdown
        md_file = os.path.join(SCRIPT_DIR, f"xiaohongshu_explore_{timestamp}.md")
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(f"# 小红书探索页热门笔记\n\n")
            f.write(f"**抓取时间**: {timestamp}\n\n")
            f.write(f"| 排名 | 点赞 | 标题 | 作者 |\n")
            f.write(f"|------|------|------|------|\n")
            for i, note in enumerate(notes, 1):
                f.write(f"| {i} | {note['likes_raw']} | [{note['title']}]({note['url']}) | {note['author']} |\n")
        print(f"✅ 表格已保存: {md_file}")

        # 保存截图
        if take_screenshot and result.screenshot:
            import base64
            screenshot_file = os.path.join(SCRIPT_DIR, f"xiaohongshu_explore_{timestamp}.png")
            with open(screenshot_file, 'wb') as f:
                f.write(base64.b64decode(result.screenshot))
            print(f"✅ 截图已保存: {screenshot_file}")

        return notes


async def fetch_single_note(note_url, take_screenshot=False):
    """抓取单个笔记的详细内容"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    print(f"正在抓取笔记: {note_url}\n")

    config = CrawlerRunConfig(
        screenshot=take_screenshot,
        wait_until="networkidle"
    )

    async with AsyncWebCrawler(verbose=False) as crawler:
        result = await crawler.arun(note_url, config=config)

        print(f"状态码: {result.status_code}")
        print(f"Markdown 长度: {len(result.markdown)} 字符\n")
        print(f"内容预览:\n{result.markdown[:1000]}\n")

        # 提取 note_id
        note_id = re.search(r'/explore/([a-f0-9]+)', note_url)
        note_id = note_id.group(1) if note_id else "unknown"

        # 保存
        md_file = os.path.join(SCRIPT_DIR, f"xiaohongshu_note_{note_id}_{timestamp}.md")
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(f"# 小红书笔记详情\n\n")
            f.write(f"**链接**: {note_url}\n")
            f.write(f"**抓取时间**: {timestamp}\n\n---\n\n")
            f.write(result.markdown)
        print(f"✅ 笔记内容已保存: {md_file}")

        if take_screenshot and result.screenshot:
            import base64
            screenshot_file = os.path.join(SCRIPT_DIR, f"xiaohongshu_note_{note_id}_{timestamp}.png")
            with open(screenshot_file, 'wb') as f:
                f.write(base64.b64decode(result.screenshot))
            print(f"✅ 截图已保存: {screenshot_file}")


async def main():
    import sys

    take_screenshot = '--screenshot' in sys.argv

    if '--note' in sys.argv:
        # 抓取单个笔记
        note_idx = sys.argv.index('--note')
        if note_idx + 1 < len(sys.argv):
            await fetch_single_note(sys.argv[note_idx + 1], take_screenshot)
        else:
            print("请提供笔记URL: --note URL")
    else:
        # 抓取探索页
        await fetch_explore_page(take_screenshot)


if __name__ == '__main__':
    asyncio.run(main())
