# 必装 Skill 工具包

这是一组通用底层能力：`docx`、`xlsx`、`pptx`、`pdf`、`kb-retriever`、`skill-creator` 和 `defuddle`。

安装器会把 Skill 同步到 `~/.claude/skills/` 与 `~/.codex/skills/`。如果用户已经安装了这些目录或仓库中的同名版本，AI 应先检查并只更新到当前版本，不重复创建副本。

Git 源码包不携带平台专用的便携 Python；文档 Skill 使用用户已有的 Python 3。需要的库可按 `INSTALL.md` 安装到用户自己的环境或虚拟环境。

## 文档与音视频入口

本包保持7项底层Skill；配套必装工具 [document-reader](../document-reader/INSTALL.md) 提供“文档读取编辑”统一入口，已补视频/音频识别、视频号捕获流程及本地核验归档。先检查是否已有入口，再用其install.py按当前引擎安装，避免重复。

一般视频下载与本地转写复用 [video-audio](../video-audio/INSTALL.md)，后端依赖按需安装；不把res-downloader证书、系统代理或GB级模型作为每台机器的自动安装项。
