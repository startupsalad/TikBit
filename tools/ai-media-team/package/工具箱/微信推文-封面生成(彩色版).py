#!/usr/bin/env python3
"""
微信推文生成封面图工具（彩色版 / Multi-Gradient 风格）
尺寸：900×383px（公众号头条封面标准，2.35:1）
安全区：中间 383×383px 正方形（分享时裁切为卡片封面）
风格：深色/浅色可选 + 青紫粉三色渐变（固定视觉风格，不依赖品牌色）
输出：2x 高清（1800×766px）
支持彩色 Emoji 渲染

使用方法：
  1. 修改下方 CONFIG 区域的文字内容
  2. 设置 STYLE = "dark" 或 STYLE = "light" 选择深色底/浅色底
  3. 设置 OUTPUT_PATH 为目标绝对路径
  4. 运行脚本：python3 "新媒体AI员工/工具箱/微信推文-封面生成(彩色版).py"

依赖：Python 3 + Playwright（pip install playwright && playwright install chromium）
"""

import os
from playwright.sync_api import sync_playwright

# ============================================================
# CONFIG - 每次生成新封面时，只需修改这里
# ============================================================

# 输出完整路径（绝对路径，由柳如是在调用时设置）
# 默认保存到脚本同目录，柳如是调用时会覆盖此路径
OUTPUT_FILENAME = "封面_彩色版示例.png"

# 风格选择："dark"（深色底，推荐）或 "light"（浅色底）
STYLE = "dark"

# 4行文字
LINE1 = "主标题文字"          # 渐变色大字（深色底）/ 渐变色大字（浅色底）
LINE2 = "副标题文字"          # 白色大字（深色底）/ 深色大字（浅色底）
LINE3 = "说明行1"             # 半透明白字（深色底）/ 灰色字（浅色底）
LINE4 = "说明行2"             # 渐变色字（深色底）/ 渐变色字（浅色底）

# 底部标签（3个关键词，可带 Emoji）
TAG1 = "🎯 标签1"
TAG2 = "🤖 标签2"
TAG3 = "⚡ 标签3"

# ============================================================
# 以下为模板代码，一般不需要修改
# ============================================================

# 输出路径：默认保存到脚本同目录（柳如是调用时通过命令行参数或直接修改 OUTPUT_PATH 覆盖）
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_PATH = os.path.join(SCRIPT_DIR, OUTPUT_FILENAME)

# ---- 深色底模板 ----
# 背景：#0B0F1A → #1a1035 → #0f1a2e 深蓝紫渐变
# 适用：朋友圈/信息流中更醒目
HTML_DARK = """
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
    background: linear-gradient(135deg, #0B0F1A 0%, #1a1035 50%, #0f1a2e 100%);
    position: relative;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
  }}

  /* 背景光球 - 左上蓝 */
  .cover::before {{
    content: '';
    position: absolute;
    top: -60px;
    left: -80px;
    width: 350px;
    height: 350px;
    background: radial-gradient(circle, rgba(14,165,233,0.15) 0%, transparent 70%);
    pointer-events: none;
    z-index: 0;
  }}

  /* 背景光球 - 右下红 */
  .cover::after {{
    content: '';
    position: absolute;
    bottom: -80px;
    right: -60px;
    width: 350px;
    height: 350px;
    background: radial-gradient(circle, rgba(244,63,94,0.12) 0%, transparent 70%);
    pointer-events: none;
    z-index: 0;
  }}

  /* 中间光球 - 紫 */
  .glow-center {{
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 400px;
    height: 300px;
    background: radial-gradient(ellipse, rgba(139,92,246,0.1) 0%, transparent 70%);
    pointer-events: none;
    z-index: 0;
  }}

  .content {{
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -55%);
    z-index: 2;
    text-align: center;
    width: 100%;
    padding: 0 40px;
  }}

  /* 第一行：主标题 - 渐变色 */
  .line1 {{
    font-size: 56px;
    font-weight: 900;
    letter-spacing: 5px;
    margin-bottom: 8px;
    line-height: 1.2;
    background: linear-gradient(135deg, #0EA5E9, #8B5CF6, #F43F5E);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    filter: drop-shadow(0 0 20px rgba(139,92,246,0.4));
  }}

  /* 第二行：副标题 - 白色大字 */
  .line2 {{
    font-size: 50px;
    font-weight: 900;
    color: #FFFFFF;
    letter-spacing: 8px;
    text-shadow: 0 0 20px rgba(139,92,246,0.3), 0 2px 10px rgba(0,0,0,0.5);
    margin-bottom: 12px;
    line-height: 1.2;
  }}

  /* 渐变装饰线 */
  .glow-line {{
    width: 340px;
    height: 2px;
    margin: 0 auto 10px;
    background: linear-gradient(90deg, transparent, #0EA5E9 20%, #8B5CF6 50%, #F43F5E 80%, transparent);
    border-radius: 1px;
    box-shadow: 0 0 8px rgba(139,92,246,0.4);
  }}

  /* 第三行 */
  .line3 {{
    font-size: 30px;
    font-weight: 500;
    color: rgba(255,255,255,0.85);
    letter-spacing: 4px;
    margin-bottom: 4px;
    line-height: 1.4;
    text-shadow: 0 0 10px rgba(14,165,233,0.3);
  }}

  /* 第四行 */
  .line4 {{
    font-size: 28px;
    font-weight: 500;
    letter-spacing: 3px;
    line-height: 1.4;
    background: linear-gradient(90deg, #0EA5E9, #8B5CF6, #F43F5E);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    filter: drop-shadow(0 0 10px rgba(139,92,246,0.3));
  }}

  /* 底部标签 */
  .tags {{
    position: absolute;
    bottom: 14px;
    left: 0;
    right: 0;
    z-index: 2;
    text-align: center;
  }}

  .tags-line {{
    width: 600px;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(139,92,246,0.3) 20%, rgba(139,92,246,0.3) 80%, transparent);
    margin: 0 auto 8px;
  }}

  .tags-text {{
    font-size: 18px;
    color: rgba(255,255,255,0.6);
    letter-spacing: 2px;
    font-weight: 500;
  }}

  .tags-text span {{
    margin: 0 14px;
  }}
</style>
</head>
<body>
  <div class="cover">
    <div class="glow-center"></div>
    <div class="content">
      <div class="line1">{line1}</div>
      <div class="line2">{line2}</div>
      <div class="glow-line"></div>
      <div class="line3">{line3}</div>
      <div class="line4">{line4}</div>
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

# ---- 浅色底模板 ----
# 背景：#FAFBFF → #f0f0ff 浅蓝白
# 适用：清新风格，教育类内容
HTML_LIGHT = """
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
    background: linear-gradient(135deg, #FAFBFF 0%, #f0f0ff 50%, #e8f4ff 100%);
    position: relative;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
  }}

  /* 背景光球 - 左上蓝（更淡） */
  .cover::before {{
    content: '';
    position: absolute;
    top: -60px;
    left: -80px;
    width: 350px;
    height: 350px;
    background: radial-gradient(circle, rgba(14,165,233,0.08) 0%, transparent 70%);
    pointer-events: none;
    z-index: 0;
  }}

  /* 背景光球 - 右下红（更淡） */
  .cover::after {{
    content: '';
    position: absolute;
    bottom: -80px;
    right: -60px;
    width: 350px;
    height: 350px;
    background: radial-gradient(circle, rgba(244,63,94,0.06) 0%, transparent 70%);
    pointer-events: none;
    z-index: 0;
  }}

  /* 中间光球 - 紫（更淡） */
  .glow-center {{
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 400px;
    height: 300px;
    background: radial-gradient(ellipse, rgba(139,92,246,0.06) 0%, transparent 70%);
    pointer-events: none;
    z-index: 0;
  }}

  .content {{
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -55%);
    z-index: 2;
    text-align: center;
    width: 100%;
    padding: 0 40px;
  }}

  /* 第一行：主标题 - 渐变色（与深色底相同） */
  .line1 {{
    font-size: 56px;
    font-weight: 900;
    letter-spacing: 5px;
    margin-bottom: 8px;
    line-height: 1.2;
    background: linear-gradient(135deg, #0EA5E9, #8B5CF6, #F43F5E);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    filter: drop-shadow(0 0 15px rgba(139,92,246,0.2));
  }}

  /* 第二行：副标题 - 深色大字 */
  .line2 {{
    font-size: 50px;
    font-weight: 900;
    color: #1a1a2e;
    letter-spacing: 8px;
    text-shadow: 0 2px 10px rgba(139,92,246,0.1);
    margin-bottom: 12px;
    line-height: 1.2;
  }}

  /* 渐变装饰线 */
  .glow-line {{
    width: 340px;
    height: 2px;
    margin: 0 auto 10px;
    background: linear-gradient(90deg, transparent, #0EA5E9 20%, #8B5CF6 50%, #F43F5E 80%, transparent);
    border-radius: 1px;
    box-shadow: 0 0 6px rgba(139,92,246,0.2);
  }}

  /* 第三行 */
  .line3 {{
    font-size: 30px;
    font-weight: 500;
    color: #475569;
    letter-spacing: 4px;
    margin-bottom: 4px;
    line-height: 1.4;
  }}

  /* 第四行 */
  .line4 {{
    font-size: 28px;
    font-weight: 500;
    letter-spacing: 3px;
    line-height: 1.4;
    background: linear-gradient(90deg, #0EA5E9, #8B5CF6, #F43F5E);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    filter: drop-shadow(0 0 8px rgba(139,92,246,0.15));
  }}

  /* 底部标签 */
  .tags {{
    position: absolute;
    bottom: 14px;
    left: 0;
    right: 0;
    z-index: 2;
    text-align: center;
  }}

  .tags-line {{
    width: 600px;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(139,92,246,0.2) 20%, rgba(139,92,246,0.2) 80%, transparent);
    margin: 0 auto 8px;
  }}

  .tags-text {{
    font-size: 18px;
    color: #94A3B8;
    letter-spacing: 2px;
    font-weight: 500;
  }}

  .tags-text span {{
    margin: 0 14px;
  }}
</style>
</head>
<body>
  <div class="cover">
    <div class="glow-center"></div>
    <div class="content">
      <div class="line1">{line1}</div>
      <div class="line2">{line2}</div>
      <div class="glow-line"></div>
      <div class="line3">{line3}</div>
      <div class="line4">{line4}</div>
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

def main():
    # 根据 STYLE 选择模板
    if STYLE == "light":
        template = HTML_LIGHT
        style_name = "浅色底"
    else:
        template = HTML_DARK
        style_name = "深色底"

    html = template.format(
        line1=LINE1,
        line2=LINE2,
        line3=LINE3,
        line4=LINE4,
        tag1=TAG1,
        tag2=TAG2,
        tag3=TAG3,
    )

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 900, "height": 383}, device_scale_factor=2)
        page.set_content(html)
        page.wait_for_timeout(500)
        page.screenshot(path=OUTPUT_PATH, type="png")
        browser.close()

    print(f"✅ 封面图已生成：{OUTPUT_PATH}")
    print(f"   风格：{style_name}（{STYLE}）")
    print(f"   尺寸：1800×766px（2x 高清，原始 900×383）")
    print(f"   安全区：中间 383×383px 正方形内为核心内容")

if __name__ == "__main__":
    main()
