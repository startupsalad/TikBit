# 文档读取编辑工具包安装

读取 `给AI的安装指令.md` 和 `📖 使用说明.md`。已有工具先检查版本，勿重复安装。

1. 保留本目录全部脚本和references；运行 `python install.py --vault "知识库路径"` 安装Claude/GPT两端项目Skill。用户级安装省略--vault并尊重CLAUDE_CONFIG_DIR/CODEX_HOME；可用--dry-run检查目标。
2. 按需求安装原文档Python依赖与Office转换引擎，运行 `python 检查环境.py --quick`。
3. 本地音视频按需安装ffmpeg/ffprobe；本地转写、一般视频下载再读同仓库 `tools/video-audio/INSTALL.md`。无需为基本读取提供API密钥。
4. 视频号单独读 `references/video-channels.md`。res-downloader安装、证书、微信播放和代理核对按说明由用户参与，不自动改变系统配置。
5. 用现成文档及本地视频实测；脚本列出的PDF/图片要再次读取。改Office存量文件时再按OfficeCLI说明安装编辑后端。

0.2.0增加视频入口和视频号流程；未包含第三方抓取应用或转写模型。
