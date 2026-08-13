# HTML 页面生成系统

一套完整的 HTML 推文页/落地页生成工具，内置 10 套预制设计风格，可一键转长图 PDF 发手机。

## 快速开始

### 使用方式

直接告诉 Claude：

```
帮我做一个金融活动H5，luxury 风格，包含标题/时间/地点/亮点/报名按钮。
同时转长图PDF发手机。
```

**Claude 会自动：**
1. 读取对应的 DESIGN.md 设计规范文件
2. 生成移动端优先的 HTML（375px 基础宽度）
3. 调用 `/长图PDF` skill 转成单页长图 PDF
4. 你可以直接发微信、钉钉、企业微信

---

## 系统组成

### 1. 设计系统文件（`design-systems/`）

10 套预制设计风格，每个风格是一份 DESIGN.md 规范文件：

| 文件名 | 来源 | 适用场景 | 特点 |
|:---:|:---:|:---|:---|
| clean.md | bergside | 金融/政务 | 极简白底，黑白灰，专业稳健 |
| luxury.md | bergside | 高端理财 | 暗色奢华，金色点缀，低调精致 |
| glassmorphism.md | bergside | AI/科技 | 毛玻璃蓝紫，透明层叠，未来感 |
| dashboard.md | bergside | 数据汇报 | 模块化卡片，数据展示，系统感 |
| storytelling.md | bergside | 品牌推文 | 叙事型排版，图文混搭，有温度 |
| stripe.md | VoltAgent | 现代金融 | 蓝白对比，极简线条，可信专业 |
| linear.md | VoltAgent | 科技公司 | 暗黑极简，极限留白，高级感 |
| notion.md | VoltAgent | 内容阅读 | 编辑感排版，温暖中性，易读 |
| vercel.md | VoltAgent | 黑科技 | 纯黑白，高对比，震撼感 |
| startup-salad.md | 自制 | 创业沙拉品牌 | 蓝绿对比，几何排版，创新专业 |

### 2. html-page skill（`.claude/skills/html-page/SKILL.md`）

- **功能**：触发词识别 + 自动加载设计系统 + 生成移动端 HTML
- **触发词**：H5落地页、推文页、活动页、HTML宣传页、发手机看的页面
- **工作流**：确认需求 → 加载设计规范 → 生成 HTML → 转 PDF

### 3. 文档指南

- **使用指南.md** — 快速参考手册，包含场景示例和注意事项
- **集成完成总结.md** — 详细说明整个系统的设计和架构
- **测试案例_luxury风格.html** — 参考示例页面（用浏览器打开查看效果）

---

## 使用场景

### 场景 1：快速生成金融活动页

```
做一个银行理财论坛H5。
风格：luxury（暗色奢华）
内容：标题、时间、地点、亮点、报名按钮、二维码
需要转长图PDF。
```

**结果**：5 分钟内获得一个高质量 HTML + PDF，直接发微信朋友圈

### 场景 2：对比多个风格

```
同一个活动，帮我分别用 clean、luxury、glassmorphism 三个风格做一版。
```

**结果**：3 个 HTML 文件，对比选择最合适的风格

### 场景 3：用创业沙拉品牌风格

```
做一个创业沙拉品牌推文页，用 startup-salad 风格。
```

**结果**：自动应用公司品牌色（蓝绿对比）和规范排版

---

## 如何部署到本项目

### 方式 1：直接使用（推荐）

1. **项目级 skill 配置** — html-page skill 已复制到本项目 `.claude/skills/` 下
2. **设计系统文件** — design-systems/ 目录中的所有 DESIGN.md 已复制到本项目
3. **直接使用** — 在对话中说"做一个 H5"，Claude 会自动触发 html-page skill

### 方式 2：从资源库复制（更新时用）

当资源库版本更新时：
1. 从 `03_📦资源库/HTML页面生成系统/` 中复制最新的 DESIGN.md 文件
2. 覆盖本项目 `.claude/design-systems/` 中的旧版本
3. 确保 `.claude/skills/html-page/SKILL.md` 也是最新的

---

## 技术规范

### 生成的 HTML 特点

✅ **移动端优先**
- 基础宽度 375px（iPhone SE 标准）
- 逐步响应式适配桌面

✅ **自包含**
- 所有 CSS 内联（便于 PDF 转换）
- 无外部依赖（Google Fonts + inline styles）
- 字体用系统字体或 Google Fonts（不依赖本地安装）

✅ **微信适配**
- 禁止 `position: fixed`（微信内置浏览器会卡）
- 不超出屏幕宽度（避免横向滚动）
- 所有尺寸用相对单位（rem、%）

✅ **无障碍**
- 足够的色彩对比度（WCAG AA 标准）
- 语义化 HTML（section、article 等）
- 图片、按钮都有清晰标签

### 长图 PDF 转换

生成完 HTML 后，自动可转成单页长图 PDF：
- 无分页缝（不会被 A4 切割）
- 宽度压缩到 760px（手机竖屏舒适）
- 支持微信、企业微信、钉钉直接打开

---

## 与其他系统的关系

### vs frontend-design skill
- **frontend-design**：从零创意设计，需要详细的设计思考
- **html-page**：快速套用预制风格，重点是快速交付

→ 一个创意为主，一个效率为主

### vs 金融业活动方案生成系统
- **方案系统**：生成 Word/PDF 方案文档
- **HTML 系统**：生成移动端网页

→ 可以配合使用（方案里可以嵌入 HTML 页面链接）

### vs 长图PDF skill
- **长图PDF**：任意 HTML → 无缝长图
- **html-page**：专门为移动端推文页优化的 HTML 生成

→ html-page 生成的 HTML 经过优化，转 PDF 效果最佳

---

## 文件结构

```
03_📦资源库/HTML页面生成系统/
├── design-systems/                 ← 10 个设计系统文件
│   ├── clean.md
│   ├── luxury.md
│   ├── glassmorphism.md
│   ├── dashboard.md
│   ├── storytelling.md
│   ├── stripe.md
│   ├── linear.md
│   ├── notion.md
│   ├── vercel.md
│   ├── startup-salad.md
│   ├── 使用指南.md                ← 快速参考手册
│   ├── 集成完成总结.md             ← 详细说明文档
│   └── 测试案例_luxury风格.html     ← 参考示例
├── .claude/
│   └── skills/
│       └── html-page/
│           └── SKILL.md             ← html-page skill 定义
└── README.md                         ← 本文件
```

---

## 常见问题

**Q: 为什么要用 10 套预制风格？**
A: 能加快速度。不用每次都从零设计，直接选择现成的高质量设计系统（来自 Stripe、Linear、Notion 等大牌产品）。

**Q: 可以自定义风格吗？**
A: 可以。如果预制风格都不符合，直接告诉 Claude 你想要的感觉，它会基于 glassmorphism 或其他风格调整创建新版本。

**Q: 生成的 HTML 可以直接用吗？**
A: 可以。生成的 HTML 是生产级别的（已经过测试和优化），可以：
- 直接在浏览器打开预览
- 转成 PDF 发手机
- 上传到服务器，分享链接
- 嵌入到企业微信、钉钉等平台

**Q: 转 PDF 后还能编辑吗？**
A: PDF 是静态快照，不能编辑。如果需要改内容，编辑 HTML 源码重新转 PDF 即可（5 分钟搞定）。

**Q: 支持外部图片 CDN 吗？**
A: 不建议。转 PDF 时如果无网络会显示不了。优先用内联 data URI 或 SVG 图形占位。

---

## 后续优化方向

### 短期
- 保存首个成功案例，作为团队参考
- 根据反馈优化 startup-salad.md 品牌规范

### 中期
- 新增客制化风格（如"客户品牌专属风格"）
- 建立活动页面素材库

### 长期
- 集成 brand-guidelines skill，自动生成 DESIGN.md
- React/Vue 组件库版本（用于复杂交互）

---

## 更新记录

| 日期 | 版本 | 更新内容 |
|:---|:---|:---|
| 2026-06-18 | 1.0 | 初版发布：10 套设计系统 + html-page skill + 文档 |

---

**一句话总结**：做一个高质量 H5 推文页 = 一句话 + 3 分钟 + 一键 PDF 🚀
