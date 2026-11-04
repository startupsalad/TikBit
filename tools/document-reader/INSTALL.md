# 文档读取编辑工具包安装

读取 `给AI的安装指令.md` 和 `📖 使用说明.md`。已有工具先检查版本，勿重复安装。

1. 保留本目录全部脚本和references；运行 `python install.py --vault "知识库路径"` 安装Claude/GPT两端项目Skill。用户级安装省略--vault并尊重CLAUDE_CONFIG_DIR/CODEX_HOME；可用--dry-run检查目标。
2. 按需求安装原文档Python依赖与Office转换引擎，运行 `python 检查环境.py --quick`。
3. 本地音视频按需安装ffmpeg/ffprobe；本地转写、一般视频下载再读同仓库 `tools/video-audio/INSTALL.md`。无需为基本读取提供API密钥。
4. 视频号单独读`references/video-channels.md`。0.4.0统一入口直接解析分享链接、从腾讯CDN下载及校验，普通客户无需res-downloader、证书、代理或在微信播放。默认使用第三方公共解析服务，维护者可换兼容端点；失败在对话内报告，不悄悄切到手动抓取。读口播加`--transcribe`，后端及运行依赖由AI按需准备，复用缓存模型并先说明初始化耗时。
5. 用现成文档及本地视频实测；脚本列出的PDF/图片要再次读取。改Office存量文件时再按OfficeCLI说明安装编辑后端。

本地口播转写：按video-audio的INSTALL安装local-transcribe后端；AI可用当前Python后台执行`python -m pip install --only-binary=:all: --target "用户目录/.tikbit/media-runtime/site-packages" -r speech-requirements.txt`准备隔离依赖，路径须展开为真实用户目录，普通客户不运行命令。本机已实证PyAV 19与faster-whisper 1.2.1不兼容，使用所附版本约束，不让pip尝试现场编译。优先复用已有模型；首次模型准备先说明耗时。指定模型可用`TIKBIT_TRANSCRIBE_MODEL`，已有medium缓存会自动采用本地路径；GPU库不可用时后端降级CPU，不擅自安装CUDA。

自动下载模式退出码4表示视频已保留、转写尚待准备；读取JSON的`source`与`archive`，对本地文件继续转写，不能重新下载冒充进展。默认自动模式不使用退出码3的手动代理含义。

0.4.0增加`channels_resolver.py`默认直接解析下载，保留0.3.0维护者手动会话和0.2.0本地媒体CLI。完整保留全部脚本／references；不生成客户开始菜单入口，不打包第三方抓取应用或大模型。只有显式手动抓取分支的退出码3表示代理待核对，应读取JSON，不能自动重下。
