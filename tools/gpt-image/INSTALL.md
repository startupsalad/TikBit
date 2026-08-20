# GPT 生图工具包安装

本工具包仅面向 **TikBit AI 工作台**，支持 Windows 和 macOS。安装动作由 AI 执行，用户不需要手动复制文件或运行命令。

## 给 TikBit AI 的安装指令

1. 先向用户说明：这是对话式 GPT 生图工具包，会调用用户自己的 API 额度；安装不会自动产生费用。
2. 确认用户同意安装后，检查 Node.js 版本：

```text
node --version
```

需要 Node.js 18 或更高版本。TikBit 工作台自带 Node 时直接使用；没有时提示用户安装 Node.js 18+，不要静默下载未知二进制。

3. 将本目录的 `gpt-image.js` 复制到用户目录：

```text
Windows: %USERPROFILE%/.tikbit/gpt-image/gpt-image.js
macOS:  ~/.tikbit/gpt-image/gpt-image.js
```

同时将 `config.example.json` 复制为同目录的 `config.json`（只在 `config.json` 不存在时创建）。

4. 将本目录 `SKILL.md` 注册到 TikBit AI 工作台的工具/Skill 目录，使后续对话可按触发规则自动调用。不要注册到其他 AI 客户端的全局配置。

5. 首次需要生图时再配置 API。优先使用环境变量 `GPT_API_KEY`、`GPT_BASE_URL`；也可由 AI 将用户提供的值写入本机 `config.json`。不得在聊天记录、仓库或日志中回显完整密钥。

6. 安装验证：运行无密钥检查（不会发起网络请求）：

```text
node %USERPROFILE%/.tikbit/gpt-image/gpt-image.js
```

预期结果是提示“GPT 生图功能还没配置 API”，而不是 Node 语法错误。完成后告诉用户：以后直接在 TikBit 对话里说“生成一张……”即可。

## AI 调用入口

```text
node ~/.tikbit/gpt-image/gpt-image.js "图片描述" --size 1024x1024 --output "输出路径.png"
node ~/.tikbit/gpt-image/gpt-image.js "修改描述" --reference "参考图.png" --output "输出路径.png"
node ~/.tikbit/gpt-image/gpt-image.js --batch "任务清单.txt" --concurrency 3
```

Windows 请把 `~/.tikbit` 展开为用户目录，或使用 PowerShell 可解析的完整路径。输出路径优先使用当前项目/知识库内的明确相对路径，避免把交付图片散落在工具目录。

## API 配置示例

```json
{
  "base_url": "https://tikbit.ai/v1",
  "api_key": "用户自己的密钥",
  "image_model": "gpt-image-2"
}
```

`config.example.json` 只有空密钥示例；实际密钥由用户自行提供和保管。
