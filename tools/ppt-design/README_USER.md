# PPT 制作工具包 - 用户说明

> **📌 给人看的简明使用指南**

---

## 这是什么

一个完整的 PPT 制作系统，包含 62 种品牌风格（Apple、Claude、Notion、Stripe、Linear、Tesla 等）+ 标准工作流 + 多模式生成引擎。

**核心特点**：
- 🎨 **DEMO 先行**：先生成 1-2 页风格预览，确认后再批量制作（不是做好再换风格）
- 🎯 **智能推荐**：根据内容自动匹配 5 种合适的品牌风格
- 📦 **多格式输出**：HTML（在线演示）/ PPTX（可编辑）/ PDF（归档）
- 🤖 **AI 全自动**：你只需要说"做 PPT"，AI 自动执行完整流程

---

## 快速开始

### 第 1 步：安装

把本工具包下载后，跟你的 AI 说：

```
帮我安装这个 PPT 制作工具包，读一下 README_AI_INSTALL.md
```

AI 会自动：
- 安装 8 个 skills 到 `.claude/skills/`
- 复制工具脚本到工作目录
- 配置 CLAUDE.md
- 安装 Python 依赖（可选）

**⚠️ 重要**：如果你要用 GPT 生图功能（A 模式），需要自己配置 OpenAI API 密钥。其他模式（B/C/D/E/F/G）不需要密钥。详见 `README_AI_INSTALL.md` 第 4 步。

### 第 2 步：使用

安装完成后，直接跟 AI 说：

```
帮我做个产品发布会 PPT，12 页
```

AI 会自动执行标准工作流：
1. **Phase 1**：出框架确认（每一页内容是什么）
2. **Phase 2**：推荐 3-5 种风格 + 生成 DEMO（每种 1-2 页）
3. **Phase 3**：你选风格后批量制作全套
4. **Phase 4**：交付 HTML / PPTX / PDF

---

## 典型使用场景

### 场景 1：没明确风格（AI 推荐）

```
你："做个技术分享 PPT，10 页"

AI 执行：
Phase 1: 出框架（功能/技巧/最佳实践）
Phase 2: 推荐 5 种风格：
  1. Vercel（推荐，现代极简）
  2. Cursor（科技感）
  3. Linear（商务现代）
  4. Warp（开发者风格）
  5. 智能匹配（AI 直接选最合适的）
  + 生成每种的 DEMO（1-2 页）
  
Phase 3: 你选"Vercel" → AI 批量制作全套
Phase 4: 交付 deck.html（在线演示）
```

### 场景 2：已有风格倾向

```
你："做个融资 PPT，用 Tesla 风格，15 页"

AI 执行：
Phase 1: 出框架（问题/方案/市场/团队/融资计划）
Phase 2: 推荐 3 种：
  1. Tesla（你说的）
  2. Apple（相近风格）
  3. Linear（商务备选）
  + 生成 DEMO
  
Phase 3: 你确认 Tesla → 批量制作
Phase 4: 交付 .pptx（可编辑，供投资方标注）
```

### 场景 3：指定特殊模式

```
你："做个品牌发布 PPT，要杂志风，Monocle 那种"

AI 判定：杂志风 → E 模式（guizang-ppt）
Phase 1: 出框架
Phase 2: 瑞士国际主义 / 电子杂志两种风格 DEMO
Phase 3: 你选瑞士 → 批量制作
Phase 4: 交付单文件 HTML（横滑翻页，高设计感）
```

### 场景 4：文档转换

```
你："把这份 50 页财务报告转成 PPT"

AI 判定：PDF → F2 工具（ultimate-ppt-master）
执行：多步采集 → 表格识别 → LLM 精炼 → 生成大纲 + 逐字稿
交付：.pptx（可编辑）+ HTML（在线演示）+ 逐字稿 TXT
```

---

## 支持的 62 种品牌风格

**科技 / AI**：
Apple、Claude、Cursor、ElevenLabs、Figma、Framer、Lovable、Meta、MiniMax、Mintlify、Mistral、Notion、Ollama、OpenCode、PostHog、Raycast、Replicate、Resend、Runway、Sanity、Sentry、Supabase、Superhuman、Together AI、Vercel、VoltAgent、Warp、Webflow、X.AI、Zapier

**开发者工具**：
Airtable、Cal.com、Clay、ClickHouse、Cohere、Composio、Expo、HashiCorp、IBM、Intercom、Linear、Miro、MongoDB、NVIDIA、Pinterest、Stripe

**金融 / 商业**：
Binance、Coinbase、Kraken、Revolut、Wise

**汽车 / 消费品**：
Airbnb、BMW、Ferrari、Lamborghini、Nike、Renault、Shopify、SpaceX、Spotify、Tesla、Uber

完整风格库：`.claude/skills/space-multi-design-ppt/references/brand-registry.md`

---

## 输出格式

| 格式 | 适合场景 | 说明 |
|:---:|:---:|:---:|
| **HTML** | 在线演示 / 分享链接 | 单文件网页，键盘翻页，全屏模式，无需安装软件 |
| **PPTX** | 二次编辑 / 正式交付 | 原生可编辑，PowerPoint / Keynote 打开 |
| **PDF** | 归档 / 发送 / 打印 | 固定版式，不可编辑 |

**默认输出 HTML**（除非你明确说要 PPTX）

---

## 五模式 + F 工具 + G 引擎

工具包内置完整的模式体系：

| 模式 | 场景 | 输出 |
|:---:|:---:|:---:|
| **A** | 一次性路演 / 视觉冲击 | GPT-Image 底图 + 文字层 |
| **B** | 标书 / 年度方案 / 客户会改 | python-pptx 原生可编辑 |
| **C** | 在线演讲 / 演讲者模式 / 47 种动画 | HTML slides + 逐字稿 + 计时器 |
| **D** | 学术论文 / 多代理评审 / 数字可溯源 | 多代理工作流 + 独立评审 |
| **E** | 杂志风 / 瑞士国际主义 / 高设计感 | 单 HTML 文件 + 横滑翻页 |
| **F1** | 简单文档 → PPTX | 快速模板转换（<1000 字） |
| **F2** | 复杂文档 → 多格式 | LLM 精炼 + PPTX + HTML + 逐字稿 |
| **G** | **品牌风格引擎（默认）** | **62 种品牌 + 智能推荐 + DEMO 先行** |

AI 会根据你的需求自动选择最合适的模式，你不需要记住这些。

---

## 标准工作流

```
用户："帮我做 XXX 的 PPT"
  ↓
【Phase 1 框架确认】
  AI 出：需求解析 + 大纲框架（每一页内容）
  用户确认 ✓
  ↓
【Phase 2 风格 DEMO】
  情况 A：用户已有风格倾向
    → AI 推荐 3 种相关风格
    → 生成每种的 DEMO（1-2 页）
  
  情况 B：用户未明确风格
    → AI 推荐 5 种匹配风格 + 智能匹配
    → 生成 3-4 种 DEMO
  
  默认输出 HTML
  用户选择一个 ✓
  ↓
【Phase 3 批量制作】
  AI 拉取品牌 DESIGN.md
  按大纲逐页生成
  可选：用户明确要 GPT 生图才调用
  ↓
【Phase 4 交付】
  交付文件 + 使用说明
  询问是否需要调整 / 换格式 / 补页
```

**关键点**：
- ✅ DEMO 必须真做（不是口头描述）
- ✅ DEMO 不超过 4 种（太多难选）
- ✅ 默认 HTML（除非明确要 PPTX）
- ✅ GPT 生图按需（明确要视觉冲击才调）

---

## 常见问题

**Q：安装需要多久？**
A：AI 自动安装，1-2 分钟完成（取决于网络速度）

**Q：不会代码也能用吗？**
A：完全可以。你只需要跟 AI 说"做 PPT"，AI 全自动执行

**Q：可以换风格吗？**
A：可以。在 Phase 2 DEMO 阶段换，或者做完后说"换成 XXX 风格重新渲染"

**Q：生成的 PPT 可以编辑吗？**
A：HTML 格式改代码；PPTX 格式用 PowerPoint 直接改

**Q：GPT 生图会自动调用吗？**
A：不会。只有你明确说"要视觉冲击" / "要炫酷" / "第 X 页用 GPT 生图"才调用

**Q：支持哪些 AI？**
A：Claude Code、Codex、Cursor、GPT 等兼容 Agent Skills 协议的 AI

**Q：可以分享给同事吗？**
A：可以。直接把整个工具包文件夹发给他，让他的 AI 读 `README_AI_INSTALL.md` 自动安装

---

## 文件结构

```
PPT制作工具包/
├── README_AI_INSTALL.md           # AI 自动安装指令（给 AI 看）
├── README_USER.md                 # 本文件（给人看）
├── CLAUDE.md片段.txt              # 配置片段
├── skills/                        # 8 个 skills
│   ├── space-multi-design-ppt/    # G 引擎（62 种品牌风格）★
│   ├── allaction-ppt-design/      # 五模式决策树
│   ├── html-ppt/                  # C 模式（HTML slides）
│   ├── slide-maker/               # D 模式（多代理评审）
│   ├── guizang-ppt/               # E 模式（杂志风）
│   ├── ppt-master/                # F1 工具（简单转换）
│   ├── ultimate-ppt-master/       # F2 工具（复杂转换）
│   └── huashu-design/             # 设计资源库
├── 工具脚本/
│   ├── GPT工具包/                 # A 模式（GPT 出图）
│   └── 可编辑PPT版式库/           # B 模式（python-pptx）
└── 流程文档/                      # 9 份整合文档（给 AI 读）
```

---

## 进阶用法

### 混搭风格

```
"用 Claude 配色 + Linear 排版，做个产品介绍"
```

### 指定页面 GPT 生图

```
"做个融资 PPT，用 Tesla 风格，第 3/5/8 页用 GPT 生图"
```

### 同时输出多格式

```
"用 Notion 风格生成 HTML 和 PPTX"
```

### 指定演讲者模式

```
"做个技术分享，要演讲者模式和逐字稿"
→ AI 自动用 C 模式（html-ppt）+ presenter-mode-reveal 模板
```

---

## 技术支持

遇到问题先检查：
1. AI 是否读取了 `README_AI_INSTALL.md`
2. Skills 是否安装成功（`.claude/skills/` 下有 8 个文件夹）
3. CLAUDE.md 是否追加了配置

仍有问题，查看详细文档：
- 标准工作流：`流程文档/ppt-workflow-standard.md`
- 五模式决策树：`流程文档/ppt-five-mode-complete-integration.md`
- G 引擎使用说明：`skills/space-multi-design-ppt/SKILL.md`

---

**开始使用吧 🎯**

跟你的 AI 说："帮我做个 XXX 的 PPT"
