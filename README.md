# TikBit 工具库

创业沙拉维护的通用 AI 工具集合，面向 AI 助手和团队成员使用。

## 给 AI 助手

把本仓库地址交给你的 AI：

```text
https://github.com/startupsalad/TikBit
```

请先读取 [`catalog.json`](catalog.json)，根据用户选择的工具读取对应目录下的 `INSTALL.md`，再按当前操作系统执行安装。安装前先确认目标路径、依赖和 API Key 由用户自行提供；不要索取或上传用户的密钥。

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

| 工具 | 用途 |
|:---:|:---:|
| `ai-customer-service` | 在线客服机器人参考实现与 Skill |
| `ai-social-media` | AI 新媒体内容与视觉 Skill |
| `ai-marketing` | 营销、定价、竞品与增长 Skill |
| `html-page` | H5、推文页和落地页生成系统 |
| `ppt-design` | PPT 制作相关 Skill 与指南 |
| `ppt-style-gallery` | PPT 风格与 HTML 版式速查图册 |
| `document-reader` | Word、Excel、PPT、PDF、图片与网页读取工具 |
| `web-design` | 网页设计方法论与设计 Skill |
| `video-audio` | 视频音频处理工具包 |
| `voice-notification` | 任务语音通知工具 |
| `context-reminder` | 对话长度提醒工具 |
| `writing-humanizer` | 中文去 AI 化写作 Skill |

## 隐私与安全

本仓库不包含 API Key、Token、密码、客户资料、微盘占位文件或本机安装配置。需要密钥的工具只提供空配置和环境变量示例，密钥必须由使用者在本机配置。

## 第三方内容

部分工具包含第三方开源 Skill、模板或依赖，版权和许可证见 [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) 及各工具目录内的许可证文件。

## 许可证

创业沙拉原创分发层和原创代码采用 MIT License；第三方内容以其原许可证为准。
