# TikBit 对话生图工具 1.2.0

零依赖 Node.js CLI，支持文生图、参考图编辑和小批次任务；工作台内通过 `gpt-image` Skill 调用。

```sh
node install.cjs --vault "知识库完整路径"
node ~/.tikbit/gpt-image/gpt-image.js --check
node ~/.tikbit/gpt-image/gpt-image.js "画面描述" --model 精细 --output "项目/图片/成品.png"
```

## 1.2.0 修复

- 统一执行入口，安装与老用户修复共用同一安装器；Windows/macOS 均支持。
- 两引擎常驻 Skill；只登记本机工作台配置位置，不复制令牌、不覆盖已有密钥和图片。
- 专用图片配置优先；工作台凭据只成对用于受信任的 TikBit HTTPS 端点。
- 新装或未指定模型时默认 2.5 精细档 `gpt-image-2.5-sunburst`；快速档可用 `--model 快速` 选择 `gpt-image-2.5-flare`。已有配置、环境变量及命令行明确选择仍优先，不覆盖用户保存的旧模型。以上为 TikBit 网关别名；模型列表可见不等于分组生成权限可用。
- `--check` 为本机离线诊断；同名图片自动加序号；不要求用户在聊天里发送密钥。

专用配置位于 `~/.tikbit/gpt-image/config.json`，环境变量 GPT_API_KEY/GPT_BASE_URL/GPT_IMAGE_MODEL 可覆盖对应项。`--model` 优先级最高。

`--size` 指定尺寸，`--reference` 指定逗号分隔参考图，`--batch` 指定每行“文件名 | 图片描述”的任务清单，`--concurrency` 控制并发。生成前确认需求与费用；验证配置和安装不会调用生成接口。

安装详情见 INSTALL.md。离线回归：`node --test integration.test.cjs`。
