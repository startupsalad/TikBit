# ai-radar — AI 行业情报雷达

> 一句话要一份 AI 日报 / 周报 / 月报。替你**盯住国外核心 AI 主体**，在通稿泛滥里**拣出真信号**，宿主 agent 直接出中文金字塔研报。

![Agent Skill](https://img.shields.io/badge/Agent-Skill-7c5cff)
![License: MIT](https://img.shields.io/badge/License-MIT-22c55e)
![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-3776ab)
![dependencies: zero](https://img.shields.io/badge/dependencies-zero-0ea5e9)
![tests: 8/8](https://img.shields.io/badge/tests-8%2F8%20passing-22c55e)
![zero API key](https://img.shields.io/badge/API%20key-not%20required-f59e0b)

```bash
# 一行装（Claude Code）
cp -r ai-radar ~/.claude/skills/ai-radar
```

装好后说一句「**给我今天的 AI 日报**」即触发：脚本抓取 → agent 摘要 / 分类 / 评分 / 解读 → 一份 2 分钟读完的中文研报（⚡速览 → 🔥必读 → 📌关注 → 📚附录）。

| | |
|---|---|
| 👀 **先看产出** | [`samples/daily-sample.md`](samples/daily-sample.md) — 真实生成 59 条 + 5 个 PM 视角深度头条 |
| 🌐 **在线 demo** | https://songshishuang.github.io/ai-radar/ |
| 📦 **唯一依赖** | Python 3.8+（抓取脚本纯标准库，无需 `pip install`） |

## 凭什么不是又一个新闻聚合器

> 同类开源工具（如 6.6k★ 的 [Horizon](https://github.com/Thysrael/Horizon)）已把「抓取 → 摘要 → 推送」做得很卷，ai-radar 的差异在**编辑判断力**层——下面这几项同类少有系统化做：

| | 别的聚合器 | ai-radar |
|---|---|---|
| **① 信源置信度护栏** | LLM 摘要默认信源即真 | 二手聚合站 / 未证实传闻**降级、不进必读**——一条假必读比漏一条真新闻更糟 |
| **② 角色化多视角** | 人人同一份 | 同一批新闻按 **PM / 工程 / 投资 / 研究** 换评分权重与解读重点 |
| **③ 结论先行** | 摘要堆叠 | 金字塔结构，每条必读带**一句话结论 + 行动 + 原始来源** |
| **④ 盯主体 · 中文** | 泛搜英文关键词 | 追 OpenAI/Anthropic 等官方源 + 实体标注，**中文输出**（同类多英文优先）|

外加**双档覆盖**（轻档现抓零配置 / 重档连自建后端沉淀历史）与全程**零 API key**——摘要/分类/评分/深度解读全部由宿主 agent（它本身就是 LLM）直接完成，不调任何外部 LLM API。

## 用法

```
你：给我今天的 AI 日报
你：从工程师视角看这周的 AI 动态        # lens=engineer, range=weekly
你：这个月 AI 投资圈发生了什么          # lens=investor, range=monthly
你：只看大厂和开源，今天的             # categories=vendor,community
```

**参数**（从话语自动解析，都有默认值，不必显式指定）：

| 参数 | 取值 | 默认 | 说明 |
|---|---|---|---|
| `lens` | pm / engineer / investor / researcher | pm | 研报视角（改变评分加权与解读重点）|
| `range` | daily / weekly / monthly | daily | 时间窗 36h / 7d / 30d |
| `categories` | vendor / paradigm / community / media / social 子集 | 全部 | 来源大类过滤 |

## 安装

### Claude Code

```bash
# 一行装：自动复制到 skills 目录 + 清理开发文件
./install.sh

# 或手动 —— 个人：复制到 skills 目录
cp -r ai-radar ~/.claude/skills/ai-radar

# 团队：放进项目 .claude/skills/ 共享
mkdir -p .claude/skills && cp -r ai-radar .claude/skills/
```

重启 / 新开会话后，说「AI 日报」「今天 AI 有什么」即可触发。

### 其它 agent 工具

skill 是纯文件（SKILL.md + scripts + references），跨平台通用：

| 平台 | 安装路径 |
|---|---|
| Claude Code / Desktop | `~/.claude/skills/ai-radar/` |
| Cursor | `<project>/.cursor/skills/ai-radar/` |
| Codex / 其它 | 各自的 skills 目录 |

## 连接你自己的「AI 情报站」（可选，数据同源）

部署了完整版「AI 情报站」（定时管道 + 网站 + 邮件/IM 订阅）后，设环境变量即可让 skill 直接复用它已生成的报告：

```bash
export AI_RADAR_API=http://localhost:8000          # 或你的 VPS 域名
```

此后 skill 进入**连接模式**，输出与你的网站/邮件字节级同源。详见 [`references/deploy.md`](references/deploy.md)。完整版部署见主仓库 `deploy/`（VPS 五容器）或 `.github/workflows/`（GitHub Pages 静态站）。

## 自定义数据源

编辑 [`scripts/sources.json`](scripts/sources.json)：`enabled:false` 禁用某源；`method:dynamic` 的源由 agent 用 WebSearch 补抓（适合 X/Twitter 等无 RSS 的源）。

## 边界与安全

- `fetch.py` **只读抓取**：仅对源清单发 HTTP GET，不写文件、不执行任意命令、不外发数据。
- 落盘只在 `./ai-radar-reports/`，覆盖同名前先确认。
- **不做分发**（邮件/IM 是自托管完整版后端的事）；**不盲信用户喂的未证实信息**，须抓源核实。

## 测试

```bash
python3 tests/test_fetch.py      # 抓取器离线解析测试（8/8，零依赖）
```

工作流级 eval（4 题四件套：正常日报 / 视角切换 / 对抗诱饵 / 合规审核）见 [`tests/eval-prompts.md`](tests/eval-prompts.md)。

## 结构

```
ai-radar/
├── SKILL.md                  # 触发 + 双模式工作流 + 参数 + 边界与安全
├── scripts/
│   ├── fetch.py              # 自包含抓取器（stdlib 优先，零必装依赖）
│   └── sources.json          # 37 源清单
├── references/
│   ├── report-format.md      # 金字塔研报模板
│   ├── lenses.md             # 4 视角加权与解读重点
│   ├── deploy.md             # 连接模式契约 + 自托管指引
│   ├── compliance.md         # 内容合规审核清单（输出前必做）
│   └── jdme-card.md          # 日报→京ME 卡片推送格式
├── samples/
│   └── daily-sample.md       # 真实产出样本（59 条 + 5 深度头条）
├── assets/
│   └── sample-report.md      # 精简样例
├── tests/
│   ├── test_fetch.py         # 抓取器离线测试（8/8）
│   └── eval-prompts.md       # 工作流 eval（4 题四件套）
├── install.sh               # 一行装脚本
├── demo.tape                # vhs 录制脚本 → demo.gif
└── LICENSE                  # MIT
```

## License

[MIT](LICENSE) © 2026 songshishuang
