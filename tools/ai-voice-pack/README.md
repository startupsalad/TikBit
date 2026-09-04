# AI 语音朗读包

Claude Code 专用的 Stop 钩子语音朗读工具。每次 Claude 回复后，用系统语音念出简短总结；离线运行，不消耗 API Token。

这是按需工具，只写入 Claude 侧的 `~/.claude/settings.json`、`~/.claude/ss-speak/` 和 Claude 指令文件。GPT(Codex) 不支持同一套 Stop 钩子，未安装属于正常状态。
