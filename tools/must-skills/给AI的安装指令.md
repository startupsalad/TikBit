# 给 AI 的安装指令

请先读取 `catalog.json` 中 `must-skills` 的元数据，再读取本目录 `INSTALL.md`。先检查 `~/.claude/skills/` 和 `~/.codex/skills/` 是否已有 7 个同名 Skill；已存在且可用的不要重复安装。需要更新时运行 `node install-core.js`，完成后验证目录和 Python 解释器，再向用户汇报结果。
