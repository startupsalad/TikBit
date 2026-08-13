# 网页设计套件 · 给其他 AI 的安装指令

> 这份文档是写给**其他同事的 AI 助手**看的，用于从团队工具库安装网页设计套件到他们本机。

---

## 📦 套件说明

这是创业沙拉的**网页设计套件**，让 AI 按专业方法论设计网站/落地页/官网/H5，避免"AI 模板货"感。

**包含**：
1. **设计大脑**（`设计大脑/`）：
   - 网页设计方法论（五步法：定调性→借骨架→写文案→执行→自检）
   - 12 个世界级品牌参考库（Stripe/Linear/Vercel/Apple/Notion/Framer/Figma/Raycast/Cal/Nike/Spotify/Airbnb）
   - 品牌定义模板、H5 规范、营销文案经验

2. **执行技能**（`skills/`）：
   - `web-design-engineer/` — 设计风格参考库
   - `frontend-design/` — 前端设计执行

---

## 🚀 安装步骤（AI 助手执行）

### 第 1 步：确认环境

检查用户有没有 Node.js（安装引擎需要）：

```bash
node -v
```

- 有 Node → 继续
- 没有 → 引导用户去 https://startupsalad.com/setup 装 AI 工作台（含 Node）

### 第 2 步：定位原始安装包

**重要**：团队工具库里的是"源文件"，安装需要**原始安装包**的 `install-core.js`。

询问用户：

> 你有原始的「网页设计套件」安装包吗？
> - 如果有 → 告诉我路径
> - 如果没有 → 去找熊哥或大龙要一份

假设用户提供了路径：`/path/to/StartupSalad-AI-WebDesign/网页设计套件`

### 第 3 步：运行安装引擎

```bash
cd "/path/to/StartupSalad-AI-WebDesign/网页设计套件"
node 核心/install-core.js 核心
```

安装引擎会自动：
1. 复制「设计大脑」到 `~/.claude/web-design/`
2. 智能检测 skills（`web-design-engineer` / `frontend-design`）是否已存在，缺了才补装到 `~/.claude/skills/`
3. 在 `~/.claude/CLAUDE.md` 和各 Obsidian 知识库的 `CLAUDE.md` 里追加使用指令（幂等，重复装不叠加）

看到 **「✓ 网页设计套件安装成功！」** 就搞定了。

### 第 4 步：重启 Claude Code

**必须重启**，CLAUDE.md 指令才会在新会话生效。

告诉用户：
> ✅ 网页设计套件已装好！请**重启 Claude Code**，重启后我就能按方法论设计网页了。

### 第 5 步：验证安装

重启后，让用户说：

```
帮我做个简单的产品落地页试试
```

如果你自动读取了 `~/.claude/web-design/网页设计方法论.md` 并开始问调性、分析需求 → 安装成功 ✅

---

## 🎯 使用方式（告知用户）

### 基本用法

直接说需求，AI 会自动按五步法设计：

```
帮我做一个 XX 产品的落地页，Linear 那种极简感
```

### 定义品牌（推荐）

建立统一视觉体系：

```
帮我定义品牌设计语言
```

AI 会引导填写品牌色、字体、调性，保存后以后做页面自动应用。

### 指定调性

从 12 个品牌参考库挑选风格：

```
我想要 Apple 那种大留白的高级感
```

可选品牌：Stripe / Linear / Vercel / Apple / Notion / Framer / Figma / Raycast / Cal / Nike / Spotify / Airbnb

---

## 🔄 如果没有原始安装包（手动安装）

用户如果拿不到原始安装包，你可以**手动执行安装步骤**：

### 手动第 1 步：复制设计大脑

```bash
cp -r "团队工具库路径/02_🛠️工具库/通用工具/网页设计套件/设计大脑" ~/.claude/web-design/
```

### 手动第 2 步：复制 skills（如果不存在）

先检测：

```bash
ls ~/.claude/skills/web-design-engineer/SKILL.md 2>/dev/null
ls ~/.claude/skills/frontend-design/SKILL.md 2>/dev/null
```

如果都不存在，复制：

```bash
cp -r "团队工具库路径/02_🛠️工具库/通用工具/网页设计套件/skills/web-design-engineer" ~/.claude/skills/
cp -r "团队工具库路径/02_🛠️工具库/通用工具/网页设计套件/skills/frontend-design" ~/.claude/skills/
```

### 手动第 3 步：写 CLAUDE.md 指令块

在 `~/.claude/CLAUDE.md` 末尾追加（用 `<!-- WEBDESIGN-BEGIN -->` / `<!-- WEBDESIGN-END -->` 包裹，重复装时先删旧块再写新块）：

```markdown
<!-- WEBDESIGN-BEGIN -->
## 网页设计套件

做网站/落地页/官网/H5 前，先读取 `~/.claude/web-design/网页设计方法论.md`，按五步法设计：

1. **定调性** — 问用户品牌调性，或从 12 个品牌参考库挑一个（Stripe/Linear/Apple等）
2. **借骨架** — 读对应品牌的 DESIGN.md，提取视觉语言和结构
3. **写文案** — 营销导向，参考 `网站撰写经验.md`
4. **执行** — 调用 `web-design-engineer` 或 `frontend-design` skill 编码
5. **自检** — 对照方法论里的"反 AI slop 清单"检查

**品牌定义**：引导用户填写 `定义你的品牌.DESIGN.md`，建立统一视觉。

**H5 页面**：参考 `H5页面设计规范.md` 的代码模板和技术规范。
<!-- WEBDESIGN-END -->
```

---

## 🐛 常见问题

### Q1: 安装引擎报错 / 找不到 node

**A**: 
```bash
# 找 node 路径
which node  # Mac/Linux
where node  # Windows

# 用完整路径跑
/完整路径/node 核心/install-core.js 核心
```

### Q2: 装完没生效

**A**: 99% 是没重启 Claude Code。CLAUDE.md 指令必须新会话才生效。

### Q3: 做页面时没按方法论来

**A**: 检查当前知识库的 `CLAUDE.md` 里有没有 `WEBDESIGN-BEGIN` 块。如果是在 Obsidian 知识库里工作，指令必须写进那个知识库的 `CLAUDE.md`（不是全局那个）。

### Q4: skills 没生效

**A**: 确认 `~/.claude/skills/web-design-engineer/SKILL.md` 和 `frontend-design/SKILL.md` 存在。

---

## 🆚 与其他工具的关系

### vs HTML 页面生成系统

| 特性 | 网页设计套件 | HTML 页面生成系统 |
|:---:|:---:|:---:|
| **重点** | 设计质量，从零创意 | 快速交付，套用预制风格 |
| **方法** | 五步法 + 品牌参考库 | 10 套 DESIGN.md 直接选 |
| **适用** | 品牌级页面、官网、重要落地页 | 活动页、推文页、快速原型 |

→ 可以配合：快速原型用 HTML 系统，精品设计用设计套件

---

## 📚 进阶使用

装好后，建议让 AI 深入阅读：

1. **`设计大脑/网页设计方法论.md`** — 总纲，必读
2. **`设计大脑/设计语言参考库/`** — 浏览 12 个品牌的 DESIGN.md，学习顶级设计语言
3. **`设计大脑/网站撰写经验.md`** — 营销文案实战技巧
4. **`设计大脑/H5页面设计规范.md`** — H5 技术规范和代码模板

---

## 🔄 更新套件

团队工具库更新后，重新运行安装引擎（第 3 步）即可覆盖旧版本。安装器是幂等的，不会重复叠加指令。

---

**创建者**：创业沙拉 · 大龙Jim  
**官网**：startupsalad.com/setup
