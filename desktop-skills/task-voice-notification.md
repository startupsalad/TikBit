---
name: task-voice-notification
description: TikBit 主对话任务完成、等待人工处理时的语音通知；支持精确对话编号、分支静音与四种音色。
---

# Task voice notification

Read `resources/engine/notification-rule.md` for the four notification modes. The installer merges that rule into this vault's CLAUDE.md and AGENTS.md. Use done only for final delivery, perm for authorization, ask for choices or confirmations (including optional and asynchronous questions), and stuck for required human operations. Native dialogs are announced by the compatible plugin when TIKBIT_VOICE_UI_MANAGED=1; do not manually repeat those notifications. Text-only questions still require ask. Never announce ordinary Q&A, subagent completion, or enable Stop-based automatic done. Use `node run.cjs <mode>` from the actual vault with this installed script path; it passes the real vault and host configuration to the engine. Do not guess a tab or change the chosen voice to bypass a muted result.

Engine and audio assets live in `resources/engine` and `resources/voice_clips`. Voice defaults to xiaoxiao. User choices remain in the writable engine directory; updates preserve them. `--dry-run` checks ownership without playing or writing. Installation does not play test audio.
