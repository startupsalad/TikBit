# PPT 制作工具包 - 总览

> **📦 完整的 AI 驱动 PPT 制作系统**
> 
> 版本：v1.0.0 | 发布日期：2026-07-16

---

## 快速导航

| 文档 | 用途 | 适合谁 |
|:---:|:---:|:---:|
| **README_USER.md** | 使用说明 | 👤 人类用户 |
| **README_AI_INSTALL.md** | 自动安装指令 | 🤖 AI 助手 |
| **VERSION.md** | 版本记录 | 📋 维护者 |
| **CLAUDE.md片段.txt** | 配置片段 | ⚙️ 集成时用 |

---

## 工具包结构

> **📦 内容打包说明**：skills 里两个 ppt-master 系各带上万 SVG 图标，整包 2.5 万+ 碎文件散着经微盘/网盘同步易漏传。所以**内容目录全部压进 `PPT制作工具包_核心内容.zip`**，说明文件留在顶层明文。AI 安装时按 `README_AI_INSTALL.md` 第 0 步先解压。

```
PPT制作工具包/
│
├── 📄 README.md                   # 总览文档（本文件）
├── 📄 README_USER.md              # 用户使用说明（给人看）
├── 📄 README_AI_INSTALL.md        # AI 自动安装指令（给 AI 看）
├── 📄 VERSION.md                  # 版本记录
├── 📄 安全须知_API密钥.md         # 密钥安全
├── 📄 CLAUDE.md片段.txt           # CLAUDE.md 配置片段
├── 📄 工具包制作工作记录.md       # 制作记录
│
└── 📦 PPT制作工具包_核心内容.zip  # 🔑 核心内容包（AI 装前第 0 步解压）
        └─ 解压后还原出 ↓
           │
           ├── 📁 skills/ (8 个)              # AI Skills 集合
           │   ├── space-multi-design-ppt/   # ★ G 引擎（62 种品牌风格）
           │   ├── allaction-ppt-design/     # 五模式决策树
           │   ├── html-ppt/                 # C 模式（HTML slides）
           │   ├── slide-maker/              # D 模式（多代理评审）
           │   ├── guizang-ppt/              # E 模式（杂志风）
           │   ├── ppt-master/               # F1 工具（简单转换）
           │   ├── ultimate-ppt-master/      # F2 工具（复杂转换）
           │   └── huashu-design/            # 设计资源库
           │
           ├── 📁 工具脚本/                   # Python 脚本集合
           │   ├── GPT工具包/                # A 模式（GPT 出图）
           │   └── 可编辑PPT版式库/          # B 模式（python-pptx）
           │
           ├── 📁 流程文档/ (9 份)            # 整合文档（给 AI 读）
           │   ├── ppt-workflow-standard.md
           │   ├── ppt-five-mode-complete-integration.md
           │   └── ...（G/C/D/E/F1/F2/设计资源库整合文档）
           │
           └── 📁 编辑风HTML版式库/           # 34 套编辑风 HTML 版式
```

---

## 核心能力

### 1. 品牌风格引擎（62 种）

**科技 / AI**（30 种）：
Apple、Claude、Cursor、ElevenLabs、Figma、Framer、Lovable、Meta、MiniMax、Mintlify、Mistral、Notion、Ollama、OpenCode、PostHog、Raycast、Replicate、Resend、Runway、Sanity、Sentry、Supabase、Superhuman、Together AI、Vercel、VoltAgent、Warp、Webflow、X.AI、Zapier

**开发者工具**（16 种）：
Airtable、Cal.com、Clay、ClickHouse、Cohere、Composio、Expo、HashiCorp、IBM、Intercom、Linear、Miro、MongoDB、NVIDIA、Pinterest、Stripe

**金融**（5 种）：
Binance、Coinbase、Kraken、Revolut、Wise

**汽车 / 消费品**（11 种）：
Airbnb、BMW、Ferrari、Lamborghini、Nike、Renault、Shopify、SpaceX、Spotify、Tesla、Uber

### 2. 标准工作流

```
Phase 1: 框架确认
  - 需求解析
  - 大纲结构
  - 用户确认 ✓

Phase 2: 风格 DEMO
  - 推荐 3-5 种匹配风格
  - 生成每种的 1-2 页预览
  - 用户选择 ✓

Phase 3: 批量制作
  - 拉取品牌 DESIGN.md
  - 按大纲逐页生成
  - 可选 GPT 生图

Phase 4: 交付
  - HTML / PPTX / PDF
  - 使用说明
  - 后续调整
```

### 3. 多模式体系

| 模式 | 场景 | 输出 | 触发词 |
|:---:|:---:|:---:|:---:|
| **G** | 品牌风格驱动（**默认**） | HTML / PPTX / PDF | "用 XX 风格" / "智能推荐" |
| **A** | 视觉冲击 / 讲故事 | GPT-Image + 文字层 | "视觉炸" / "讲故事" |
| **B** | 标书 / 客户会改 | python-pptx 可编辑 | "标书" / "客户会改" |
| **C** | 在线演讲 / 演讲者模式 | HTML + 逐字稿 + 47 动画 | "演讲" / "逐字稿" |
| **D** | 学术 / 多代理评审 | 独立评审 + 源追踪 | "数字有来源" / "评审" |
| **E** | 杂志风 / 高设计感 | 单 HTML 横滑翻页 | "杂志风" / "Monocle" |
| **F1** | 简单文档转换 | 快速 PPTX | PDF/DOCX < 1000 字 |
| **F2** | 复杂文档转换 | PPTX + HTML + 逐字稿 | PDF/DOCX > 2000 字 |

### 4. 多格式输出

| 格式 | 特点 | 适合场景 |
|:---:|:---:|:---:|
| **HTML** | 单文件网页，键盘翻页，全屏，总览 | 在线分享，技术演讲，无需软件 |
| **PPTX** | 原生可编辑，PowerPoint / Keynote | 二次编辑，正式交付，客户标注 |
| **PDF** | 固定版式，不可编辑 | 归档，发送，打印 |

---

## 使用方式

### 同事或外部用户

1. **下载本工具包**（整个文件夹，注意确认 `PPT制作工具包_核心内容.zip` 下载完整）
2. **跟 AI 说**："帮我安装这个 PPT 制作工具包，读一下 README_AI_INSTALL.md"
3. **AI 自动执行**：
   - **第 0 步：解压核心内容 zip**（还原 skills/ 等目录）
   - 安装 8 个 skills
   - 复制工具脚本
   - 配置 CLAUDE.md
   - 安装依赖（可选）
4. **开始使用**："帮我做个 XXX 的 PPT"

### AI 助手

1. **读取** `README_AI_INSTALL.md`
2. **执行安装步骤**（7 步自动化流程）
3. **读取** `流程文档/*.md` 建立工作记忆
4. **响应用户**："做 PPT"触发标准工作流

---

## 典型案例

### 案例 1：产品发布会（无明确风格）

```
用户："做个 TikBit 产品发布会 PPT，12 页"

AI 执行：
Phase 1: 框架（问题/方案/案例/行动号召）
Phase 2: 推荐 Apple/Tesla/Linear/Vercel/智能匹配
        生成 3 种 DEMO
Phase 3: 用户选 Apple → 批量制作
Phase 4: 交付 deck.html
```

### 案例 2：技术分享（指定风格）

```
用户："用 Claude 风格做个技术分享，要演讲者模式"

AI 执行：
Phase 1: 框架（技巧/最佳实践）
Phase 2: Claude/Cursor/Vercel 三种 DEMO
Phase 3: 用户选 Claude → C 模式（演讲者模式）
Phase 4: 交付 HTML + 逐字稿
```

### 案例 3：融资方案（标书）

```
用户："做融资方案 PPT，客户会改字段"

AI 判定：标书 → B 模式（python-pptx 可编辑）
Phase 1: 框架（市场/产品/团队/融资计划）
Phase 2: IBM/Stripe/Linear 三种 DEMO
Phase 3: 用户选 IBM → 批量制作
Phase 4: 交付 .pptx（原生可编辑）
```

---

## 安装要求

**必需**：
- AI 环境（Claude Code / Codex / Cursor）
- 写权限（skills 目录和工作目录）

**可选**：
- Python 3.x + pip（A/B 模式）
- Node.js + npm（G 引擎 getdesign.md）
- Playwright/Chromium（PDF 导出）

---

## 技术架构

```
用户请求 "做 PPT"
    ↓
【入口】space-multi-design-ppt (G 引擎)
    ↓
【路由】allaction-ppt-design (决策树)
    ↓
【执行】A/B/C/D/E 模式 or F1/F2 工具
    ↓
【输出】HTML / PPTX / PDF
    ↓
【交付】用户确认
```

**决策优先级**：
E（杂志风）> D（多代理）> C（HTML）> B（可编辑）> A（GPT）> G（品牌风格）> F（文档转换）> 默认 B

---

## 更新记录

- **v1.0.0** (2026-07-16) - 首次发布

---

## 联系方式

- 制作方：立即行动科技（创业沙拉）
- 内部使用 + 合作伙伴分发

---

**开始使用 🎯**

跟你的 AI 说："帮我安装 PPT 制作工具包"

