# TikBit 工具库

创业沙拉维护的通用 AI 工具集合，面向 AI 助手和团队成员使用。

## 给 AI 助手

把本仓库地址交给你的 AI：

```text
https://github.com/startupsalad/TikBit
```

请先读取 [`catalog.json`](catalog.json) 中的 `recommendation_policy`、`api_key_policy` 和完整工具清单。先检查本机已安装状态，再按“建议必装 → 条件推荐 → 其他按需”的顺序向用户介绍并解释理由，已安装的直接标注为已安装。等待用户确认具体工具后，再读取对应目录下的 `INSTALL.md` 并按当前操作系统执行安装。安装前先确认目标路径和依赖。

密钥按 `api_key_policy` 处理：`api_key_source` 为 `workstation_relay` 的工具（`gpt-image`、`ppt-design`）直接复用本机 TikBit 工作台已配置的令牌，**不要向用户索取密钥**；`user_provided` 的工具（`ai-customer-service`）运行在用户自己的服务器上，必须由用户自备令牌，不要代填本机令牌。任何情况下都不回显或上传用户的密钥。

## 安装建议

推荐只代表优先级，**不会跳过用户确认自动安装**。

### 建议必装

| 工具 | 推荐理由 |
|:---:|:---|
| `html-page` | AI 生成的文案、方案和 PPT 内容，更适合先通过 HTML 页面呈现、检查和交付。 |
| `document-reader` | 增强 PDF、Word、Excel、PPT、图片和网页等常用资料的读取、解析与编辑能力。 |
| `context-reminder` | 有效节省 Token，并降低对话过长后 AI 遗漏信息、跑偏或输出不稳定的概率。 |
| `gpt-image` | 让 TikBit AI 在对话中直接生成、修改和批量输出图片；图片工作室仍用于用户手动操作单张图片。 |

### 条件推荐

| 工具 | 适合谁 |
|:---:|:---|
| `voice-notification` | 会同时运行多个任务，或经常遇到需要几分钟到几十分钟的任务，并且设备具备语音播放条件。 |
| `writing-humanizer` | 经常写文案、陈述稿、讲稿和其他对外文字。 |

其余工具由 AI 根据用户的实际任务按需推荐。

## 快速安装

Windows PowerShell：

```powershell
irm https://raw.githubusercontent.com/startupsalad/TikBit/main/install.ps1 | iex
```

macOS / Linux：

```bash
curl -fsSL https://raw.githubusercontent.com/startupsalad/TikBit/main/install.sh | bash
```

完整元数据见 [`catalog.json`](catalog.json)。

## 工具目录

| 工具 | 用途 | 推荐等级 |
|:---:|:---|:---:|
| `ai-customer-service` | 在线客服机器人（自部署）：给自己网站加 AI 问答窗口，需自备服务器和令牌 | 按需 |
| `ai-social-media` | AI 新媒体内容与视觉 Skill | 按需 |
| `ai-marketing` | 营销、定价、竞品与增长 Skill | 按需 |
| `html-page` | H5、推文页和落地页生成系统 | 建议必装 |
| `gpt-image` | TikBit AI 工作台对话式 GPT 生图、参考图编辑和批量出图 | 建议必装 |
| `ppt-design` | PPT 制作相关 Skill 与指南 | 按需 |
| `ppt-style-gallery` | PPT 风格与 HTML 版式速查图册 | 按需 |
| `document-reader` | Word、Excel、PPT、PDF、图片与网页读取、解析和编辑 | 建议必装 |
| `web-design` | 网页设计方法论与设计 Skill | 按需 |
| `video-audio` | 视频音频处理工具包 | 按需 |
| `voice-notification` | AI 长任务语音提醒 | 条件推荐 |
| `context-reminder` | 对话长度提醒与 Token 管理 | 建议必装 |
| `writing-humanizer` | 中文文案、陈述稿和讲稿去 AI 化 | 条件推荐 |

## 隐私与安全

本仓库不包含 API Key、Token、密码、客户资料、微盘占位文件或本机安装配置。需要密钥的工具只提供空配置和环境变量示例，密钥必须由使用者在本机配置。

## 第三方内容

部分工具包含第三方开源 Skill、模板或依赖，版权和许可证见 [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) 及各工具目录内的许可证文件。

## 许可证

创业沙拉原创分发层和原创代码采用 MIT License；第三方内容以其原许可证为准。
