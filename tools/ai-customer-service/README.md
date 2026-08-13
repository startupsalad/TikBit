# AI 客服工具包

> 给任意网站加一个「点一下就能问答」的智能在线客服窗口。后端调本机 claude CLI（走创业沙拉 tikbit 中转站），自备服务器自部署，全程无第三方托管。
> 由创业沙拉 TikBit 出品 · https://startupsalad.com · v1.0

## 这是什么

一套完整的 AI 在线客服解决方案：访客点开网页右下角悬浮窗提问，后端带着你的知识库调本机 claude CLI 给出即时回答。含**一套改配置就能跑的参考实现** + **一个让 AI 帮你定制部署的 skill**。架构复刻了创业沙拉自己 ai.salad.co/guide 跑通的在线答疑那套。

## 快速导航

| 文档 | 用途 | 适合谁 |
|:---|:---|:---:|
| **README.md**（本文） | 总览 + 目录树 | 所有人 |
| **📖 使用说明.md** | 5 分钟上手 + FAQ | 👤 人类用户 |
| **【给其他AI的安装指令】.md** | 让 AI 自动帮你部署 | 🤖 AI 助手 |
| **【安全须知】API密钥与鉴权基线.md** | 密钥/鉴权必读 | ⚠️ 所有人 |
| **docs/[AI客服工具包] 部署手册·公开版.md** | 完整部署步骤 | 🔧 部署者 |
| **docs/[AI客服工具包] 知识库准备指南.md** | 怎么整知识库 | 📝 内容准备者 |
| **VERSION.md** | 版本记录 | 📋 维护者 |

## 两种用法

- **让 AI 帮你部署**（推荐小白）：把工具包给你的 AI 助手，说「读一下【给其他AI的安装指令】.md，帮我部署客服机器人」，AI 会引导你填配置、整知识库、生成命令。
- **自己跑参考实现**（技术型）：进 `参考实现/`，`cp backend/.env.example backend/.env` 填好，`cd deploy && bash scripts/deploy.sh` 一键起。

## 目录结构

```
AI客服工具包/
├── README.md                        # 总览（本文）
├── 📖 使用说明.md                    # 给人：快速上手 + FAQ
├── 【给其他AI的安装指令】.md          # 给 AI：自动部署剧本
├── 【安全须知】API密钥与鉴权基线.md    # 密钥/鉴权必读
├── VERSION.md · LICENSE · CLAUDE.md片段.txt
│
├── skills/在线客服机器人/SKILL.md     # AI 定制生成用的能力（方法论）
│
├── 参考实现/                          # 改配置就能跑
│   ├── backend/                      # Node.js 服务（零依赖，spawn 调 claude CLI）
│   │   ├── server.js + src/knowledge.js  # 主服务(限流+每日预算) + 知识库加载
│   │   ├── knowledge-base/           # 知识库（放你的 FAQ）
│   │   ├── package.json + .env.example
│   ├── frontend/                     # 聊天窗口
│   │   ├── chatbot-widget.js         # 一行 <script> 引入
│   │   ├── 集成说明.md + demo.html
│   └── deploy/                       # 一键部署
│       ├── Dockerfile + docker-compose.yml
│       ├── nginx/chatbot.conf + scripts/{deploy,update,logs}.sh
│
└── docs/                            # 部署手册 / 知识库指南 / 踩坑
```

## 技术栈

Node.js 原生（后端零第三方依赖，spawn 调 claude CLI）· 创业沙拉 tikbit 中转站（兼容 Claude API）· Docker + Nginx 反向代理 · 纯 JS 前端 widget（无框架）。1 核 1G 服务器可跑。

## 安全基线（务必看）

令牌走 claude CLI 那层（环境变量 `ANTHROPIC_AUTH_TOKEN`），**不下发前端、不进代码**。接口公网可调，防滥用靠后端内建的**单 IP 限流 + 全站每日算力预算封顶 + 答疑范围锁死**，防止被人刷爆你的 tikbit 额度。别关。详见 `【安全须知】API密钥与鉴权基线.md`。

---

想要从知识库梳理到部署调优的一站式服务？找创业沙拉：https://startupsalad.com

