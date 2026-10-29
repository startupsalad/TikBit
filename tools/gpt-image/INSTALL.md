# GPT 生图工具安装与修复

需要 Node.js 22+（工作台自带）。安装前说明用途与行为，获得用户同意；安装不调用生图接口、不计费。

1. 下载本目录完整内容到本机工具目录，不复制示例密钥，不在聊天中索取或发送真实密钥。
2. 执行 `node install.cjs --vault "知识库完整路径"`；也可 `node install.cjs --discover` 从 Obsidian 注册表发现已登记库，不全盘扫描。
3. 工具落到 `~/.tikbit/gpt-image/`；Claude/GPT 常驻 Skill 分别落到 `~/.tikbit/claude/skills/gpt-image/`、`~/.tikbit/codex/skills/gpt-image/`。工作台使用隔离配置目录；已有知识库入口规则、笔记和插件状态均不改写。
4. 已有 config.json、密钥、模型、输出图片和旧嵌套安装保留。首次创建空密钥配置；仅登记工作台配置路径，不复制令牌。工作台换密钥后按当前本机配置读取，不缓存旧密钥。
5. 从目标库重新开启 AI 对话，执行 `node "<用户目录>/.tikbit/gpt-image/gpt-image.js" --check`。成功只证明本机配置可用，不证明账号模型权限、余额或真实生成成功。

自定义服务必须在本机自行设置完整的 GPT_API_KEY/GPT_BASE_URL；不会把 TikBit 工作台令牌发送给自定义网址。修复器不读取官方 Claude/Codex 账号配置，不修改凭据或全局 hooks。

已有用户无需重装工作台，可单独运行本目录 install.cjs。JSON 损坏、路径不可写或安装包缺文件时会失败并返回非零，不静默重置用户配置。付费生成测试、上传和发布另行确认。
