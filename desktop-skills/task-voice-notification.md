---
name: task-voice-notification
description: TikBit 主对话任务完成、等待人工处理时的语音通知；支持精确对话编号、分支静音与四种音色。
---

# Task voice notification

The installer activates a managed rule in this vault's CLAUDE.md and AGENTS.md. Follow that rule for final completion and real blocking points. Never announce a subagent's completion, trigger notification for ordinary Q&A, or enable Stop-based automatic completion. Use the bundled `run.cjs` launcher; it passes the actual vault and Obsidian configuration directory to the notification child. Do not infer a tab number or change voice identity to bypass a muted result.

Engine and audio assets live in `resources/engine` and `resources/voice_clips`. Voice defaults to xiaoxiao. User choices remain in the writable engine directory; updates preserve them. `--dry-run` checks ownership without playing or writing. Installation does not play test audio.
