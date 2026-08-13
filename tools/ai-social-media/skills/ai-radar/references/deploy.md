# 连接模式接口契约 & 自托管完整版

## 连接模式：从运行中的「AI 情报站」实例取数

ai-radar skill 可以连到用户自己运行的 AI 情报站后端（FastAPI），直接复用它**已生成的报告**——这样 skill 输出和该用户的网站/邮件**完全同源**，且省去现场抓取与加工的时间。

### 触发条件

环境变量 `AI_RADAR_API` 指向后端根地址，例如：

```bash
export AI_RADAR_API=http://localhost:8000          # 本地运行
export AI_RADAR_API=https://intel.example.com      # 自有 VPS
```

### 接口契约（只读，无需认证）

| 端点 | 返回 | skill 用途 |
|---|---|---|
| `GET /api/reports?type={daily\|weekly\|monthly}&limit=1` | 报告元信息列表（倒序） | 取最新一份报告的 period_date |
| `GET /api/reports/{type}/{period}` | `{title, markdown, html, headline_analysis, stats, ...}` | 直接呈现 `markdown`（已是金字塔结构） |
| `GET /api/items?min_score=6&limit=60` | 已加工条目 `[{title,url,source,summary_zh,category,entities,importance_score}]` | lens≠pm 时按目标视角重新综合 |

period 格式：daily=`2026-06-12`，weekly=`2026-W24`（ISO 周），monthly=`2026-06`。

### 行为

1. **同视角（pm）**：直接取 `markdown` 呈现，零加工——最快、与网站字节级同源。
2. **换视角**：取 `/api/items`，按选定视角重新生成研报（视角细则见 SKILL.md 工作流引用的 lenses；数据同源、解读不同）。
3. **连不通**：任何超时/4xx/5xx → 自动降级独立模式，报告开头注明「实例未连通，已现场抓取」。绝不因为连接模式失败就报错退出。

---

## 自托管完整版（持续运行 + 邮件/IM 订阅）

skill 是**按需的即时研报**。如果用户想要 **7×24 自动运行 + 网站浏览 + 邮件/企业微信/Telegram 推送**，那是完整版「AI 情报站」应用的能力，不在 skill 范围内。指引用户：

- **GitHub 静态站（零服务器）**：仓库 `frontend/` + `.github/workflows/deploy.yml`，本地 `./publish.sh --gen` 生成 → push → 自动部署 GitHub Pages。在线 demo：https://songshishuang.github.io/ai-radar/
- **VPS 完整版（含订阅推送）**：仓库 `deploy/` 下 `docker compose up -d`，五容器（Caddy / Next.js / FastAPI+调度 / Postgres / RSSHub），跑定时管道 + 邮件/IM 分发。
- 两者都把 `AI_RADAR_API` 指过去后，本 skill 即进入连接模式与其同源。

> 一句话定位：**skill = 随手要一份研报；完整版 = 让它每天自己长出来并推给你。** 两者通过 `AI_RADAR_API` 衔接，数据同源。
