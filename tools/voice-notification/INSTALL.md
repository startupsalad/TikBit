# 任务语音通知工具包安装与更新

当前版本：**0.3.1**。这是工作台的可选独立工具，不是插件默认内置功能；插件升级不会自动更新本机语音脚本。

## 首次安装

先读 `📖 使用说明.md` 和 `给AI的安装指令.md`，介绍用途并征得用户同意后安装。Windows 和 macOS 使用各自脚本。只通知主对话的最终完成或确需人工处理；子代理/后台分支不得直接通知用户，不恢复 Stop 自动完成播报。

- 未设置 `TIKBIT_VAULT_ROOT`：保留独立客户端的通用提醒。独立 Codex 会只读本机 `CODEX_HOME`、`~/.codex` 或 `~/.tikbit/codex` 中的首行 session_meta；已验证主线程才放行，子线程或身份不明静音。
- 已设置 `TIKBIT_VAULT_ROOT`：只允许当前可见标签的唯一精确匹配，不猜新标签编号、不使用历史登记表。新对话 ID 未落盘、标签已关闭或重复匹配时静音。
- `TIKBIT_VOICE_SUPPRESS=1`：整个分支静音，优先级最高；可用于受控的 Claude/其他客户端子任务。独立 Claude/第三方客户端没有统一可靠的子代理标志，必须同时落实主/子任务规则，不能把 Codex 检测说成覆盖所有客户端。
- macOS 身份校验需要 Python 3.8+，无需第三方库；缺少 Python 时身份校验调用静音，普通无身份客户端的通用提醒不受影响。Windows 引擎不依赖 Python。

## 更新已安装用户（无需重装工作台）

在新工具包目录先检查，再更新：

```bash
python update.py --check
python update.py
# 有两处安装或使用自定义目录时，显式指定目标：
python update.py --target "安装语音脚本的目录" --check
python update.py --target "安装语音脚本的目录"
```

更新器仅替换已安装的公开版 notify-voice 引擎及 VERSION；保留音色选择、音频、钩子、自有配置及标记。自动检测 `~/.claude` / `~/.task-voice`，存在歧义则停止；仅自动接收已知公开0.3.0原版、已核实的2026-08-06官方OSS原包引擎或当前版（兼容换行/BOM差异）；私有改动、未知旧版拒绝覆盖，不提供盲目强制覆盖。脚本差异备份在目标目录 `backups/voice-notification/时间戳/`，无需备份对话历史。更新失败会恢复已替换文件；确认无误前保留备份。

还必须按安装指令第5步更新 AI 规则：只由主对话播报，子代理不得播报。脚本替换后下一次调用即生效；只在改了环境或钩子时重启客户端。

## 无声检查

Windows：`powershell -NoProfile -ExecutionPolicy Bypass -File "安装目录/notify-voice.ps1" -Mode done -DryRun`。

macOS：`bash "安装目录/notify-voice.sh" done --dry-run`。

返回 JSON 的 `allowed`、`tab`、`reason`，不播放、不写标记、不改历史表。`allowed=false` 时先核对归属，不要用手填编号绕过。

## 开发验收与本地打包

以下命令在Git源码目录执行，安装用ZIP不包含开发测试和打包器。

```bash
python -m unittest discover -s tests -v
python build_packages.py --output "系统临时目录/TaskVoice候选包"
```

测试拦截所有音频；Windows上用PowerShell与Git Bash验证两引擎逻辑不代表macOS真实播放已验。打包器仅生成两平台TaskVoice候选ZIP，不上传、不覆盖已有包。正式发布还需确认Git推送及下载单包、全家桶的更新范围。
