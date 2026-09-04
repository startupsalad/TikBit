# 视频号评论导出工具

连接用户自己以调试模式打开的 Chrome，批量读取视频号助手评论并生成 Markdown、CSV、JSON 三种格式。只读取用户自己的账号，不修改后台数据。

运行前需要 Python 3 和 `playwright`；工具通过 CDP 连接已打开的 Chrome，不需要下载 Playwright 浏览器。
