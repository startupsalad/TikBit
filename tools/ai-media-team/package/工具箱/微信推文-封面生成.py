#!/usr/bin/env python3
"""
微信推文生成封面图工具（Playwright HTML渲染版）
尺寸：900×383px（公众号头条封面标准，2.35:1）
安全区：中间 383×383px 正方形（分享时裁切为卡片封面）
风格：品牌色版（自动读取用户配置文件中的品牌色）
支持彩色 Emoji 渲染

使用方法：
  直接修改下方 CONFIG 区域的文字内容，然后运行：
  python3 "新媒体AI员工/工具箱/微信推文-封面生成.py"

依赖：Python 3 + Playwright（pip install playwright && playwright install chromium）
"""

import os
import re
from playwright.sync_api import sync_playwright

# ============================================================
# CONFIG - 每次生成新封面时，只需修改这里
# ============================================================

# 输出文件名（不含路径，自动保存到脚本同目录）
OUTPUT_FILENAME = "封面_断更了无数次之后.png"

# 顶部 Emoji（3个，用空格分隔）
EMOJI_ROW = "🔄 🛠️ 🚀"

# 主标题第一行（荧光色，视觉焦点）
TITLE_LINE1 = "断更了无数次之后"

# 主标题第二行（白色）
TITLE_LINE2 = "我给自己搭了一条生产线"

# 副标题（品牌色）
SUBTITLE = "💰 30万一年的事，不能再干了"

# 底部标签（3个关键词，带 Emoji）
TAG1 = "📝 内容生产"
TAG2 = "🤖 AI系统"
TAG3 = "💼 1人≈1团队"

# ============================================================
# 自动读取用户配置文件中的品牌色
# ============================================================

def load_brand_color():
    """从配置文件读取品牌主色，如果读取失败则使用默认绿色"""
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(script_dir, "..", "我的新媒体AI员工.md")

        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 匹配 "品牌主色**：#XXXXXX" 或 "主色**：#XXXXXX"
        match = re.search(r'(?:品牌主色|主色)[*：\s]+[：]?\s*(#[0-9a-fA-F]{6})', content)
        if match:
            primary_color = match.group(1).upper()
            print(f"✅ 已读取品牌主色：{primary_color}")
            return primary_color
        else:
            print("⚠️  未找到品牌主色配置，使用默认绿色 #00D900")
            return "#00D900"
    except Exception as e:
        print(f"⚠️  读取配置文件失败：{e}，使用默认绿色 #00D900")
        return "#00D900"

# 读取品牌色
PRIMARY_COLOR = load_brand_color()

# 根据品牌色计算衍生色
def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hex(r, g, b):
    return f"#{r:02x}{g:02x}{b:02x}"

def darken_color(hex_color, factor=0.5):
    """让颜色变暗"""
    r, g, b = hex_to_rgb(hex_color)
    r = int(r * factor)
    g = int(g * factor)
    b = int(b * factor)
    return rgb_to_hex(r, g, b)

def lighten_color(hex_color, factor=1.5):
    """让颜色变亮"""
    r, g, b = hex_to_rgb(hex_color)
    r = min(255, int(r * factor))
    g = min(255, int(g * factor))
    b = min(255, int(b * factor))
    return rgb_to_hex(r, g, b)

# 计算衍生色
COLOR_DARK = darken_color(PRIMARY_COLOR, 0.4)      # 深色（装饰线暗部）
COLOR_LIGHT = lighten_color(PRIMARY_COLOR, 1.8)    # 亮色（主标题荧光色）
COLOR_GLOW = PRIMARY_COLOR                          # 中间色（装饰线、副标题）

# 计算背景渐变（深色底，带品牌色调）
r, g, b = hex_to_rgb(PRIMARY_COLOR)
BG_DARK = "#1E1E1E"
BG_LIGHT = rgb_to_hex(
    min(30, int(r * 0.1)),
    min(30, int(g * 0.15)),
    min(30, int(b * 0.1))
)

print(f"   衍生色 - 深色：{COLOR_DARK}，亮色：{COLOR_LIGHT}，发光：{COLOR_GLOW}")
print(f"   背景渐变：{BG_DARK} → {BG_LIGHT}")

# ============================================================
# 以下为模板代码，一般不需要修改
# ============================================================

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "..", "..", "📢发布定稿区")
os.makedirs(OUTPUT_DIR, exist_ok=True)
OUTPUT_PATH = os.path.join(OUTPUT_DIR, OUTPUT_FILENAME)

# 900×383, 安全区中心 383×383 (x: 258.5~641.5)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}

  body {{
    width: 900px;
    height: 383px;
    overflow: hidden;
    font-family: "Source Han Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif;
  }}

  .cover {{
    width: 900px;
    height: 383px;
    background: linear-gradient(180deg, {bg_dark} 0%, {bg_light} 100%);
    position: relative;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
  }}

  /* 噪点纹理 */
  .cover::before {{
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.04'/%3E%3C/svg%3E");
    opacity: 0.5;
    pointer-events: none;
    z-index: 1;
  }}

  .content {{
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -58%);
    z-index: 2;
    text-align: center;
    width: 100%;
    padding: 0 40px;
  }}

  /* 顶部 Emoji */
  .emoji-row {{
    font-size: 42px;
    letter-spacing: 16px;
    margin-bottom: 14px;
    filter: drop-shadow(0 0 10px {color_glow_rgba});
  }}

  /* 装饰线 */
  .glow-line {{
    width: 360px;
    height: 2px;
    margin: 0 auto 16px;
    background: linear-gradient(90deg, transparent, {color_dark} 20%, {color_glow} 50%, {color_dark} 80%, transparent);
    border-radius: 1px;
    box-shadow: 0 0 8px {color_glow_rgba};
  }}

  /* 主标题第一行 */
  .title-line1 {{
    font-size: 46px;
    font-weight: 900;
    color: {color_light};
    letter-spacing: 6px;
    text-shadow: 0 0 20px {color_light_rgba_35}, 0 0 40px {color_light_rgba_15};
    margin-bottom: 8px;
    line-height: 1.2;
  }}

  /* 主标题第二行 */
  .title-line2 {{
    font-size: 42px;
    font-weight: 900;
    color: #FFFFFF;
    letter-spacing: 3px;
    text-shadow: 0 2px 10px rgba(0,0,0,0.5);
    margin-bottom: 16px;
    line-height: 1.2;
  }}

  /* 副标题 */
  .subtitle {{
    font-size: 24px;
    font-weight: 500;
    color: {color_glow};
    letter-spacing: 4px;
    text-shadow: 0 0 12px {color_glow_rgba};
  }}

  /* 底部标签 */
  .tags {{
    position: absolute;
    bottom: 16px;
    left: 0;
    right: 0;
    z-index: 2;
    text-align: center;
  }}

  .tags-line {{
    width: 600px;
    height: 1px;
    background: #2a2a2a;
    margin: 0 auto 10px;
  }}

  .tags-text {{
    font-size: 14px;
    color: #777777;
    letter-spacing: 1px;
  }}

  .tags-text span {{
    margin: 0 12px;
  }}
</style>
</head>
<body>
  <div class="cover">
    <div class="content">
      <div class="emoji-row">{emoji_row}</div>
      <div class="glow-line"></div>
      <div class="title-line1">{title_line1}</div>
      <div class="title-line2">{title_line2}</div>
      <div class="subtitle">{subtitle}</div>
    </div>

    <div class="tags">
      <div class="tags-line"></div>
      <div class="tags-text">
        <span>{tag1}</span>
        <span>{tag2}</span>
        <span>{tag3}</span>
      </div>
    </div>
  </div>
</body>
</html>
"""

def hex_to_rgba(hex_color, alpha):
    """将HEX颜色转换为rgba字符串"""
    r, g, b = hex_to_rgb(hex_color)
    return f"rgba({r},{g},{b},{alpha})"

def main():
    html = HTML_TEMPLATE.format(
        emoji_row=EMOJI_ROW,
        title_line1=TITLE_LINE1,
        title_line2=TITLE_LINE2,
        subtitle=SUBTITLE,
        tag1=TAG1,
        tag2=TAG2,
        tag3=TAG3,
        bg_dark=BG_DARK,
        bg_light=BG_LIGHT,
        color_dark=COLOR_DARK,
        color_glow=COLOR_GLOW,
        color_light=COLOR_LIGHT,
        color_glow_rgba=hex_to_rgba(COLOR_GLOW, 0.4),
        color_light_rgba_35=hex_to_rgba(COLOR_LIGHT, 0.35),
        color_light_rgba_15=hex_to_rgba(COLOR_LIGHT, 0.15),
    )

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 900, "height": 383}, device_scale_factor=2)
        page.set_content(html)
        page.wait_for_timeout(500)
        page.screenshot(path=OUTPUT_PATH, type="png")
        browser.close()

    print(f"✅ 封面图已生成：{OUTPUT_PATH}")
    print(f"   尺寸：1800×766px（2x 高清，原始 900×383）")
    print(f"   安全区：中间 383×383px 正方形内为核心内容")

if __name__ == "__main__":
    main()
