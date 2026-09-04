# 必装 Skill 工具包

这是一组通用底层能力：`docx`、`xlsx`、`pptx`、`pdf`、`kb-retriever`、`skill-creator` 和 `defuddle`。

安装器会把 Skill 同步到 `~/.claude/skills/` 与 `~/.codex/skills/`。如果用户已经安装了这些目录或仓库中的同名版本，AI 应先检查并只更新到当前版本，不重复创建副本。

Git 源码包不携带平台专用的便携 Python；文档 Skill 使用用户已有的 Python 3。需要的库可按 `INSTALL.md` 安装到用户自己的环境或虚拟环境。
