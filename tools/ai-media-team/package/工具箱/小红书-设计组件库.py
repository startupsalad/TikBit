#!/usr/bin/env python3
"""
小红书设计组件库（产品级）

设计原则：
1. 只负责视觉呈现（设计+排版），不负责内容生产
2. 所有视觉参数（颜色/字体/尺寸）通过参数传入，不硬编码
3. 提供合理的默认值，但允许完全自定义
4. 每个组件返回完整的HTML字符串
5. 支持 custom_css 参数扩展样式

使用方式：
    from 小红书设计组件库 import *

    # 定义品牌色（从配置文件读取）
    colors = {
        "primary_color": "#6366f1",
        "accent_color": "#61bc84",
        "bg_color": "#f5f5f5",
        "text_color": "#1a1a1a"
    }

    # 生成页面
    pages = [
        cover(title="标题", subtitle="副标题", **colors),           # 简洁封面
        cover_gradient(lines=["第一行", "第二行", "第三行"], ...),  # 炫酷封面
        pain_list(title="痛点", items=[...], **colors),
        cta(quote="金句", action="行动", **colors)
    ]

    # 渲染为图片
    generate_images(pages, output_dir="输出路径")
"""

from playwright.sync_api import sync_playwright
import os


def cover(
    title,
    subtitle="",
    author="",
    emoji="",
    style="light",
    # 颜色参数
    primary_color="#6366f1",
    accent_color="#61bc84",
    bg_color="#ffffff",
    text_color="#1a1a1a",
    text_secondary="#666666",
    # 字体参数
    font_family='"PingFang SC", "Microsoft YaHei", sans-serif',
    # 自定义CSS
    custom_css="",
    **kwargs
):
    """
    封面页

    参数:
    - title: 主标题
    - subtitle: 副标题（可选）
    - author: 作者署名（可选）
    - emoji: 大emoji（可选）
    - style: 'light' 或 'dark'
    - primary_color: 主色
    - accent_color: 点缀色
    - bg_color: 背景色
    - text_color: 主文字色
    - text_secondary: 次要文字色
    - font_family: 字体
    - custom_css: 自定义CSS
    """

    # 根据style调整默认色值
    if style == "dark":
        bg_color = bg_color if bg_color != "#ffffff" else "#1a1a1a"
        text_color = text_color if text_color != "#1a1a1a" else "#ffffff"
        text_secondary = text_secondary if text_secondary != "#666666" else "#cccccc"

    emoji_html = f'<div class="emoji-big">{emoji}</div>' if emoji else ''
    subtitle_html = f'<div class="subtitle">{subtitle}</div>' if subtitle else ''
    author_html = f'<div class="author">{author}</div>' if author else ''

    html = f'''<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    width: 1080px;
    height: 1440px;
    background: linear-gradient(135deg, {bg_color} 0%, {bg_color}dd 100%);
    font-family: {font_family};
    display: flex;
    align-items: center;
    justify-content: center;
  }}
  .page {{
    text-align: center;
    padding: 80px 60px;
  }}
  .emoji-big {{
    font-size: 120px;
    margin-bottom: 40px;
  }}
  .title {{
    font-size: 72px;
    font-weight: 900;
    color: {text_color};
    line-height: 1.3;
    margin-bottom: 30px;
  }}
  .subtitle {{
    font-size: 48px;
    font-weight: 600;
    color: {primary_color};
    line-height: 1.4;
    margin-bottom: 60px;
  }}
  .author {{
    font-size: 32px;
    color: {text_secondary};
    margin-top: 80px;
  }}
  {custom_css}
</style>
</head>
<body>
  <div class="page">
    {emoji_html}
    <div class="title">{title}</div>
    {subtitle_html}
    {author_html}
  </div>
</body>
</html>'''

    return html


def pain_list(
    title,
    emoji,
    items,
    highlight_index=None,
    # 颜色参数
    primary_color="#6366f1",
    bg_color="#f5f5f5",
    card_bg="#ffffff",
    text_color="#1a1a1a",
    text_secondary="#333333",
    highlight_bg="#fff5f5",
    # 字体参数
    font_family='"PingFang SC", "Microsoft YaHei", sans-serif',
    # 自定义CSS
    custom_css="",
    **kwargs
):
    """
    痛点/问题列表页

    参数:
    - title: 页面标题
    - emoji: 大emoji
    - items: 列表项（字符串数组）
    - highlight_index: 高亮第几项（从0开始，None=不高亮）
    - primary_color: 主色（边框、高亮文字）
    - bg_color: 页面背景色
    - card_bg: 卡片背景色
    - text_color: 主文字色
    - text_secondary: 次要文字色
    - highlight_bg: 高亮卡片背景色
    - font_family: 字体
    - custom_css: 自定义CSS
    """

    # 生成列表项HTML
    items_html = ""
    for i, item in enumerate(items):
        is_highlight = (i == highlight_index)
        card_class = "pain-highlight" if is_highlight else "pain-item"
        items_html += f'''
        <div class="{card_class}">
          <div class="pain-text">{item}</div>
        </div>
        '''

    html = f'''<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    width: 1080px;
    height: 1440px;
    background: linear-gradient(135deg, {bg_color} 0%, {card_bg} 50%, {bg_color} 100%);
    font-family: {font_family};
  }}
  .page {{
    padding: 70px 60px;
    display: flex;
    flex-direction: column;
  }}
  .emoji-big {{
    font-size: 100px;
    text-align: center;
    margin-bottom: 30px;
  }}
  .title {{
    font-size: 64px;
    font-weight: 900;
    color: {text_color};
    text-align: center;
    margin-bottom: 50px;
  }}
  .pain-list {{
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 24px;
  }}
  .pain-item {{
    background: {card_bg};
    border-radius: 20px;
    padding: 28px 36px;
    border-left: 6px solid {primary_color};
    box-shadow: 0 4px 16px rgba(0,0,0,0.06);
  }}
  .pain-highlight {{
    background: {highlight_bg};
    border-left: 6px solid {primary_color};
    padding: 32px 40px;
    box-shadow: 0 6px 20px rgba(99,102,241,0.15);
  }}
  .pain-text {{
    font-size: 34px;
    font-weight: 500;
    color: {text_secondary};
    line-height: 1.5;
  }}
  .pain-highlight .pain-text {{
    font-weight: 800;
    color: {primary_color};
    font-size: 38px;
  }}
  {custom_css}
</style>
</head>
<body>
  <div class="page">
    <div class="emoji-big">{emoji}</div>
    <div class="title">{title}</div>
    <div class="pain-list">
      {items_html}
    </div>
  </div>
</body>
</html>'''

    return html


def insight(
    emoji,
    text,
    key_phrase="",
    style="center",
    # 颜色参数
    primary_color="#6366f1",
    bg_color="#ffffff",
    text_color="#1a1a1a",
    # 字体参数
    font_family='"PingFang SC", "Microsoft YaHei", sans-serif',
    # 自定义CSS
    custom_css="",
    **kwargs
):
    """
    金句/洞察页

    参数:
    - emoji: 大emoji
    - text: 金句文本
    - key_phrase: 关键短语（会用主色高亮）
    - style: 'center' 或 'left'
    - primary_color: 主色（关键短语颜色）
    - bg_color: 背景色
    - text_color: 文字色
    - font_family: 字体
    - custom_css: 自定义CSS
    """

    # 如果有关键短语，替换为高亮版本
    if key_phrase and key_phrase in text:
        text = text.replace(key_phrase, f'<span class="highlight">{key_phrase}</span>')

    align = "center" if style == "center" else "left"

    html = f'''<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    width: 1080px;
    height: 1440px;
    background: {bg_color};
    font-family: {font_family};
    display: flex;
    align-items: center;
    justify-content: center;
  }}
  .page {{
    padding: 80px 60px;
    text-align: {align};
  }}
  .emoji-big {{
    font-size: 120px;
    margin-bottom: 50px;
  }}
  .insight-text {{
    font-size: 56px;
    font-weight: 800;
    color: {text_color};
    line-height: 1.5;
  }}
  .highlight {{
    color: {primary_color};
  }}
  {custom_css}
</style>
</head>
<body>
  <div class="page">
    <div class="emoji-big">{emoji}</div>
    <div class="insight-text">{text}</div>
  </div>
</body>
</html>'''

    return html


def steps(
    title,
    steps_data,
    show_time=True,
    # 颜色参数
    primary_color="#6366f1",
    accent_color="#61bc84",
    bg_color="#f5f5f5",
    card_bg="#ffffff",
    text_color="#1a1a1a",
    text_secondary="#666666",
    # 字体参数
    font_family='"PingFang SC", "Microsoft YaHei", sans-serif',
    # 自定义CSS
    custom_css="",
    **kwargs
):
    """
    步骤流程页

    参数:
    - title: 页面标题
    - steps_data: 步骤列表，格式：[{"name": "步骤名", "time": "10分钟", "desc": "描述"}, ...]
    - show_time: 是否显示时间
    - primary_color: 主色
    - accent_color: 点缀色（步骤编号）
    - bg_color: 页面背景色
    - card_bg: 卡片背景色
    - text_color: 主文字色
    - text_secondary: 次要文字色
    - font_family: 字体
    - custom_css: 自定义CSS
    """

    # 生成步骤HTML
    steps_html = ""
    for i, step in enumerate(steps_data, 1):
        time_html = f'<div class="step-time">{step.get("time", "")}</div>' if show_time and step.get("time") else ''
        desc_html = f'<div class="step-desc">{step["desc"]}</div>' if step.get("desc") else ''

        steps_html += f'''
        <div class="step-item">
          <div class="step-number">{i}</div>
          <div class="step-content">
            <div class="step-name">{step["name"]}</div>
            {time_html}
            {desc_html}
          </div>
        </div>
        '''

    html = f'''<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    width: 1080px;
    height: 1440px;
    background: linear-gradient(135deg, {bg_color} 0%, {card_bg} 100%);
    font-family: {font_family};
  }}
  .page {{
    padding: 70px 60px;
  }}
  .title {{
    font-size: 64px;
    font-weight: 900;
    color: {text_color};
    text-align: center;
    margin-bottom: 60px;
  }}
  .steps-list {{
    display: flex;
    flex-direction: column;
    gap: 30px;
  }}
  .step-item {{
    display: flex;
    gap: 30px;
    background: {card_bg};
    border-radius: 20px;
    padding: 36px;
    box-shadow: 0 4px 16px rgba(0,0,0,0.06);
  }}
  .step-number {{
    width: 80px;
    height: 80px;
    background: {accent_color};
    color: white;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 48px;
    font-weight: 900;
    flex-shrink: 0;
  }}
  .step-content {{
    flex: 1;
  }}
  .step-name {{
    font-size: 42px;
    font-weight: 800;
    color: {text_color};
    margin-bottom: 12px;
  }}
  .step-time {{
    font-size: 32px;
    color: {primary_color};
    font-weight: 600;
    margin-bottom: 8px;
  }}
  .step-desc {{
    font-size: 28px;
    color: {text_secondary};
    line-height: 1.5;
  }}
  {custom_css}
</style>
</head>
<body>
  <div class="page">
    <div class="title">{title}</div>
    <div class="steps-list">
      {steps_html}
    </div>
  </div>
</body>
</html>'''

    return html


def compare(
    title,
    before,
    after,
    layout="horizontal",
    # 颜色参数
    primary_color="#6366f1",
    accent_color="#61bc84",
    bg_color="#f5f5f5",
    card_bg="#ffffff",
    text_color="#1a1a1a",
    text_secondary="#666666",
    # 字体参数
    font_family='"PingFang SC", "Microsoft YaHei", sans-serif',
    # 自定义CSS
    custom_css="",
    **kwargs
):
    """
    对比页

    参数:
    - title: 页面标题
    - before: 之前的列表（字符串数组）
    - after: 之后的列表（字符串数组）
    - layout: 'horizontal' 或 'vertical'
    - primary_color: 主色（之前）
    - accent_color: 点缀色（之后）
    - bg_color: 页面背景色
    - card_bg: 卡片背景色
    - text_color: 主文字色
    - text_secondary: 次要文字色
    - font_family: 字体
    - custom_css: 自定义CSS
    """

    # 生成before列表
    before_html = ""
    for item in before:
        before_html += f'<div class="compare-item before-item">{item}</div>'

    # 生成after列表
    after_html = ""
    for item in after:
        after_html += f'<div class="compare-item after-item">{item}</div>'

    flex_direction = "row" if layout == "horizontal" else "column"

    html = f'''<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    width: 1080px;
    height: 1440px;
    background: {bg_color};
    font-family: {font_family};
  }}
  .page {{
    padding: 70px 60px;
    display: flex;
    flex-direction: column;
  }}
  .title {{
    font-size: 64px;
    font-weight: 900;
    color: {text_color};
    text-align: center;
    margin-bottom: 50px;
  }}
  .compare-container {{
    flex: 1;
    display: flex;
    flex-direction: {flex_direction};
    gap: 30px;
  }}
  .compare-column {{
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 20px;
  }}
  .column-title {{
    font-size: 48px;
    font-weight: 800;
    text-align: center;
    margin-bottom: 20px;
  }}
  .before-title {{
    color: {text_secondary};
  }}
  .after-title {{
    color: {accent_color};
  }}
  .compare-item {{
    background: {card_bg};
    border-radius: 16px;
    padding: 24px 28px;
    font-size: 32px;
    font-weight: 500;
    line-height: 1.5;
    box-shadow: 0 4px 12px rgba(0,0,0,0.06);
  }}
  .before-item {{
    border-left: 5px solid {text_secondary};
    color: {text_secondary};
  }}
  .after-item {{
    border-left: 5px solid {accent_color};
    color: {text_color};
    font-weight: 600;
  }}
  {custom_css}
</style>
</head>
<body>
  <div class="page">
    <div class="title">{title}</div>
    <div class="compare-container">
      <div class="compare-column">
        <div class="column-title before-title">之前</div>
        {before_html}
      </div>
      <div class="compare-column">
        <div class="column-title after-title">之后</div>
        {after_html}
      </div>
    </div>
  </div>
</body>
</html>'''

    return html


def cta(
    quote,
    action,
    author="",
    tags=None,
    # 颜色参数
    primary_color="#6366f1",
    accent_color="#61bc84",
    bg_color="#ffffff",
    text_color="#1a1a1a",
    text_secondary="#666666",
    # 字体参数
    font_family='"PingFang SC", "Microsoft YaHei", sans-serif',
    # 自定义CSS
    custom_css="",
    **kwargs
):
    """
    转化尾页

    参数:
    - quote: 金句/引言
    - action: 行动号召
    - author: 作者署名（可选）
    - tags: 标签列表（可选）
    - primary_color: 主色
    - accent_color: 点缀色
    - bg_color: 背景色
    - text_color: 主文字色
    - text_secondary: 次要文字色
    - font_family: 字体
    - custom_css: 自定义CSS
    """

    author_html = f'<div class="author">{author}</div>' if author else ''

    tags_html = ""
    if tags:
        for tag in tags:
            tags_html += f'<span class="tag">{tag}</span>'

    html = f'''<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    width: 1080px;
    height: 1440px;
    background: linear-gradient(135deg, {bg_color} 0%, {bg_color}dd 100%);
    font-family: {font_family};
    display: flex;
    align-items: center;
    justify-content: center;
  }}
  .page {{
    padding: 80px 60px;
    text-align: center;
  }}
  .quote {{
    font-size: 52px;
    font-weight: 800;
    color: {text_color};
    line-height: 1.5;
    margin-bottom: 60px;
  }}
  .action {{
    font-size: 44px;
    font-weight: 700;
    color: {primary_color};
    background: {bg_color == "#ffffff" and "#fff5f5" or "rgba(255,255,255,0.1)"};
    padding: 30px 50px;
    border-radius: 20px;
    margin-bottom: 50px;
    display: inline-block;
  }}
  .author {{
    font-size: 32px;
    color: {text_secondary};
    margin-bottom: 40px;
  }}
  .tags {{
    display: flex;
    gap: 15px;
    justify-content: center;
    flex-wrap: wrap;
  }}
  .tag {{
    font-size: 28px;
    color: {accent_color};
    background: {bg_color == "#ffffff" and "#f0f9f4" or "rgba(255,255,255,0.1)"};
    padding: 12px 24px;
    border-radius: 30px;
  }}
  {custom_css}
</style>
</head>
<body>
  <div class="page">
    <div class="quote">{quote}</div>
    <div class="action">{action}</div>
    {author_html}
    <div class="tags">{tags_html}</div>
  </div>
</body>
</html>'''

    return html


def cover_gradient(
    lines,
    tags=None,
    flow_steps=None,
    # 渐变色参数（3色）
    gradient_colors=None,
    # 背景参数
    bg_dark="#0B0F1A",
    bg_mid="#1a1035",
    # 字体参数
    font_family='"PingFang SC", "Microsoft YaHei", sans-serif',
    # 自定义CSS
    custom_css="",
    **kwargs
):
    """
    炫酷封面：深色底 + 光球背景 + 渐变文字 + 标签 + 流程图

    参数:
    - lines: 标题行列表（最后一行为渐变高亮行）
      例: ["做新媒体的人", "一定要给自己搭一条", "内容生产线"]
    - tags: 标签列表（可选）
      例: ["📦 整套系统打包带走", "💪 1人≈1个团队"]
    - flow_steps: 流程步骤列表（可选）
      例: [{"name": "选题", "color": "#0EA5E9"}, {"name": "创作", "color": "#06B6D4"}]
    - gradient_colors: 渐变色列表（3色，默认青紫粉）
      例: ["#0EA5E9", "#8B5CF6", "#F43F5E"]
    - bg_dark: 深色背景主色
    - bg_mid: 深色背景中间色
    - font_family: 字体
    - custom_css: 自定义CSS
    """

    if gradient_colors is None:
        gradient_colors = ["#0EA5E9", "#8B5CF6", "#F43F5E"]

    c1, c2, c3 = gradient_colors[0], gradient_colors[1], gradient_colors[2]

    # 生成标题行HTML
    title_html = ""
    for i, line in enumerate(lines):
        if i == len(lines) - 1:
            # 最后一行：渐变高亮
            title_html += f'<div class="line-highlight">{line}</div>'
        else:
            title_html += f'<div class="line-normal">{line}</div>'

    # 生成标签HTML
    tags_html = ""
    if tags:
        tags_items = "".join(f'<div class="tag">{t}</div>' for t in tags)
        tags_html = f'<div class="tags">{tags_items}</div>'

    # 生成流程图HTML
    flow_html = ""
    if flow_steps:
        flow_items = []
        for i, step in enumerate(flow_steps):
            color = step.get("color", c1)
            flow_items.append(f'<div class="step" style="background:{color};">{step["name"]}</div>')
            if i < len(flow_steps) - 1:
                flow_items.append('<div class="arrow">→</div>')
        flow_html = f'<div class="flow">{"".join(flow_items)}</div>'

    html = f'''<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    width: 1080px;
    height: 1440px;
    overflow: hidden;
    font-family: {font_family};
  }}
  .cover {{
    width: 1080px;
    height: 1440px;
    background: linear-gradient(160deg, {bg_dark} 0%, {bg_mid} 40%, #0f1a2e 100%);
    position: relative;
    display: flex;
    flex-direction: column;
    align-items: center;
  }}
  /* 背景光球 - 左上 */
  .cover::before {{
    content: '';
    position: absolute;
    top: -100px; left: -120px;
    width: 600px; height: 600px;
    background: radial-gradient(circle, {c1}2e 0%, transparent 70%);
    pointer-events: none; z-index: 0;
  }}
  /* 背景光球 - 右下 */
  .cover::after {{
    content: '';
    position: absolute;
    bottom: -120px; right: -100px;
    width: 600px; height: 600px;
    background: radial-gradient(circle, {c3}1f 0%, transparent 70%);
    pointer-events: none; z-index: 0;
  }}
  /* 中间光球 */
  .glow-center {{
    position: absolute;
    top: 30%; left: 50%;
    transform: translate(-50%, -50%);
    width: 700px; height: 500px;
    background: radial-gradient(ellipse, {c2}1f 0%, transparent 70%);
    pointer-events: none; z-index: 0;
  }}
  .title-area {{
    position: relative; z-index: 2;
    text-align: center;
    margin-top: 280px;
  }}
  .line-normal {{
    font-size: 64px;
    font-weight: 700;
    color: rgba(255,255,255,0.95);
    letter-spacing: 5px;
    margin-bottom: 16px;
    line-height: 1.3;
    text-shadow: 0 2px 20px {c2}33;
  }}
  .line-highlight {{
    font-size: 88px;
    font-weight: 900;
    letter-spacing: 10px;
    line-height: 1.2;
    background: linear-gradient(135deg, {c1}, {c2}, {c3});
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    filter: drop-shadow(0 0 30px {c2}80) drop-shadow(0 0 60px {c1}4d);
  }}
  .glow-line {{
    width: 500px; height: 3px;
    margin: 40px auto 0;
    background: linear-gradient(90deg, transparent, {c1} 20%, {c2} 50%, {c3} 80%, transparent);
    border-radius: 2px;
    box-shadow: 0 0 12px {c2}80;
    position: relative; z-index: 2;
  }}
  .tags {{
    display: flex;
    justify-content: center;
    gap: 20px;
    margin-top: 50px;
    position: relative; z-index: 2;
  }}
  .tag {{
    padding: 14px 28px;
    border-radius: 30px;
    background: rgba(255,255,255,0.06);
    border: 1.5px solid {c2}59;
    color: rgba(255,255,255,0.85);
    font-size: 26px;
    font-weight: 500;
    letter-spacing: 1px;
    backdrop-filter: blur(10px);
  }}
  .flow {{
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 16px;
    margin-top: auto;
    margin-bottom: 160px;
    position: relative; z-index: 2;
  }}
  .step {{
    width: 100px; height: 100px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #fff;
    font-size: 26px;
    font-weight: 700;
    letter-spacing: 2px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.3);
  }}
  .arrow {{
    color: rgba(255,255,255,0.3);
    font-size: 28px;
  }}
  .bottom-line {{
    position: absolute;
    bottom: 70px;
    left: 60px; right: 60px;
    height: 3px;
    background: linear-gradient(90deg, transparent, {c1} 20%, {c2} 50%, {c3} 80%, transparent);
    border-radius: 2px;
    box-shadow: 0 0 12px {c2}66;
    z-index: 2;
  }}
  {custom_css}
</style>
</head>
<body>
  <div class="cover">
    <div class="glow-center"></div>
    <div class="title-area">
      {title_html}
    </div>
    <div class="glow-line"></div>
    {tags_html}
    {flow_html}
    <div class="bottom-line"></div>
  </div>
</body>
</html>'''

    return html


def generate_images(pages, output_dir, width=1080, height=1440, dpi=2):
    """
    批量生成图片

    参数:
    - pages: 组件函数返回的HTML列表
    - output_dir: 输出文件夹路径
    - width: 页面宽度（默认1080px）
    - height: 页面高度（默认1440px）
    - dpi: 设备像素比（默认2，即2倍图）
    """

    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch()

        for i, html in enumerate(pages, 1):
            page = browser.new_page(
                viewport={"width": width, "height": height},
                device_scale_factor=dpi
            )
            page.set_content(html)
            page.wait_for_timeout(500)  # 等待渲染完成

            output_path = os.path.join(output_dir, f"P{i}.png")
            page.screenshot(path=output_path, type="png")
            print(f"✓ 已生成: {output_path}")

            page.close()

        browser.close()

    print(f"\n✓ 全部完成！共生成 {len(pages)} 张图片")


if __name__ == "__main__":
    # 示例：生成一套图文（演示两种封面风格）

    # 定义品牌色（实际使用时从配置文件读取）
    colors = {
        "primary_color": "#6366f1",
        "accent_color": "#61bc84",
        "bg_color": "#f5f5f5",
        "card_bg": "#ffffff",
        "text_color": "#1a1a1a",
        "text_secondary": "#666666"
    }

    # 示例1：简洁封面风格
    pages_simple = [
        cover(
            title="主标题",
            subtitle="副标题",
            author="作者名",
            emoji="✨",
            **colors
        ),
        pain_list(
            title="痛点列表",
            emoji="😩",
            items=["痛点1", "痛点2", "痛点3"],
            highlight_index=2,
            **colors
        ),
        cta(
            quote="金句文案",
            action="行动召唤",
            author="作者名",
            tags=["#标签1", "#标签2"],
            **colors
        )
    ]

    # 示例2：炫酷封面风格
    pages_gradient = [
        cover_gradient(
            lines=["第一行文字", "第二行文字", "第三行高亮"],
            tags=["📦 标签1", "💪 标签2", "📱 标签3"],
            flow_steps=[
                {"name": "步骤1", "color": "#0EA5E9"},
                {"name": "步骤2", "color": "#06B6D4"},
                {"name": "步骤3", "color": "#8B5CF6"},
                {"name": "步骤4", "color": "#EC4899"}
            ],
            gradient_colors=["#0EA5E9", "#8B5CF6", "#F43F5E"]
        ),
        insight(
            emoji="🤔",
            text="金句文案，关键词会高亮显示",
            key_phrase="关键词",
            **colors
        ),
        steps(
            title="流程步骤",
            steps_data=[
                {"name": "步骤1", "time": "10分钟", "desc": "描述1"},
                {"name": "步骤2", "time": "20分钟", "desc": "描述2"}
            ],
            **colors
        )
    ]

    # 生成图片
    print("生成简洁风格...")
    generate_images(pages_simple, output_dir="./输出/简洁风格")

    print("\n生成炫酷风格...")
    generate_images(pages_gradient, output_dir="./输出/炫酷风格")

