# 工具目录

> 每个子目录是一个独立工具包，含自己的 `INSTALL.md` 和使用说明。完整元数据见仓库根目录的 [`catalog.json`](../catalog.json)。

## 怎么装

不要手动复制文件。把仓库地址交给你的 AI 助手，让它读 `catalog.json`，按推荐等级介绍完、你确认要装哪些之后，它会读对应目录的 `INSTALL.md` 自动完成安装和验证。

```text
https://github.com/startupsalad/TikBit
```

## 工具清单

| 目录 | 用途 | 推荐等级 |
|:---|:---|:---:|
| `html-page` | H5、推文页和落地页生成系统 | 建议必装 |
| `document-reader` | Word、Excel、PPT、PDF、图片与网页读取、解析和编辑 | 建议必装 |
| `context-reminder` | 对话长度提醒与 Token 管理 | 建议必装 |
| `gpt-image` | 对话式 GPT 生图、参考图编辑和批量出图 | 建议必装 |
| `voice-notification` | AI 长任务语音提醒 | 条件推荐 |
| `writing-humanizer` | 中文文案、陈述稿和讲稿去 AI 化 | 条件推荐 |
| `ai-customer-service` | 在线客服机器人（自部署），需自备服务器和令牌 | 按需 |
| `ai-social-media` | AI 新媒体内容与视觉 Skill | 按需 |
| `ai-marketing` | 营销、定价、竞品与增长 Skill | 按需 |
| `ppt-design` | PPT 制作 Skill 与指南，核心大包走 Release | 按需 |
| `ppt-style-gallery` | PPT 风格与 HTML 版式速查图册 | 按需 |
| `web-design` | 网页设计方法论与设计 Skill | 按需 |
| `video-audio` | 视频音频处理工具包 | 按需 |

## 密钥说明

本目录任何文件都不含真实密钥，配置文件一律是空值或示例占位符。需要密钥的工具分两类，详见 `catalog.json` 的 `api_key_policy`：

- **复用工作台令牌**（`gpt-image`、`ppt-design` 的 A 模式）：AI 安装时直接复用你 TikBit 工作台已配置的令牌，你不需要另外提供密钥，也不用另找 OpenAI。生图消耗工作台同一份额度。
- **需自备令牌**（`ai-customer-service`）：跑在你自己的服务器上，令牌要填进你自己的 `.env`。去 [tikbit.ai](https://tikbit.ai) 后台「令牌管理」取一个，别用别人的。

其余工具不需要任何密钥。

---

由创业沙拉 | TikBit 维护 · [startupsalad.com](https://startupsalad.com)
