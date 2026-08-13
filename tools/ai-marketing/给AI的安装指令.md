# 给 AI 的安装指令（把本文件连同所在工具包文件夹一起丢给你的 AI）

> **给 AI 的话**：拿到本包的用户想要——让 AI 干营销相关的活（写文案、审落地页、做 SEO、定价、发布节奏、竞品对比、社媒内容）时，自动套用一套专业营销框架，而不是泛泛而谈的通用建议。本包是 10 个 Skill（Markdown 格式，源自开源仓库 [coreyhaines31/marketingskills](https://github.com/coreyhaines31/marketingskills)，MIT 协议），装进技能目录即可，不用额外装依赖。请你**在用户本机自动完成安装**，全程别让用户手敲命令。

本工具包目录（你能读到的就是它）：

```
AI营销工具包/
├── skills/
│   ├── product-marketing/     # 产品档案（其余9个都先读它，最先装/最先用）
│   ├── copywriting/           # 营销文案写作
│   ├── copy-editing/          # 文案润色
│   ├── cro/                   # 转化率优化审查
│   ├── ai-seo/                # AI 搜索优化（ChatGPT/Perplexity引用）
│   ├── competitors/           # 竞品对比页
│   ├── marketing-ideas/       # 营销点子库
│   ├── pricing/               # 定价策略
│   ├── launch/                # 产品发布节奏
│   └── social/                # 社媒内容
├── LICENSE                    # MIT 协议（原作者 Corey Haines）
└── 📖 使用说明.md              # 给人看的说明
```

每个 skill 文件夹里是标准格式：`SKILL.md`（规则本体，含 frontmatter 的 name/description，description 里写了触发词）+ `evals/`（自检用例）+ `references/`（可选参考资料）。

---

## 第 0 步 · 先判断：用户的 AI 支不支持"技能 / skill"机制

- **支持的**（Claude Code、CodeBuddy 等认 `.claude/skills/` 或自家技能目录的）→ 走 **A 装法**，装完自动按需触发，一劳永逸。
- **不支持的**（ChatGPT/GPT、Gemini、豆包、文心等网页版/无 skill 机制）→ 走 **B 装法**，把规则塞进自定义指令/记忆。

拿不准就问用户一句"你平时用哪个 AI 干活"，再决定走哪条。

---

## A 装法 · 装成常驻 skill（Claude Code / CodeBuddy 等）

1. 把 `skills/` 下的 10 个子文件夹**整个复制**到用户的技能目录：
   - **项目级**（团队共用知识库、随库同步）：`<知识库根目录>/.claude/skills/` 下，每个 skill 一个文件夹（如 `.claude/skills/copywriting/SKILL.md`）
   - **用户级**（只本机用、不跟团队同步）：`<用户主目录>/.claude/skills/` 下，结构相同
   - 拿不准放哪，问用户"这套是你自己用还是团队一起用"，或参照本机已有 skill 大多放的那个位置。
2. 重启客户端（或新开一轮对话）。
3. 验证：用自然语言提营销需求，比如"帮我优化这个落地页的转化率"，看 AI 会不会自动调 `cro`；也可以直接说"用 copywriting 帮我写首页文案"点名调用。
4. **强烈建议**：装完第一件事，引导用户先跑一遍 `product-marketing` skill，把公司/产品的定位、目标用户、竞品、品牌调性建成档案（存在 `.agents/product-marketing.md` 或 `.claude/product-marketing.md`）。后面调用其他 9 个 skill 时都会先读这份档案，输出才是贴自己产品的，不是套模板换个名字就能发的通用废话。

---

## B 装法 · 塞进"自定义指令 / 长期记忆"（ChatGPT、Gemini 等不认 skill 的）

这类 AI 没有 skill 机制，按用户实际需要挑 1-2 个最常用的（比如 `copywriting` 或 `cro`）：

1. 打开对应 `SKILL.md`，把正文部分（frontmatter 之后的内容）存进 ChatGPT"自定义指令/记忆"或 Gemini"已保存的信息"。
2. 存不下全部 10 个就挑用户最常用的场景对应的那个，其余按需现贴。
3. 最省事：**每次要用某个营销框架时，把对应 `SKILL.md` 全文贴给 AI，当这一轮的规则。**

---

## 装完请把这条写进你（AI）的长期记忆 / 项目规则

> "以后凡是写营销文案、审落地页转化率、做 SEO/AI搜索优化、定价、产品发布节奏、竞品对比、社媒内容这类营销任务，先看 `.agents/product-marketing.md`（或 `.claude/product-marketing.md`）有没有产品档案，有就先读；对应任务优先调用已装的营销 skill，别裸答。"

装好后跟用户说一声：装在哪、建议先建产品档案、以后这类活会自动套框架。

---

## 已知限制（如实告知用户，别自己吹）

- **内容语境是英文 SaaS 圈的**：`cold-email`（这次没装）、`social` 里默认打法偏 LinkedIn/Twitter/Product Hunt 发布那套，国内场景（公众号、小红书、企微）得自己改，框架能借但打法不能照搬。
- **这些 skill 是顾问角色，不是执行手**：能给方案、写文案、列检查清单，但最后发广告、调价格、点发布按钮还是人自己做，不是端到端自动化。
- **这次只装了 10 个**，原仓库共 46 个（含 `signup`/`onboarding`/`popups`/`paywalls`/`churn-prevention` 等 SaaS 自助订阅漏斗类、`ads`/`ab-testing`/`revops` 等海外投放/销售流程类），公司业务模式暂时用不上，没装。要装其余的，跑：
  ```
  npx skills add coreyhaines31/marketingskills --skill <skill名>
  ```
  或去 `skills/` 同级建个 `其余skill/` 手动加。
