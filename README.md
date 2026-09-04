# TikBit 工具库

创业沙拉 | TikBit 维护的通用 AI 工具集合，面向 AI 助手和团队成员使用。

## 给 AI 助手

把本仓库地址交给 AI：

```text
https://github.com/startupsalad/TikBit
```

请先读取 [`catalog.json`](catalog.json) 的 `recommendation_policy`、`api_key_policy` 和完整工具清单，再按三档向用户介绍：**必装 → 推荐 → 按需**。先检查本机是否已经安装对应目录、Skill 或行为指令；已经安装且可用的直接标记为已安装，不要重复复制或重复添加钩子。等待用户确认具体工具后，再读取对应目录的 `INSTALL.md`。

`context-reminder` 已集成到工作台插件，不再作为本仓库工具。旧版工作台的独立必装 Skill 包仍保留为 `must-skills`，AI 识别到已有 docx/xlsx/pptx/pdf 等 Skill 时应跳过重复安装。

## 三档推荐

### 必装

| 工具 | 用途 |
|:---|:---|
| `must-skills` | docx、xlsx、pptx、pdf、知识库检索、Skill 创建和网页正文读取等底层能力 |
| `html-page` | H5、推文页和落地页生成 |
| `document-reader` | Word、Excel、PPT、PDF、图片和网页读取、解析与编辑 |
| `gpt-image` | 工作台对话式生图、参考图编辑和批量出图 |

### 推荐

| 工具 | 适合场景 |
|:---|:---|
| `voice-notification` | 同时跑多个任务，或经常等待几分钟以上 |
| `writing-humanizer` | 经常写文案、陈述稿、讲稿和其他对外文字 |

### 按需

| 工具 | 用途 |
|:---|:---|
| `ai-customer-service` | 自部署在线客服机器人 |
| `ai-social-media` | 新媒体内容与视觉 Skill |
| `ai-media-team` | 策划、内容、制作三个 AI 总监 |
| `ai-marketing` | 营销、定价、竞品与增长 Skill |
| `ai-self-growth` | 在知识库积累用户画像、项目记忆和经验 |
| `ppt-design` | PPT 制作 Skill 与指南 |
| `ppt-style-gallery` | PPT 风格与 HTML 版式速查图册 |
| `web-design` | 网页设计方法论与 Skill |
| `video-audio` | 视频下载、抽帧和语音转文字 |
| `video-channels-comment` | 视频号评论批量导出与分析 |
| `ai-voice-pack` | Claude 回复后的系统语音朗读（Claude 专用） |
| `wechat-ai-deployment` | 个人微信/企业微信接入 AI 的统一部署手册 |

## 快速安装工具库

Windows PowerShell：

```powershell
irm https://raw.githubusercontent.com/startupsalad/TikBit/main/install.ps1 | iex
```

macOS / Linux：

```bash
curl -fsSL https://raw.githubusercontent.com/startupsalad/TikBit/main/install.sh | bash
```

## 密钥与隐私

仓库不包含 API Key、Token、密码、客户资料或本机路径。`gpt-image` 和 `ppt-design` 的指定模式可复用本机工作台令牌；自部署客服、视频云端转写和微信接入必须使用用户自己的凭证。任何密钥只写入用户自己的本地或服务器环境，不提交到 Git。

部分工具包含第三方 Skill、模板、字体或运行依赖，许可证见 [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) 及各工具目录。
