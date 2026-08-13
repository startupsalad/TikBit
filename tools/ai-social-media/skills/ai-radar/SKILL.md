---
name: ai-radar
description: >-
  AI 行业情报雷达：一句话要一份 AI 日报 / 周报 / 月报。替你盯住国外核心 AI 主体（OpenAI / Anthropic /
  Google / Meta / Mistral 等厂商官方源 + Hacker News + HuggingFace 论文与模型 + TechCrunch/The Verge 等
  行业媒体 + X 关键人物），在通稿泛滥里**按重要度拣出真信号**，由你（宿主 agent）直接做中文摘要、8 类分类、
  实体标注、1-10 评分，按 PM / 工程 / 投资 / 研究视角产出「结论先行 + 每条锚定原始来源」的金字塔研报，零 API key、
  零部署。当用户说「AI 日报 / 周报 / 月报」「今天 / 这周 AI 有什么」「最近 AI 动态」「AI 情报 / AI 资讯研报」
  「追踪 / 盯一下 AI 前沿」「AI radar」「大厂 AI 进展」「AI 圈发生了什么」，或想定期了解模型发布、开源项目、
  产研提效工具、行业产品与融资动态时，都应使用本 skill；即使没明说「研报」二字，只要意图是把分散英文 AI 资讯
  聚成一份 2 分钟读完的中文简报，也要触发，而不要自己漫无目的地搜索。不要用于：单条事实速查（如「Claude 上下文
  窗口多大」直接回答即可）、用户明确要以中文 / 国内 AI 源为主、或用户在开发 AI 产品 / 写代码（那是产品开发，不是情报聚合）。
---

# ai-radar — AI 行业情报研报生成器

把分散在几十个英文源里的 AI 动态，聚合成一份**结论先行、2 分钟读完**的中文研报。你（宿主 agent）本身就是 LLM——所以摘要、分类、评分、深度解读全部由你直接完成，**不需要任何 API key**。

## 核心理念

- **抓取靠脚本，思考靠你**：确定性的拉取/解析交给 `scripts/fetch.py`（自包含、零依赖），需要判断力的加工（中文摘要、重要度、视角解读）由你做。
- **结论先行**：读者要的是「这事对我意味着什么 + 我该做什么」，不是事件的逐字复述。正文极简，深度全文沉底到附录。
- **双模式**：能连到用户自己运行的「AI 情报站」就直接拉它**已生成的报告**（与其网站同源、最快）；连不到就本地现抓现做。

## 第一步：判断运行模式

检查环境变量 `AI_RADAR_API`（如 `https://songshishuang.github.io/ai-radar` 的后端，或 `http://localhost:8000`）：

- **设了 → 连接模式**（优先）：直接复用用户实例已生成的报告，省时且与其网站字节级同源。见下方「连接模式」。
- **没设 → 独立模式**：用内置脚本现场抓取 + 你来加工生成。见下方「独立模式」。

> 用户也可显式指定：「用独立模式」「不要连后端」→ 直接走独立模式。

## 参数

从用户话语里解析（都有合理默认，不必追问）：

| 参数 | 取值 | 默认 | 说明 |
|---|---|---|---|
| `range` | daily / weekly / monthly | daily | 对应时间窗 36h / 7d / 30d |
| `lens` | pm / engineer / investor / researcher | pm | 研报视角，详见 `references/lenses.md` |
| `categories` | vendor,paradigm,community,media,social 子集 | 全部 | 来源大类过滤 |

「AI 周报」→ range=weekly；「从工程师视角」→ lens=engineer；「只看大厂和开源」→ categories=vendor,community。

---

## 连接模式（AI_RADAR_API 已设）

1. 算出目标 period：daily→今天 `YYYY-MM-DD`、weekly→`YYYY-Www`（ISO 周）、monthly→`YYYY-MM`。
2. `GET {AI_RADAR_API}/api/reports/{type}/{period}`：
   - **命中**：拿到已生成报告的 `markdown` 字段，直接呈现给用户（它已是金字塔结构）。若拿不到精确 period，改用 `GET {AI_RADAR_API}/api/reports?type={type}&limit=1` 取最新一份。
   - **lens ≠ pm**：实例报告是 PM 视角。改为 `GET {AI_RADAR_API}/api/items?min_score=6&limit=60` 取已加工条目，按 `references/lenses.md` 的目标视角**重新综合**成研报（数据同源、视角不同）。
3. 连接失败（超时 / 4xx / 5xx）→ 自动降级到独立模式，并在报告开头注明「实例未连通，已现场抓取」。

---

## 独立模式（现抓现做）

### 1. 抓取（脚本）

```bash
python ai-radar/scripts/fetch.py --since 36h          # daily
python ai-radar/scripts/fetch.py --since 7d           # weekly
python ai-radar/scripts/fetch.py --since 30d          # monthly
# 可选：--categories vendor,community   --sources 自定义 sources.json
```

脚本裸 Python 3.8+ 即可跑（标准库优先；装了 `feedparser`/`httpx` 会自动用更鲁棒的路径）。它输出一段 JSON：

```json
{
  "items": [{"title","url","source","category","published_at","summary_raw","extra"}],
  "dynamic_sources": [{"name","query"}],
  "failed_sources": ["name: reason"],
  "stats": {"fetched","sources_ok","sources_failed","window_hours"}
}
```

> 输出可能很大（一天 100+ 条、近百 KB）。直接读 stdout 容易被截断，建议先落盘再解析：
> `python ai-radar/scripts/fetch.py --since 36h > /tmp/radar.json`，再读 `/tmp/radar.json`。

### 2. 补抓动态源（你的工具）

对 `dynamic_sources` 里的每一项（**X 核心人物组**、MCP Marketplace 等无 RSS 的源），用 **WebSearch** 按其 `query` 搜最近动态，挑出真有信息量的 1-3 条，补进条目池。**这是日报的固定输入、不是可选项** ⚠️——X 上核心人物（如 Anthropic 的 Cat Wu `@_catwu` / Dario Amodei、OpenAI 的 Sam Altman 等）的产品观点与行业表态，是 ai-radar 区别于纯 RSS 聚合的独特信号，最容易因「嫌麻烦」被跳过，**务必每期都补**。某人/某组本期无重要动态就如实跳过、并在尾注标「本期 X 无重要动态」——绝不编造、也不假装搜过。
> **补抓方法（提升覆盖）**：X 人物**分人单搜**——每位用「`<人名> <@handle> site:x.com` 近一周动态/观点」**单独搜一次**，不要一次按整组搜（实测组搜覆盖率低、12 人只命中 3）；优先盯最活跃的 **Altman / Dario Amodei / Karpathy / Hassabis**。WebSearch 对 X 原文覆盖有限是**已知局限**（X 封锁了免费抓取生态，官方 API $200+/月、nitter 实例多已挂），搜到就报、搜不到如实标，**不强求 12 人全覆盖**。

**信源置信度护栏**：WebSearch 回来的常混杂权威源（官方、知名作者）与二手聚合站（不知名 AI 资讯站、加密媒体转载）。**仅见于二手聚合站、无法回溯到一手来源的内容，至多进「值得关注」并标注「来源存疑」，不得进必读、不得作为深度分析依据**。重要度宁可压低也不要被未经证实的传闻拔高——一条假必读比漏一条真新闻伤害更大。

### 3. 加工（你来做，逐条）

对每条 `items`，生成：

- `summary_zh`：80-150 字中文摘要，**只讲发生了什么 + 为何重要**，不堆砌。
- `category`：8 类之一 —— `model-release`(模型发布) / `dev-tooling`(产研工具) / `agent-infra`(Agent基建) / `research`(前沿研究) / `opensource`(开源生态) / `product-launch`(产品动态) / `business`(商业资本) / `policy-safety`(政策安全)。按内容实质判断，别套用来源大类。
- `entities`：涉及的公司/产品/模型规范名（如 `OpenAI`、`Claude`、`DeepSeek-R1`），最多 5 个。
- `importance` 1-10：行业级大事 8-10；从业者该关注 5-7；常规 1-4。**按 lens 调权重**（见 `references/lenses.md`）。

去重：同一事件多源报道合并为一条，保留全部来源链接。

### 4. 生成研报（金字塔结构）

严格按 `references/report-format.md` 的模板产出，并套用 `references/lenses.md` 里选定视角的解读重点。核心结构：

```
☕ 阅读预算一行
## ⚡ 今日速览       —— 3 句话讲完今天
## 🔥 今日必读       —— ≥8 分 Top3-5，每条 3 行（标题 / ⚡so-what 结论 / 👉首要行动）
## 📌 值得关注       —— 6-7 分，每条 1 行
---
尾注：收录 N 条 · 其余见来源
## 📚 附录·深度解读   —— 必读条目的六段全文，沉底，想深入再看
```

### 5. 合规审核（输出前必做）

日报要**上公网站 + 推送内部 IM**、给同事看——呈现 / 落盘 / 分发**之前**必须过一轮合规审核（清单见 [`references/compliance.md`](references/compliance.md)）。重点核：**① 政治 / 地缘表述中立**（中美竞争 / 出口管制 / 监管 / 制裁类只客观陈述事实、不带立场、不渲染对立——AI 情报里最高频）② 不传未证实信息 ③ 导向正面、不渲染威胁论 / 失业恐慌 ④ 企业负面用「事实 + 来源」非主观贬低 ⑤ 人物动态只用公开信息。命中条目**改写中立化或降级 / 移除**——**合规优先于完整，宁可少一条不留风险**。通过后可在尾注标「· 已过合规审核」。

### 6. 输出

- 在对话里完整呈现研报。
- 默认落盘：`./ai-radar-reports/{range}-{period}.md`（便于用户归档/喂给其它工具）。
  **落盘统一用 shell 写文件**（`cat > 文件 <<'EOF' … EOF` 或等价方式），不要依赖 `Write` 工具——在子代理/受限场景下 `Write` 可能被拦截，shell 写文件则到处都能用。
- **分发到京ME（可选）**：用户要把日报推到京ME 时，按 [`references/jdme-card.md`](references/jdme-card.md) 的卡片格式（标题 / 红色主题 / 正文**每条挂超链接** / 「看完整日报」按钮 / 精简扫读版）压成 `params.json`，调 **`jdme-push`** skill 发送（它管凭证 / 内网 / 预览确认 / 回报终态）。**收件人由用户当场指定，绝不脑补**；其它 IM（企微 / 飞书 / 钉钉）同理类推。

---

## 降级与诚实

- 单源抓取失败由脚本隔离（`failed_sources`），不影响整体；在研报尾注如实标注失败/降级源数量。
- 信息不足（如周末资讯少）就如实说「本期信息较少」，不要为凑数拔高重要度。
- 时间敏感：published_at 缺失的条目保留但不假设其新鲜度。
- **全源失败兜底**：若 `fetch.py` 返回空 items 且动态源也抓不到，如实告知「本期未抓到新条目（数据源可能临时不可用）」，不要用旧知识编造"今天的"新闻。

## 边界与安全

本 skill 只读聚合公开信息，行为边界明确，便于你放心在任意项目里调用：

- `scripts/fetch.py` **只读抓取**：仅对源清单发 HTTP GET，不写任何文件、不执行任意命令、不外发用户数据。
- **落盘只在 `./ai-radar-reports/`**：写报告前若同名文件已存在，先告知用户、确认再覆盖。
- **不做分发**：skill 只产出研报，绝不声称已发邮件/已推送（那是自托管完整版后端的事）。
- **不盲信用户喂的未证实信息**：用户口头断言的"新闻"须经 fetch/WebSearch 抓源核实，抓不到权威来源则按信源置信度护栏降级处理。

## 资源索引

- `scripts/fetch.py` — 自包含抓取器（RSS/Atom + HN/HF/Reddit/GitHub Trending/GitHub Search）
- `scripts/sources.json` — 37 源清单，可增删（`enabled:false` 禁用，`method:dynamic` 交给你补抓）；含 `github_stars` 源（GitHub AI 项目雷达：日报=近 7 天新项目，周报=近 30 天动量项目，月报=高星且近 180 天活跃的基础设施项目；GitHub API 不提供真实 star 增量，周报用「短期创建 + 当前高星」做代理）+ 3 组 X 核心人物动态源（共 12 人）+ 厂商 blog（OpenAI/Anthropic/Google×3/AWS/MS/HF/Mistral/NVIDIA 等）。国内厂商（智谱/DeepSeek/Qwen/Moonshot 等）**无有效活跃官方英文 RSS**，靠 HF blog（其 org 发文）+ HN + 媒体间接覆盖（GLM/DeepSeek/Qwen 动态实测均能抓到）；ai-radar 定位国外源优先
- `references/report-format.md` — 金字塔研报模板与写作要点（生成前必读）
- `references/lenses.md` — 4 视角的评分权重与解读重点
- `references/deploy.md` — 连接模式接口契约 + 自托管完整版（邮件/RSS/网站）指引
- `references/compliance.md` — 内容合规审核清单（输出前必做：政治地缘中立 / 不传谣 / 导向正面 / 来源合规等）
- `references/jdme-card.md` — 日报 → 京ME 卡片推送格式（配合 `jdme-push` skill；其它 IM 类推）
- `assets/sample-report.md` — 一份样例输出
- `samples/daily-sample.md` — 真实产出样本（59 条 + 5 深度头条，看一眼产物长什么样）
- `tests/test_fetch.py` — 抓取器离线测试（覆盖 RSS/Atom、动态源路由、HF Spaces、GitHub 周期策略等）；`tests/eval-prompts.md` — 工作流 eval（4 题四件套：正常日报/视角切换/对抗诱饵/合规审核）
