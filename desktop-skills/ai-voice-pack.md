---
name: ai-voice-pack
description: Claude 回复结束后用系统语音朗读简短摘要；离线、无需 API，GPT 暂不支持该朗读钩子。
---

# AI read aloud

This package is activated for Claude only. The client merges a project-level Stop hook without changing existing hooks. Its local `resources/speak.js` reads the ON switch beside the script. Include a concise natural spoken summary in a `<!--SPEAK: ...-->` comment when appropriate. Never read API keys, private configuration or an entire document aloud. User controls can toggle the ON switch; do not remove files from other tools. System speech availability is separate from having a hook installed. Do not tell GPT users that GPT supports this Claude-specific hook.
