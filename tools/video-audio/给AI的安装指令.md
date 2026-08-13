# 视频音频处理工具包 安装指令

> **给 AI 看的安装说明**。如果你是人类用户，请改看 `📖 使用说明.md`。

## 这是什么

**视频音频处理工具包**，包含3个 Agent Skill，覆盖视频下载、视频理解、本地语音转写三个核心场景：

| Skill | 功能 | 来源 | 协议 |
|:---|:---|:---|:---|
| **video-catcher** | 下载 YouTube/Bilibili/抖音/X 等平台视频，支持字幕/封面/多清晰度/批量，全自动 fallback | [Weikezi-AI/video-catcher](https://github.com/Weikezi-AI/video-catcher) | ⚠️ GPL-3.0-only |
| **watch** | 读懂一段视频（URL 或本地）：下载→抽帧→拉字幕/Whisper转写→回答问题 | [bradautomates/claude-video](https://github.com/bradautomates/claude-video) | MIT |
| **local-transcribe** | 本地语音转文字，不上传音频，无需 API Key；输出带时间戳 MD + SRT | 创业沙拉 AI 团队自研 | MIT |

⚠️ **重要**：video-catcher 使用 **GPL-3.0-only** 协议。若修改其代码后对外发布或提供服务，需同样以 GPL-3.0 开源。详见 `LICENSE-video-catcher-GPL3.txt`。

---

## 第0步：判断目标 AI 是否支持 Skill 机制

**A. 支持 Skill（Claude Code / Codex / 其他 Agent Code 工具）**
→ 走 **方法A：Skill 安装**（推荐）

**B. 不支持 Skill（ChatGPT / Gemini / 通用 LLM）**
→ 走 **方法B：手动粘贴指令**

---

## 方法A：Skill 安装（适用于 Claude Code / Codex 等）

### 解压工具包

工具包的 Skill 文件已压缩为 `视频音频处理工具包.zip`。先解压到临时目录：

```bash
# Windows PowerShell
Expand-Archive -Path "视频音频处理工具包.zip" -DestinationPath "$env:TEMP/av_tools" -Force

# macOS / Linux
unzip 视频音频处理工具包.zip -d /tmp/av_tools
```

### 安装到项目级（推荐，知识库专用）

```bash
# Windows
xcopy /E /I "%TEMP%\av_tools\skills\video-catcher" "<知识库路径>\.claude\skills\video-catcher"
xcopy /E /I "%TEMP%\av_tools\skills\watch" "<知识库路径>\.claude\skills\watch"
xcopy /E /I "%TEMP%\av_tools\skills\local-transcribe" "<知识库路径>\.claude\skills\local-transcribe"

# macOS / Linux
cp -r /tmp/av_tools/skills/* "<知识库路径>/.claude/skills/"
```

### 安装到用户级（跨项目可用）

```bash
# Windows
xcopy /E /I "%TEMP%\av_tools\skills\video-catcher" "%USERPROFILE%\.claude\skills\video-catcher"
xcopy /E /I "%TEMP%\av_tools\skills\watch" "%USERPROFILE%\.claude\skills\watch"
xcopy /E /I "%TEMP%\av_tools\skills\local-transcribe" "%USERPROFILE%\.claude\skills\local-transcribe"

# macOS / Linux
cp -r /tmp/av_tools/skills/* ~/.claude/skills/
```

安装后重启 Claude Code / Codex 客户端。

### 验证安装

| Skill | 验证触发语 |
|:---|:---|
| video-catcher | "帮我下载这个视频 [URL]" |
| watch | "/watch [视频URL]" 或 "帮我看看这个视频" |
| local-transcribe | "帮我把这段录音转成文字 [文件路径]" |

---

## 方法B：手动粘贴指令（适用于 ChatGPT / Gemini 等）

1. 解压工具包，找到目标 Skill 的 `SKILL.md` 文件
2. 复制 `---` 分隔符**之后**的全部内容（不要复制 YAML frontmatter）
3. 粘贴到 AI 的自定义指令 / 系统提示词 / 对话开头

---

## 依赖安装

### video-catcher

```bash
pip install -r skills/video-catcher/requirements.txt
# 主要依赖：yt-dlp, playwright, requests 等
```

运行 doctor 检查：

```bash
python skills/video-catcher/scripts/doctor.py
```

### watch

```bash
# 依赖 ffmpeg、yt-dlp（video-catcher 已包含 yt-dlp）
# macOS: brew install ffmpeg
# Windows: winget install Gyan.FFmpeg 或手动复制 ffmpeg.exe 到 ~/bin/
```

watch 首次运行时会自动引导安装，运行 setup.py 即可：

```bash
python skills/watch/scripts/setup.py
```

### local-transcribe

```bash
pip install faster-whisper
# 首次转写时自动下载模型（medium≈1.5 GB，large-v3≈2.9 GB）
# huggingface.co 不通时自动切 hf-mirror.com，无需手动配置
```

---

## 开源协议声明

| Skill | 协议 | 商业使用 | 修改后分发 |
|:---|:---|:---|:---|
| video-catcher | **GPL-3.0-only** | ✅ 可商用 | ⚠️ 需以 GPL-3.0 开源修改版 |
| watch | MIT | ✅ 可商用 | ✅ 无需开源，保留版权声明即可 |
| local-transcribe | MIT | ✅ 可商用 | ✅ 无需开源，保留版权声明即可 |

完整许可证文本见本目录的 `LICENSE-*.txt` 文件。

---

## 安装后的记忆规则（可选）

如果 AI 支持长期记忆，可写入：

```
视频音频处理工具包已安装，包含3个Skill：
- video-catcher（视频下载，GPL-3.0-only）：下载 YouTube/Bilibili/抖音等视频
- watch（视频理解，MIT）：读懂视频内容，回答问题
- local-transcribe（本地转写，MIT）：本地语音转文字，不上传，不需 API Key

下载视频用 video-catcher；看懂视频内容/回答问题用 watch；
本地音视频转文字/字幕用 local-transcribe。
```

---

## 故障排查

**AI 没有调用 Skill**
→ 检查 Skill 安装路径 / 重启客户端 / 显式指定"使用 video-catcher skill 下载这个视频"

**video-catcher doctor.py 报告依赖缺失**
→ `pip install -r skills/video-catcher/requirements.txt` 后重跑

**watch 找不到 ffmpeg**
→ 确认 ffmpeg 在 PATH 或 ~/bin/ 中：`ffmpeg -version`

**local-transcribe CUDA 报错然后降级**
→ 正常现象，自动用 CPU 继续；如果想纯 CPU 加 `--device cpu`

**本机网络访问 huggingface.co 超时**
→ local-transcribe 和 watch（Whisper 部分）均内置 hf-mirror.com 降级，首次超时后自动重试

---

**最后更新**：2026-08-10

