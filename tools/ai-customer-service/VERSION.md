# 版本记录

**当前版本**：v1.0
**发布日期**：2026-07-16
**适用**：Claude / CodeBuddy 等能读文件、执行命令的 AI 助手；或技术型用户手动部署

---

## v1.0 · 2026-07-16 · 首次发布

**首次发布**，把「在线客服机器人」能力从纯 skill 方法论，补齐为可对外分发的完整工具包。

包含内容：
- **skill**：`skills/在线客服机器人/SKILL.md`（AI 定制生成用的方法论）
- **参考实现**（架构复刻创业沙拉 ai.salad.co/guide 跑通的在线答疑）：
  - `backend/` — Node.js 原生后端（零依赖），`spawn` 调本机 claude CLI，含单 IP 限流、每日算力预算封顶、并发上限、知识库自动加载
  - `frontend/` — 自注入聊天窗口，一行 `<script>` 引入，发 `{q}` 收 `{answer}` 单轮
  - `deploy/` — Dockerfile（装 claude CLI + 预种免 onboarding）+ docker-compose + Nginx 反代 + 一键部署/更新/日志脚本
- **文档**：README / 使用说明 / 给 AI 的安装指令 / 安全须知 / 公开版部署手册 / 知识库准备指南 / 踩坑手册

设计要点：
- 后端不碰密钥——令牌走 claude CLI 的环境变量（`ANTHROPIC_AUTH_TOKEN` + `ANTHROPIC_BASE_URL`，指向创业沙拉 tikbit 中转站）
- 防滥用靠限流 + 每日算力预算封顶 + 答疑范围锁死；前后端同域，无需 CORS
- 全量脱敏，可对外分发（无令牌/IP/密码/客户名）

## 安装要求

**必需**：
- 一台能装 Docker（含 compose）的服务器，有公网 IP
- tikbit 令牌（创业沙拉 tikbit 中转站 https://tikbit.ai/，兼容 Claude API）
- Nginx（网站托管）

**说明**：
- 后端 Node 代码零第三方 npm 依赖；claude CLI 由 Docker 镜像自动装（不用 Docker 直跑则需自行 `npm i -g @anthropic-ai/claude-code` + Node 18+）

## 更新计划

- [ ] v1.1：知识库支持 URL 抓取 / 多文件分片检索（当前全量塞 prompt）
- [ ] v1.2：限流器 Redis 版（支持多实例）、会话持久化
- [ ] v1.3：接入统计面板（问答量、命中率、转人工率）
- [ ] 打好的一键部署 zip（自带示例知识库）

## 已知问题

- 知识库全量进 system prompt，超 1 万字建议精简（见踩坑手册 #5）。
- 限流/每日预算是内存态，单实例有效；多实例部署需换 Redis 共享。
- 当前单轮问答（不带上下文），与创业沙拉自己的在线答疑一致；多轮可后续扩展。
- ⚠️ tikbit 的 Anthropic 格式 base_url 确切值和鉴权头以 tikbit 控制台为准，用前核实。

## 反馈 & 授权

- 出品：创业沙拉 TikBit · https://startupsalad.com
- 授权：MIT（见 LICENSE）

