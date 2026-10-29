---
name: gpt-image
description: TikBit 对话生图。用户要求生成图片、海报、封面、插画，或参考图编辑、换背景、合成、批量出图时，读取本 Skill 并执行本地 CLI。
---

# GPT 对话生图

## 调用入口

- 规范脚本：`~/.tikbit/gpt-image/gpt-image.js`；Windows 把 `~` 展开成当前用户目录。
- Node 优先使用工作台自带的 `~/.tikbit/runtime/bin/node.exe`（Windows）或 `~/.tikbit/runtime/bin/node`（macOS），存在时直接调用；否则使用 PATH 中的 `node`，也可检查旧版 `~/.local/bin/node`。
- 首次调用先执行 `node "<用户目录>/.tikbit/gpt-image/gpt-image.js" --check`：仅本机检查，不联网、不计费，也不证明模型权限或真实生图成功。
- 找不到规范脚本时，不要直接宣称不能生图；检查 `~/.tikbit/tools/gpt-image/` 和其内 `gpt-image/` 旧嵌套目录的 `install.cjs`。若有，运行 `node "<该目录>/install.cjs" --vault "<当前知识库>"`。旧包没有修复器则提示需更新本地生图工具。

## 凭据与模型

- 优先使用专用 `GPT_API_KEY/GPT_BASE_URL` 与已有 `~/.tikbit/gpt-image/config.json`。
- 未设置专用密钥时，可成对复用当前工作台传入的 Claude/GPT 凭据，或修复器登记的工作台本机配置；仅认可 HTTPS 的 `tikbit.ai`。不会把工作台令牌发到自定义网址。
- 不读取、不修改官方用户目录中的凭据；不把密钥发到聊天，不打印配置原文。缺配置提示本机修复；401/403、模型权限、路径不存在分别报告，不把配置检查成功说成 API 可用。
- 新装或未指定模型时默认 2.5 精细档 `gpt-image-2.5-sunburst`；已有配置、环境变量和命令行明确指定的模型优先，不覆盖用户保存的旧模型。可显式 `--model 精细` / `--model 快速`，分别对应 TikBit 网关别名 `gpt-image-2.5-sunburst` / `gpt-image-2.5-flare`；需要旧模型时显式指定 `--model gpt-image-2`。不声称别名是 OpenAI 官方型号，不根据旧文档认定某模型下架，不擅自切换模型或反复付费重试。

## 生成步骤

1. 确认画面、尺寸、张数、参考图、输出位置；用户已说明的不用再问。只问创意或提示词时不调用 API。
2. 生成会计费。需求未明确允许生成时先确认；安装、排查、`--check` 不调用生成接口。
3. 执行示例：`node "<用户目录>/.tikbit/gpt-image/gpt-image.js" "画面描述" --model 精细 --size 1024x1024 --output "项目/图片/成品.png"`。
4. 参考图加 `--reference "参考图.png"`，多图用逗号分隔。多张采用小批次；单张落盘检查后再接入项目。
5. 尊重本轮指定的图片输出目录；没有指定时使用对应项目素材目录。已有同名图片自动加序号，不覆盖原图，不移动参考图。
6. 回读文件，报告知识库相对路径，以 `![[项目/图片/成品.png]]` 展示。未经文件检查，不报告生成成功。
