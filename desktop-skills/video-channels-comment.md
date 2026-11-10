---
name: video-channels-comment
description: 导出用户自己已登录视频号助手中的评论，生成 Markdown、CSV、JSON 并分析反馈；使用本地浏览器登录。
---

# Video channel comments

The exporter is `resources/core/视频号评论导出工具.py`. Its Python Playwright dependency is checked by the client before readiness. It connects to the user's own Chrome through local CDP, without installing a separate browser or reading another browser profile. Guide the user through official video-channel login when needed; do not claim comments are accessible before login. Use `--help` to inspect current arguments, then run the local exporter for the requested account. Keep outputs in the current vault's task folder and report actual exported files. Do not terminate unrelated browser processes.
