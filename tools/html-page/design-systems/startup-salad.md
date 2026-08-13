---
version: alpha
name: StartupSalad-Brand-System
description: 创业沙拉品牌设计系统 — 以创新驱动、专业可靠、适应金融客户为核心定位。采用深蓝+亮绿的对比组合，体现科技创新与金融稳健的融合。配合开放式几何排版，传递灵动专业的气质。
---

# 创业沙拉品牌设计系统

创业沙拉是一家以创新为驱动的企业活动及培训全案服务商。设计系统应体现以下特征：
- **创新**：敢于尝试、富有活力
- **专业**：高效可靠、值得信赖
- **金融适配**：既不失庄重，也要有差异化

## 色彩系统

### 主色板
- **Primary Deep (金融蓝)**：`#1a3a5c` — 深邃、信任、金融感
- **Primary Base (品牌蓝)**：`#0052cc` — 清晰、科技感、可操作
- **Primary Light (天空蓝)**：`#4a90e2` — 开放、积极、年轻
- **Accent (创新绿)**：`#22c55e` — 生长、创新、活力
- **Accent Soft (浅绿)**：`#dcfce7` — 柔和、安心、承诺

### 中性色
- **Dark (深灰)**：`#1f2937` — 正文、标题
- **Medium (中灰)**：`#6b7280` — 辅助文案、次要信息
- **Light (浅灰)**：`#f3f4f6` — 背景、分隔线
- **White**：`#ffffff` — 画布

### 数据色
- **Success (成功绿)**：`#10b981`
- **Warning (警告黄)**：`#f59e0b`
- **Error (错误红)**：`#ef4444`
- **Info (信息蓝)**：`#3b82f6`

## 排版系统

### 字体选择
- **Display Font (标题)**：思源黑体 Bold / 阿里巴巴普惠体 Bold
  - 用于主标题、大标题、品牌词汇，展现力量感
- **Body Font (正文)**：思源黑体 Regular / 阿里巴巴普惠体 Regular
  - 用于正文、说明文字，清晰易读
- **Fallback (备选)**：-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif

### 字体尺寸规范
- **Display XXL**：48-56px / 行高 1.2 / 字重 700
- **Display XL**：40-48px / 行高 1.25 / 字重 700
- **Display LG**：32-40px / 行高 1.3 / 字重 600
- **Title**：24-28px / 行高 1.4 / 字重 600
- **Subtitle**：18-20px / 行高 1.5 / 字重 500
- **Body Large**：16px / 行高 1.6 / 字重 400
- **Body**：14px / 行高 1.6 / 字重 400
- **Small**：12px / 行高 1.5 / 字重 400
- **Label**：12px / 行高 1.4 / 字重 600

## 间距系统

基础单位：4px

- **XS**：4px — 紧凑间距、icon 间距
- **S**：8px — 元素内部间距
- **M**：16px — 卡片内间距、组件间距
- **L**：24px — 区块间距、大间距
- **XL**：32px — 页面区块间距
- **2XL**：48px — 大型布局间距
- **3XL**：64px — 超大间距、全屏分隔

## 组件规范

### 按钮
- **Primary Button**：蓝色背景(#0052cc) + 白色文字 / 12-16px padding / 圆角 6-8px / 高度 40-48px
- **Secondary Button**：白色背景 + 蓝色边框 + 蓝色文字 / 同上
- **Ghost Button**：透明 + 绿色文字 / 用于次要操作或对比强调
- **Hover State**：背景亮度 -10% / 微妙阴影
- **Disabled**：灰色 (opacity 50%)

### 卡片 (Card)
- **背景**：白色 (#ffffff) 或浅灰 (#f3f4f6)
- **边框**：可选，浅灰色 (#e5e7eb) / 1px
- **圆角**：8-12px
- **间距**：16-24px 内边距
- **阴影**：微妙阴影 `0 1px 3px rgba(0,0,0,0.1)` 或无

### 图片占位
- **渐变背景**：从 Primary Light (#4a90e2) 到 Accent Soft (#dcfce7)
- **SVG Illustration**：使用几何形状、线条、简化图标
- **比例**：16:9 或 1:1（根据场景）

## 布局规范

### 移动端优先
- **基础宽度**：375px（iPhone SE 基准）
- **最大宽度**：1200px（桌面级）
- **网格**：4 列（移动）/ 12 列（桌面）
- **Gutter**：16px（移动）/ 24px（桌面）

### 视觉层级
- **主标题**：Primary Deep + Display XL
- **副标题**：Primary Base + Title
- **正文**：Dark + Body
- **辅助**：Medium + Small
- **禁用/不活跃**：Light + Disabled 色

## 动效规范

### 过渡动画
- **Quick**：200ms / easing: ease-out
- **Standard**：300ms / easing: cubic-bezier(0.4, 0, 0.2, 1)
- **Slow**：500ms / easing: ease-in-out

### 常用动效
- **Page Load**：淡入 + 上浮 (fade-in-up)
- **Button Hover**：背景色渐变 + 微妙放大 (1.02x)
- **Card Appear**：级联展开 (stagger animation-delay)
- **Icon Pulse**：呼吸灯效果（用于重点引导）

## 禁忌与指南

### 禁止使用
- ❌ 紫色渐变（过度使用、显得廉价）
- ❌ 过多饱和色混搭（显得杂乱）
- ❌ 系统默认字体（Arial、Helvetica）
- ❌ 过度装饰、花哨特效
- ❌ 文字过小（<12px）、行距过紧(<1.4)

### 必须遵守
- ✅ 所有文本必须有足够对比度（WCAG AA 标准）
- ✅ 交互元素最小点击区域 44x44px
- ✅ 内嵌字体优先用谷歌字体或系统字体，避免本地依赖
- ✅ 移动端优先，逐步适配桌面
- ✅ 清晰的视觉层级，避免信息超载

## 应用场景

### 适用
- 活动推文页（H5）
- 落地页、宣传页
- 内部看板、数据展示
- 品牌宣传资料
- 邀请函、电子贺卡

### 不适用
- 法律文件、正式合同（使用公司标准模板）
- 财报、审计报告（需合规设计）
