---
name: html-page
description: 生成移动端优先的 HTML 推文页/落地页，支持选择品牌风格（金融专业/奢华暗色/科技感/极简等），可链接长图PDF导出。触发词：H5落地页、推文页、活动页、HTML宣传页、发手机看的页面。
---

# HTML 页面生成 skill — 推文页 & 落地页

专门用于生成高质量的移动端优先 HTML 推文页面和落地页，内置 10 套风格可选，生成完成后可一键转长图 PDF 发手机。

## 工作流

### 第一步：确认需求

与用户确认以下 3 个要点：

1. **页面内容** — 要传达什么？
   - 活动主题、时间地点、报名二维码
   - 项目亮点、参与人信息
   - 品牌故事、宣传语
   - 其他说明文字、视觉重点

2. **风格方向** — 选择以下风格之一（或自定义描述）：
   
   | 风格名 | 适用场景 | 特点 |
   |:---:|:---|:---|
   | **clean** | 金融/政务活动 | 极简白底，黑白灰，专业稳健 |
   | **luxury** | 高端理财/私人银行 | 暗色奢华，金色点缀，低调精致 |
   | **glassmorphism** | AI/科技活动 | 毛玻璃蓝紫，透明层叠，未来感 |
   | **dashboard** | 数据汇报/白皮书 | 模块化卡片，数据展示，系统感 |
   | **storytelling** | 品牌推文/公益活动 | 叙事型排版，图文混搭，有温度 |
   | **stripe** | 现代金融/SaaS | 蓝白对比，极简线条，可信专业 |
   | **linear** | 科技公司/产品发布 | 暗黑极简，极限留白，高级感 |
   | **notion** | 内容阅读/编辑型 | 编辑感排版，温暖中性，易读 |
   | **vercel** | 黑科技/前沿产品 | 纯黑白，高对比，震撼感 |
   | **startup-salad** | 创业沙拉品牌活动 | 蓝绿对比，几何排版，创新专业 |
   | 自定义 | 特殊需求 | 描述想要的感觉和氛围 |

3. **输出格式** — 需要什么？
   - 只要 HTML 文件？
   - 同时转长图 PDF（便于发微信、手机看）？

### 第二步：加载设计系统

根据选择的风格，读取对应的设计规范文件：
```
.claude/design-systems/{style}.md
```

这个文件包含：
- 色彩系统（主色、辅色、中性色）
- 排版规范（字体、字号、行高）
- 组件样式（按钮、卡片、间距）
- 布局指南（移动端优先、响应式）
- 动效规范（过渡、动画）

### 第三步：生成 HTML

基于以下技术规范生成完整的、可立即使用的 HTML 文件：

**结构要求：**
- ✅ 单个 HTML 文件（所有 CSS 内联、无外部依赖）
- ✅ 响应式设计（移动端 375px 优先，逐步适配）
- ✅ 语义化 HTML（section, article, header, footer）
- ✅ 无障碍设计（alt 文本、ARIA 标签、足够对比度）

**样式要求：**
- 所有样式 `<style>` 内联（便于长图PDF转换）
- CSS 变量保持色彩一致 `--color-primary`, `--color-accent` 等
- 字体使用 Google Fonts 或系统字体，**禁止依赖本地字体**
- 背景色延伸满屏（不留白边）
- 移动优先，用 `@media (min-width: 768px)` 适配桌面

**内容要求：**
- 图片无法获取时，用渐变色块 `linear-gradient()` 或 SVG 图形占位
- 按钮、链接、二维码码位都要清晰可点击
- 文字对比度达到 WCAG AA 标准（不低于 4.5:1）

**微信适配：**
- ❌ 禁止 `position: fixed`（微信内置浏览器会卡）
- ❌ 禁止超出屏幕宽度（避免横向滚动）
- ✅ 使用 `overflow-x: hidden` 确保不溢出
- ✅ 所有尺寸用 `rem` 或 `%`（相对单位）

### 第四步（可选）：长图PDF导出

生成完 HTML 后，自动提示用户：

> 这个 HTML 已生成！需要转成长图 PDF 方便发手机吗？（微信、Safari、文件 App 都能直接打开）

如果用户同意，调用 `/长图PDF` skill：
```bash
/长图PDF <path-to-html>
```

输出的 PDF 会自动：
- 渲染成单页、无分页缝
- 宽度压缩到 760px（手机竖屏阅读舒适）
- 背景色、图片、动画都保留

## 技术栈参考

### 推荐方案

| 需求 | 选择 |
|:---|:---|
| 简单静态页 | 纯 HTML + CSS |
| 需要数据绑定 | Alpine.js（轻量） 或 htmx |
| 需要动效 | CSS Animations + `animation-delay` 级联 |
| 需要图表 | Chart.js 或 ECharts（需要 CDN，谨慎使用） |
| 需要交互 | 原生 JavaScript 或轻量库 |

### 禁止事项

- ❌ 引入大型框架（React、Vue）— 过重，不适合一页纸
- ❌ 外部 CSS 文件 — 长图PDF转换会丢失
- ❌ 图片远程 CDN — 转 PDF 时如果无网络会显示不了；优先内联 data URI 或 SVG
- ❌ JavaScript 事件过度 — 仅用于微交互，不做复杂逻辑

## 文件结构示例

生成的 HTML 应遵循以下结构：

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>页面标题</title>
    <style>
        /* 所有 CSS 在这里 */
        :root {
            --color-primary: #0052cc;  /* 从 DESIGN.md 提取 */
            --color-accent: #22c55e;
            --spacing-m: 16px;
        }
        body {
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            background: var(--color-bg);
            color: var(--color-text);
            overflow-x: hidden;  /* 微信适配 */
        }
        @media (max-width: 767px) {
            /* 移动端优先 */
        }
        @media (min-width: 768px) {
            /* 桌面适配 */
        }
    </style>
</head>
<body>
    <header><!-- 头部 --></header>
    <main><!-- 主内容 --></main>
    <footer><!-- 页脚 --></footer>
    
    <script>
        // 仅轻量级交互，如下拉刷新提示、按钮点击反馈等
    </script>
</body>
</html>
```

## 对话示例

**用户：** "帮我做一个某行理财活动H5，奢华暗色风格，包含活动名称、时间地点、亮点介绍、报名二维码"

**Skill 响应：**
1. ✅ 确认需求：奢华暗色（luxury）风格 + 完整信息
2. ✅ 加载 `luxury.md` 设计规范
3. ✅ 生成 HTML（深色背景、金色点缀、卡片式排版）
4. ✅ 提示："已生成！需要转长图PDF发手机吗？"

---

## 常见问题

**Q: 为什么不用 React / Vue？**
A: 这类框架适合复杂交互，但一页纸活动推文用不上。纯 HTML + CSS 加载快、体积小、转 PDF 也不会出问题。

**Q: 图片怎么处理？**
A: 优先用渐变色块或 SVG 占位。如果用户提供图片 URL，可以：
- 内联 data URI（小图）
- 或留下 `src` 占位符，用户手动替换

**Q: 可以加动画吗？**
A: 可以，用 CSS Animations。但要：
- 只用于关键信息（标题淡入、按钮悬停）
- 动画时长 200-500ms（不要太长）
- 提供 `prefers-reduced-motion` 选项（无障碍）

**Q: 转 PDF 后页面怎样才不会变形？**
A: 保持这几点：
- 宽度 ≤ 760px（PDF 默认宽度）
- 不用 `vw` 单位（会溢出）
- 用 `rem` 或 `px` 相对单位
- 避免 `position: fixed`

---

## 下一步

- 生成完 HTML 后，用户可以：
  1. 在浏览器预览（直接打开 .html 文件）
  2. 转长图 PDF 分享
  3. 嵌入到企业微信、钉钉等内部系统
  4. 或上传到服务器，分享链接
