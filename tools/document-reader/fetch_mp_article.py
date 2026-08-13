#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信公众号文章内容提取工具
绕过企业网络拦截，提取正文 HTML 结构
"""

import sys
import re
import urllib.request
import urllib.error
import gzip
from html import unescape

def fetch_mp_article(url):
    """
    从微信公众号 URL 提取文章正文内容

    Args:
        url: 微信公众号文章 URL (https://mp.weixin.qq.com/s/...)

    Returns:
        提取的 HTML 内容（成功）或 None（失败）
    """

    # 验证 URL 格式
    if not url.startswith('https://mp.weixin.qq.com/s/'):
        print("❌ 错误：不是有效的微信公众号文章链接", file=sys.stderr)
        print("   链接应以 https://mp.weixin.qq.com/s/ 开头", file=sys.stderr)
        return None

    try:
        # 设置请求头，模拟浏览器访问
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }

        # 发送请求
        req = urllib.request.Request(url, headers=headers)

        with urllib.request.urlopen(req, timeout=30) as response:
            # 读取响应内容
            content = response.read()

            # 检查是否 gzip 压缩（magic number: 0x1f 0x8b）
            if content[:2] == b'\x1f\x8b':
                print(f"DEBUG: Content is gzipped, decompressing...", file=sys.stderr)
                content = gzip.decompress(content)

            # 尝试多种编码方式解码
            html = None
            for encoding in ['utf-8', 'gbk', 'gb2312']:
                try:
                    html = content.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue

            if html is None:
                print("ERROR: Cannot decode page content", file=sys.stderr)
                return None

            # 检查是否需要验证（更精确的检测）
            if 'captcha' in html.lower() or '验证码' in html or '人机验证' in html:
                print("WARNING: Captcha detected, please retry later", file=sys.stderr)
                return None

            # 提取文章标题
            title_match = re.search(r'<h1[^>]*class="rich_media_title"[^>]*>(.*?)</h1>', html, re.DOTALL)
            if not title_match:
                title_match = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.DOTALL)

            # 提取文章正文内容区域
            content_match = re.search(r'<div[^>]*class="rich_media_content[^"]*"[^>]*>(.*?)</div>\s*<script', html, re.DOTALL)

            if not content_match:
                print("❌ 错误：无法找到文章正文内容", file=sys.stderr)
                print("   可能原因：1) 文章已删除 2) 需要关注后查看 3) 页面结构变化", file=sys.stderr)
                return None

            # 组合标题和正文
            result_parts = []

            if title_match:
                title = title_match.group(1).strip()
                title = re.sub(r'<[^>]+>', '', title)  # 移除标签
                title = unescape(title)  # 解码 HTML 实体
                result_parts.append(f'<h1>{title}</h1>\n')

            content_html = content_match.group(1)

            # 清理不必要的属性，保留基础结构
            # 移除 style 属性（保留标签）
            content_html = re.sub(r'\s+style="[^"]*"', '', content_html)
            # 移除 class 属性
            content_html = re.sub(r'\s+class="[^"]*"', '', content_html)
            # 移除 data-* 属性
            content_html = re.sub(r'\s+data-[^=]*="[^"]*"', '', content_html)
            # 移除空的属性
            content_html = re.sub(r'\s+(?:id|name)=""', '', content_html)

            # 解码 HTML 实体
            content_html = unescape(content_html)

            # 规范化标签（移除多余空格）
            content_html = re.sub(r'<(\w+)\s+>', r'<\1>', content_html)

            result_parts.append(content_html)

            result = '\n'.join(result_parts)

            print("✅ 文章内容提取成功", file=sys.stderr)
            return result

    except urllib.error.HTTPError as e:
        print(f"❌ HTTP 错误 {e.code}: {e.reason}", file=sys.stderr)
        if e.code == 403:
            print("   可能原因：访问被拒绝，尝试更换网络环境", file=sys.stderr)
        elif e.code == 404:
            print("   可能原因：文章不存在或已删除", file=sys.stderr)
        return None

    except urllib.error.URLError as e:
        print(f"❌ 网络错误: {e.reason}", file=sys.stderr)
        print("   请检查网络连接是否正常", file=sys.stderr)
        return None

    except Exception as e:
        import traceback
        print(f"ERROR: {type(e).__name__}: {str(e)}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return None

def main():
    if len(sys.argv) < 2:
        print("用法: python fetch_mp_article.py <微信公众号文章URL>", file=sys.stderr)
        print("示例: python fetch_mp_article.py https://mp.weixin.qq.com/s/xxxx", file=sys.stderr)
        sys.exit(1)

    url = sys.argv[1]
    result = fetch_mp_article(url)

    if result:
        # 直接以 UTF-8 二进制模式写入 stdout，避免 Windows GBK 编码问题
        sys.stdout.buffer.write(result.encode('utf-8'))
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == '__main__':
    main()
