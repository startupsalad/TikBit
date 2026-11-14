# TikBit 工具库

创业沙拉 | TikBit 维护的通用 AI 工具集合，面向 AI 助手和团队成员使用。

## 给 AI 助手

把本仓库地址交给 AI：

```text
https://github.com/startupsalad/TikBit
```

请先读取 [`catalog.json`](catalog.json) 的 `recommendation_policy`、`api_key_policy` 和完整工具清单，再按三档向用户介绍：**必装 → 推荐 → 按需**。先检查本机是否已经安装对应目录、Skill 或行为指令；已经安装且可用的直接标记为已安装，不要重复复制或重复添加钩子。等待用户确认具体工具后，再读取对应目录的 `INSTALL.md`。

`context-reminder` 已集成到工作台插件，不再作为本仓库工具。旧版工作台的独立必装 Skill 包仍保留为 `must-skills`，AI 识别到已有 docx/xlsx/pptx/pdf 等 Skill 时应跳过重复安装。

## 工作台工具分发维护

支持新分发入口的工作台优先从上海阿里云 OSS 下载，GitHub 保留源码、原目录和备用包。主清单为 `https://startupsalad-downloads.oss-cn-shanghai.aliyuncs.com/tikbit-tools/catalog.json`。

工具内容变化时先升级该工具 `VERSION`，用 `scripts/build-desktop-tools.py` 生成完整包，按原流程将 GitHub 包先于目录发布，再同步 OSS；不能只更新其中一个下载通道。同步保持原目录和安装包字节，默认预检，显式 `--apply` 才上传：

```bash
python scripts/publish-desktop-tools.py --directory /path/to/complete-desktop --report /path/to/preflight.json
python scripts/publish-desktop-tools.py --directory /path/to/complete-desktop --apply --report /path/to/publication.json
```

完整目录需包含 `catalog.json` 与 `packages/` 下全部目录引用包（含已核验 PPT 大包）。脚本只用 Python 标准库，从本机已有 `~/.ossutilconfig` 读取凭据，不输出密钥；支持 `--oss-config`。应用前核本地目录与官方 GitHub 已发目录内容一致，镜像保留官方原始字节，兼容 Windows 检出换行。先校验所有本地包，逐包上传后按公网 identity 响应核长度与 SHA256；同号不同内容拒绝覆盖，失败不更新清单。包全部通过后保留内容寻址清单和旧清单，再更新主清单；不删除旧包。无变化只核验，不重传。

普通工具可独立更新，无须每次发布插件。插件发布前运行插件源码的 `node scripts/check-tool-distribution.mjs`，验证官方 GitHub 清单与 OSS 一致、所有包已就位；`upload-latest.sh` 已接入此检查。新客户端仍校验安装包大小、SHA256 和受信路径；旧客户端保持原 GitHub 行为。

如果本机 Python 缺少 GitHub 证书链，同步器可借助工作台已有 Node.js 的默认 HTTPS 信任链读取官方清单；不会关闭证书校验，不下载新依赖。

## 三档推荐

### 必装

| 工具 | 用途 |
|:---|:---|
| `must-skills` | docx、xlsx、pptx、pdf、知识库检索、Skill 创建和网页正文读取等底层能力 |
| `html-page` | H5、推文页和落地页生成 |
| `document-reader` | 文档、网页及音视频统一入口；视频号分享链接自动下载、校验读取与归档（0.4.0） |
| `gpt-image` | 工作台对话生图、参考图编辑及本地修复；默认 2.5 精细档（1.2.0） |

### 推荐

| 工具 | 适合场景 |
|:---|:---|
| `voice-notification` | 主对话完成、授权和选择提醒；0.3.3补齐双引擎规则与隔离目录，支持配套工作台弹窗去重及安全更新 |
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
| `web-design` | 网页设计与已有页面去 AI 味诊断、精修（0.2.0） |
| `video-audio` | 统一入口的按需后端：视频下载、抽帧、本地转写与视频号流程；云转写自选 |
| `video-channels-comment` | 视频号评论批量导出与分析 |
| `ai-voice-pack` | Claude 回复后的系统语音朗读（Claude 专用） |
| `wechat-ai-deployment` | 个人微信/企业微信接入 AI 的统一部署手册 |

## 快速安装工具库

### 工作台内一键安装

已接入此功能的 TikBit 客户端可在“设置 → 更多工具”查看目录，选择安装、更新或修复，安装后点击“立即使用”打开新对话。工具安装到当前知识库，Claude 和 GPT 均可使用；已有自定义文件会保留。

分发清单及独立包见 [desktop/README.md](desktop/README.md)。全部 18 个工具包支持安装；需要服务器、账号登录或画像的工具，安装后通过“继续配置”完成必要步骤。语音朗读包仅支持 Claude；PPT 核心资源按需下载。未接入该入口的旧客户端继续使用下面的 AI 安装方式。

### 通过 AI 安装

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
