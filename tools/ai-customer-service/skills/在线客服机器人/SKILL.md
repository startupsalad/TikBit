---
name: 在线客服机器人
description: 为网站部署基于 Claude API 的在线客服机器人。基于配套「参考实现」（Node.js 后端 + 前端聊天窗口 + Docker/Nginx 部署），引导用户完成需求对齐、知识库整理、配置、部署与验证。适用于产品官网、文档站、H5 页面等需要智能在线答疑的场景。触发词：在线客服、网站机器人、智能问答、在线答疑、部署客服、AI 客服。
---

# 在线客服机器人部署 skill

为一个网站（产品官网、使用说明书、文档站、H5 活动页等）部署基于 Claude API 的智能在线客服机器人。访客点击页面右下角悬浮按钮即可打开聊天窗口，输入问题获得基于知识库的即时回答。

本 skill 是「AI 客服工具包」的能力核心。工具包已内置一套**改配置就能跑的参考实现**（`参考实现/` 目录），你的主要工作是引导用户对齐需求、整理知识库、填配置、部署验证，**不用从零手写代码**——优先用参考实现，别再把整段代码贴进对话。

## 什么时候用

- 用户说「给这个网站加个在线客服」「做个智能问答」「部署个聊天机器人」。
- 已有一个 HTML 页面/网站，想加上实时答疑功能。
- 需要把产品文档、使用手册、FAQ 做成可对话的客服系统。

## 参考实现在哪

工具包 `参考实现/` 目录（相对本 skill 上层）：
- `backend/` — Node.js 原生后端（零依赖）：`server.js`（`spawn` 调本机 claude CLI + 单 IP 限流 + 每日算力预算封顶 + 并发上限）+ `src/knowledge.js`（知识库加载）。
- `frontend/chatbot-widget.js` — 自注入聊天窗口，一行 `<script>` 引入，发 `{q}` 收 `{answer}` 单轮。
- `deploy/` — Dockerfile（装 claude CLI + 预种免 onboarding）+ docker-compose + Nginx 反代 + 一键部署脚本。

> 架构复刻了创业沙拉自己 ai.salad.co/guide 跑通的在线答疑那套：后端不碰密钥，靠容器内 claude CLI（配 tikbit）完成鉴权。

配套文档：`docs/[AI客服工具包] 部署手册·公开版.md`（完整步骤）、`知识库准备指南.md`、`踩坑与避坑手册.md`、`【安全须知】API密钥与鉴权基线.md`。

## 第一步：需求收集（必做，别跳）

参照 `docs/[AI客服工具包] 知识库准备指南.md`，跟用户对齐四件事（缺一样都可能白做）：

| 项 | 问什么 | 用途 |
|:---|:---|:---|
| **给谁用** | 内部同事还是外部访客？ | 定回答口吻和深浅 |
| **答什么** | 最想答哪类问题？能举 3-5 个真实例子吗？ | 构造知识库、设边界 |
| **拿什么答** | 有哪些现成资料（FAQ/手册/话术）？哪份最权威？ | 填知识库 |
| **在哪里用** | 哪个网站/页面？域名是什么？ | 定 Nginx 反代前缀、前端嵌入位置 |

再确认部署环境：有没有能装 Docker 的服务器（公网 IP）、网站是不是 Nginx 托管、有没有 API Key（没有引导去创业沙拉 tikbit 中转站获取 https://tikbit.ai/，国内直连免梯子、兼容 Claude API）。

## 第二步：整理知识库

把用户给的资料整成 FAQ 问答对，写成 `.md` 放进 `参考实现/backend/knowledge-base/`（删掉示例 `kb.example.md`）。

- **FAQ 问答对最好用**，命中率最高；一个主题一个文件。
- 控制总量 ≤ 1 万字（约 20000 字符），超出会被后端截断并告警。
- 明确边界：不希望它答的（如具体报价、竞品对比），在知识库里写清「这类问题请联系人工客服」。

格式细节见 `backend/knowledge-base/知识库格式说明.md`。

## 第三步：填配置

引导用户 `cp 参考实现/backend/.env.example 参考实现/backend/.env`，帮他填：

| 配置项 | 填什么 | 备注 |
|:---|:---|:---|
| `ANTHROPIC_AUTH_TOKEN` | 用户自己的 tikbit 令牌（https://tikbit.ai/ 后台「令牌管理」） | **绝不硬编码进代码，绝不用别人的**；交给容器内 claude CLI 用 |
| `ANTHROPIC_BASE_URL` | 默认 `https://tikbit.ai`（走中转站），一般不用改 | |
| `CLAUDE_MODEL` | claude CLI 短名：`haiku`（快省，默认）/ `sonnet` / `opus` | |
| `DAILY_BUDGET_USD` / `IP_PER_MIN` / `IP_PER_DAY` | 每日算力封顶 + 单 IP 限流，按承受度调 | 防被刷爆，有默认值 |
| `BOT_NAME` / `API_PATH` / `FALLBACK_MSG` | 按需，有默认值 | |

**安全红线**：填好的 `.env` 只在用户服务器上，绝不提交仓库、绝不外发、绝不出现在你给用户的任何可分享内容里。

## 第四步：部署后端

引导执行（在服务器 `参考实现/deploy` 目录下）：

```bash
bash scripts/deploy.sh
```

脚本会自检配置、构建镜像、起容器（后端默认绑 `127.0.0.1:8770`，不直接暴露公网）、做健康检查。看到 `✅ 部署成功` 即可。失败带用户看 `bash scripts/logs.sh`，对照 `踩坑与避坑手册.md` 排查。

## 第五步：配 Nginx + 嵌前端

1. **Nginx 反代**：把 `deploy/nginx/chatbot.conf` 的 `location /guide-api/` 块加进用户站点的 Nginx 配置（同域名那个 `server{}`），改好接口前缀，然后 `nginx -t && nginx -s reload`。
2. **前端嵌入**：把 `frontend/chatbot-widget.js` 传到网站可访问目录，在页面 `</body>` 前加一行：
   ```html
   <script src="/assets/chatbot-widget.js"
           data-api="/guide-api/ask"
           data-title="在线咨询"
           data-fallback="咨询暂时连不上，请稍后再试或联系我们。"></script>
   ```
   **路径三处要一致**：`data-api` = Nginx 前缀 + 后端 `API_PATH`（见踩坑手册 #3）。详见 `frontend/集成说明.md`。

## 第六步：验证与交付

- 浏览器打开网站，点右下角 💬 提问，验证能收到回复；查 Network 面板确认接口 200。
- 异常对照 `踩坑与避坑手册.md`（404 路径没对上 / 一直走兜底=令牌错或 CLI 没装好 / "咨询有点忙"=触发限流或每日预算封顶 / 502 后端没起来）。
- 交付话术：告知用户「改知识库 → `cd deploy && bash scripts/update.sh`」「看日志 → `bash scripts/logs.sh`」，并说明限流+每日预算防线已开好。

## 常见问答

**Q：知识库内容太长怎么办？**
A：① 提取关键信息删废话；② 用 FAQ 问答对代替长文；③ 控制在 1 万字内，超出影响响应速度和成本。

**Q：能记住上下文吗？**
A：当前单轮问答（每次独立回答，和创业沙拉自己的在线答疑一致），简单稳、成本可控。需要多轮可后续扩展。

**Q：回答质量不好怎么办？**
A：① 优化知识库、补高频问题；② 调 `BOT_NAME` 和知识库里的风格说明；③ 换 sonnet/opus 模型（更强但更贵）。

**Q：能部署多个机器人吗？**
A：能。每个用不同端口（8770/8771…）、不同 Nginx 前缀（`/guide-api/`、`/product-api/`），照流程重复。

**Q：安全吗？会被刷爆 tikbit 额度吗？**
A：令牌锁在 claude CLI 那层不下发前端；后端开了单 IP 限流 + 全站每日算力预算封顶 + 并发上限，到顶自动降级，正常配置不会。详见 `【安全须知】API密钥与鉴权基线.md`。

**Q：能换模型吗？**
A：改 `.env` 的 `CLAUDE_MODEL`（claude CLI 短名 haiku/sonnet/opus）即可，知识库和前端通用。

## 关联

- 参考实现：工具包 `参考实现/` 目录
- 完整部署步骤：`docs/[AI客服工具包] 部署手册·公开版.md`
- 安全底线：`docs/`（或根目录）`【安全须知】API密钥与鉴权基线.md`
- Claude API 文档：https://docs.anthropic.com/claude/reference/messages_post

---

**版本**：v1.0 · 2026-07-16 · 由创业沙拉 TikBit 出品 · https://startupsalad.com

