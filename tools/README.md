# 工具目录

每个子目录是一个独立工具包，包含自己的 `INSTALL.md` 和使用说明。完整元数据见仓库根目录的 [`catalog.json`](../catalog.json)。

## 推荐等级

仓库只使用三档：**必装、推荐、按需**。安装前先检查目标目录、Skill、配置和指令标记，已安装的工具不要重复安装。

| 目录 | 推荐等级 |
|:---|:---:|
| `must-skills`、`html-page`、`document-reader`、`gpt-image` | 必装 |
| `voice-notification`、`writing-humanizer` | 推荐 |
| 其余目录 | 按需 |

`context-reminder` 已集成到工作台插件，因此不再列在工具目录和目录清单中。

## 使用方式

把仓库地址交给 AI 助手，让它读 `catalog.json`，按三档介绍后等待确认，再读取对应工具的 `INSTALL.md`：

```text
https://github.com/startupsalad/TikBit
```
