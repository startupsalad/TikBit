#!/usr/bin/env python3
"""
小红书-图文学习和分析系统
用户提供链接，使用Playwright浏览器抓取完整图文内容，下载图片，更新素材库
"""

import asyncio
import sys
import os
import re
import requests
from datetime import datetime
from playwright.async_api import async_playwright


class XiaohongshuAnalyzer:
    def __init__(self):
        self.vault_root = self._get_vault_root()
        self.material_lib = os.path.join(self.vault_root, "新媒体AI员工", "策划总监", "2️⃣热门素材库.md")
        self.image_dir = os.path.join(self.vault_root, "新媒体AI员工", "策划总监", "📦热门素材库图片")
        self.browser = None
        self.page = None

    def _get_vault_root(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.dirname(os.path.dirname(script_dir))

    async def init_browser(self):
        """初始化Playwright浏览器，使用已登录的session"""
        print("🌐 启动浏览器...")
        pw = await async_playwright().start()
        self.browser = await pw.chromium.launch_persistent_context(
            user_data_dir="/tmp/playwright-xiaohongshu",
            headless=False,
            args=['--disable-blink-features=AutomationControlled']
        )
        self.page = await self.browser.new_page()
        print("✅ 浏览器已启动")

    async def fetch_note(self, url):
        """用Playwright抓取单条笔记的完整数据"""
        print(f"📄 抓取: {url}")

        try:
            # 使用networkidle等待跳转完成，增加超时时间
            await self.page.goto(url, wait_until="networkidle", timeout=30000)
            # 额外等待页面渲染
            await asyncio.sleep(5)

            # 提取笔记数据
            data = await self.page.evaluate("""
                () => {
                    // 标题
                    const titleEl = document.querySelector('#detail-title');
                    const title = titleEl ? titleEl.textContent.trim() : '';

                    // 正文
                    const descEl = document.querySelector('#detail-desc');
                    const content = descEl ? descEl.textContent.trim() : '';

                    // 标签
                    const tags = [];
                    document.querySelectorAll('a.tag').forEach(tag => {
                        tags.push(tag.textContent.trim());
                    });

                    // 互动数据（多种选择器尝试）
                    let likes = '0', collects = '0', comments = '0';

                    // 尝试从底部互动栏获取
                    const interactItems = document.querySelectorAll('.interact-container .count, .engage-bar .count, .engage-bar-container .count');

                    // 尝试从所有包含数字的span中匹配
                    const allSpans = document.querySelectorAll('span.count, span[class*="count"]');

                    // 方法1: 通过父元素的class判断
                    document.querySelectorAll('[class*="like"] .count, [class*="like"] span').forEach(el => {
                        const text = el.textContent.trim();
                        if (text && text !== '赞' && /[\\d万千]/.test(text)) likes = text;
                    });
                    document.querySelectorAll('[class*="collect"] .count, [class*="collect"] span').forEach(el => {
                        const text = el.textContent.trim();
                        if (text && /[\\d万千]/.test(text)) collects = text;
                    });
                    document.querySelectorAll('[class*="chat"] .count, [class*="comment"] .count, [class*="chat"] span, [class*="comment"] span').forEach(el => {
                        const text = el.textContent.trim();
                        if (text && /[\\d万千]/.test(text)) comments = text;
                    });

                    // 方法2: 如果方法1没拿到，尝试从底部栏按顺序取
                    if (likes === '0' || collects === '0') {
                        const counts = [];
                        document.querySelectorAll('.engage-bar-container span, .interact-container span, [class*="engage"] span').forEach(el => {
                            const text = el.textContent.trim();
                            if (/^\d+(\.\d+)?[万千]?$/.test(text)) counts.push(text);
                        });
                        if (counts.length >= 3) {
                            likes = likes === '0' ? counts[0] : likes;
                            collects = collects === '0' ? counts[1] : collects;
                            comments = comments === '0' ? counts[2] : comments;
                        }
                    }

                    // 图片（多种选择器）
                    const images = new Set();

                    // 方法1: swiper中的图片
                    document.querySelectorAll('.swiper-slide img').forEach(img => {
                        const src = img.src || img.getAttribute('data-src') || '';
                        if (src && src.includes('xhscdn')) {
                            images.add(src.split('?')[0]);
                        }
                    });

                    // 方法2: note-image中的图片
                    document.querySelectorAll('[class*="note-image"] img').forEach(img => {
                        const src = img.src || img.getAttribute('data-src') || '';
                        if (src && src.includes('xhscdn')) {
                            images.add(src.split('?')[0]);
                        }
                    });

                    // 方法3: 所有xhscdn图片（过滤头像等小图）
                    document.querySelectorAll('img[src*="xhscdn"]').forEach(img => {
                        const src = img.src;
                        if (src && img.naturalWidth > 200) {
                            images.add(src.split('?')[0]);
                        }
                    });

                    // 作者信息
                    const authorEl = document.querySelector('.username');
                    const author = authorEl ? authorEl.textContent.trim() : '';

                    return {
                        title, content, tags,
                        likes, collects, comments,
                        images: Array.from(images),
                        author
                    };
                }
            """)

            # 如果swiper有多张图，尝试点击翻页获取所有图片
            if len(data['images']) <= 1:
                print("  🔄 尝试翻页获取更多图片...")
                for _ in range(8):
                    try:
                        await self.page.click('.swiper-button-next', timeout=1000)
                        await asyncio.sleep(0.5)
                    except:
                        break

                # 重新获取图片
                more_images = await self.page.evaluate("""
                    () => {
                        const images = new Set();
                        document.querySelectorAll('img[src*="xhscdn"]').forEach(img => {
                            const src = img.src;
                            if (src && img.naturalWidth > 200) {
                                images.add(src.split('?')[0]);
                            }
                        });
                        return Array.from(images);
                    }
                """)
                data['images'] = more_images

            print(f"  📝 标题: {data['title']}")
            print(f"  👤 作者: {data['author']}")
            print(f"  👍 {data['likes']} | ⭐ {data['collects']} | 💬 {data['comments']}")
            print(f"  🖼️ 找到 {len(data['images'])} 张图片")

            return {
                'url': url,
                'title': data['title'],
                'content': data['content'],
                'tags': data['tags'],
                'author': data['author'],
                'likes': data['likes'],
                'collects': data['collects'],
                'comments': data['comments'],
                'images': data['images'][:9],
                'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

        except Exception as e:
            print(f"❌ 抓取失败: {e}")
            return None

    def download_images(self, images, folder_name):
        """下载图片到指定文件夹"""
        folder_path = os.path.join(self.image_dir, folder_name)
        os.makedirs(folder_path, exist_ok=True)

        downloaded = []
        for i, img_url in enumerate(images, 1):
            try:
                headers = {'User-Agent': 'Mozilla/5.0'}
                resp = requests.get(img_url, headers=headers, timeout=15)
                if resp.status_code == 200 and len(resp.content) > 1000:
                    img_path = os.path.join(folder_path, f"P{i}.jpg")
                    with open(img_path, 'wb') as f:
                        f.write(resp.content)
                    downloaded.append(f"P{i}.jpg")
                    print(f"  ✓ 下载图片 {i}/{len(images)}")
                else:
                    print(f"  ✗ 图片{i}无效")
            except Exception as e:
                print(f"  ✗ 图片{i}下载失败: {e}")
        return downloaded

    def update_material_lib(self, note_data, folder_name, images):
        """更新热门素材库（表格+详细条目）"""
        date_str = datetime.now().strftime('%Y%m%d')
        entry_id = f"{date_str}-001"
        if os.path.exists(self.material_lib):
            with open(self.material_lib, 'r', encoding='utf-8') as f:
                content = f.read()
                matches = re.findall(rf'{date_str}-(\d+)', content)
                if matches:
                    last_num = max(int(m) for m in matches)
                    entry_id = f"{date_str}-{last_num+1:03d}"
        else:
            content = ''

        # 1. 更新表格：在表格最后一行后插入新行
        short_title = note_data['title'][:30]
        table_row = f"| {entry_id} | {short_title} | 小红书 | {note_data['likes']} | {note_data['collects']} | {note_data['comments']} | 未处理 |"

        if '| 处理状态 |' in content:
            # 找到表格末尾，在最后一个表格行后插入
            lines = content.split('\n')
            insert_pos = -1
            for idx, line in enumerate(lines):
                if line.startswith('|') and '处理状态' not in line and '------' not in line and '编号' not in line:
                    insert_pos = idx
            if insert_pos >= 0:
                lines.insert(insert_pos + 1, table_row)
                content = '\n'.join(lines)
                with open(self.material_lib, 'w', encoding='utf-8') as f:
                    f.write(content)

        # 2. 追加详细条目
        entry = f"\n\n## {entry_id} | {note_data['title']}\n\n"
        entry += f"**来源**：小红书 @{note_data['author']}\n"
        entry += f"**链接**：{note_data['url']}\n"
        entry += f"**抓取时间**：{note_data['crawl_time']}\n"
        entry += f"**互动数据**：👍 {note_data['likes']} | ⭐ {note_data['collects']} | 💬 {note_data['comments']}\n\n"
        entry += f"**标题**：{note_data['title']}\n\n"
        entry += f"**核心内容**：\n{note_data['content']}\n\n"
        if note_data['tags']:
            entry += f"**标签**：{' '.join(note_data['tags'])}\n\n"
        entry += f"**图片**：\n"
        entry += f"- 📁 存放位置：`新媒体AI员工/策划总监/📦热门素材库图片/{folder_name}/`\n"
        entry += f"- 🖼️ 共{len(images)}张图片\n\n"
        for img in images:
            entry += f"![[新媒体AI员工/策划总监/📦热门素材库图片/{folder_name}/{img}]]\n"

        with open(self.material_lib, 'a', encoding='utf-8') as f:
            f.write(entry)
        return entry_id

    async def process_urls(self, urls):
        """批量处理URL列表"""
        await self.init_browser()
        results = []
        try:
            for i, url in enumerate(urls, 1):
                print(f"\n{'='*50}")
                print(f"[{i}/{len(urls)}] 处理中...")
                note_data = await self.fetch_note(url)
                if not note_data:
                    continue

                date_str = datetime.now().strftime('%Y%m%d')
                entry_num = i
                if os.path.exists(self.material_lib):
                    with open(self.material_lib, 'r', encoding='utf-8') as f:
                        matches = re.findall(rf'{date_str}-(\d+)', f.read())
                        if matches:
                            entry_num = max(int(m) for m in matches) + 1
                # 文件夹名：日期-编号_标题（去掉特殊字符）
                safe_title = re.sub(r'[\\/:*?"<>|]', '', note_data['title'])[:30]
                folder_name = f"{date_str}-{entry_num:03d}_{safe_title}"

                downloaded = []
                if note_data['images']:
                    print(f"📥 下载 {len(note_data['images'])} 张图片...")
                    downloaded = self.download_images(note_data['images'], folder_name)
                else:
                    print("⚠️ 未找到图片")

                print("📝 更新素材库...")
                entry_id = self.update_material_lib(note_data, folder_name, downloaded)
                results.append({
                    'entry_id': entry_id,
                    'title': note_data['title'],
                    'images_count': len(downloaded),
                    'likes': note_data['likes'],
                    'collects': note_data['collects']
                })
                print(f"✅ 完成: {entry_id}")
        finally:
            if self.browser:
                await self.browser.close()
        return results


async def main():
    if len(sys.argv) < 2:
        print("用法: python3 小红书-图文学习和分析系统.py <URL1> [URL2] ...")
        sys.exit(1)

    urls = sys.argv[1:]
    analyzer = XiaohongshuAnalyzer()
    print(f"🚀 开始处理 {len(urls)} 条链接\n")
    results = await analyzer.process_urls(urls)

    print(f"\n{'='*50}")
    print(f"✅ 全部完成！共处理 {len(results)} 条")
    print(f"{'='*50}\n")
    for r in results:
        print(f"  {r['entry_id']} | 👍{r['likes']} ⭐{r['collects']} | {r['images_count']}张图 | {r['title']}")


if __name__ == "__main__":
    asyncio.run(main())
