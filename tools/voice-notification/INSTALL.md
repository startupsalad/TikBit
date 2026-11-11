# 任务语音通知工具包安装与更新

当前版本：**0.3.3**。这是工作台的可选独立工具；插件升级不会自动更新传统安装的语音脚本。

0.3.3把完成done、授权perm、选择／确认ask（含可选及异步问题）、必须人工介入stuck四类规则合并到实际Claude／GPT配置目录。显式`CLAUDE_CONFIG_DIR`／`CODEX_HOME`优先；未显式设置时维护已存在的标准及隔离目录，无客户端目录才使用标准默认。只替换工具自有托管块，保留个人说明、音色、音频和已有自定义Hook，写入失败回滚。

配套工作台插件可在真实授权、选择、异步问题和计划确认呈现后自动提醒；仅设置入口安装的兼容工具包启用，传统脚本不冒充已接入。未安装、未绑定、已关闭或重复归属保持静音；取消和回答后不再补播。Claude对应Hook由管理模式去重，文字提问仍需主动ask，完成仍由主对话主动done。运行中旧会话是否加载须另验；升级工具与升级配套插件是两步，不承诺旧插件自动取得原生回调。

## 对外名称

安装说明、环境检测结果、YOLO 开关提问和验收汇报统一使用 **TikBit** 或 **TikBit AI 工作台**。兼容路径 `.claudian`、插件 ID `tikbit-claudian` 和音频目录 `claudian_multitab` 保持原样；它们不是界面名称，不据此改称旧名称，不重命名用户目录。

## 首次安装

先读 `📖 使用说明.md` 和 `给AI的安装指令.md`，介绍用途并征得用户同意后安装。Windows 和 macOS 使用各自脚本。只通知主对话的最终完成或确需人工处理；子代理/后台分支不得直接通知用户，不恢复 Stop 自动完成播报。

- 未设置 `TIKBIT_VAULT_ROOT`：保留独立客户端的通用提醒。独立 Codex 会只读本机 `CODEX_HOME`、`~/.codex` 或 `~/.tikbit/codex` 中的首行 session_meta；已验证主线程才放行，子线程或身份不明静音。
- 已设置 `TIKBIT_VAULT_ROOT`：只允许当前可见标签的唯一精确匹配，不猜新标签编号、不使用历史登记表。新对话 ID 未落盘、标签已关闭或重复匹配时静音。
- `TIKBIT_VOICE_SUPPRESS=1`：整个分支静音，优先级最高；可用于受控的 Claude/其他客户端子任务。独立 Claude/第三方客户端没有统一可靠的子代理标志，必须同时落实主/子任务规则，不能把 Codex 检测说成覆盖所有客户端。
- macOS 身份校验需要 Python 3.8+，无需第三方库；缺少 Python 时身份校验调用静音，普通无身份客户端的通用提醒不受影响。Windows 引擎不依赖 Python。

## 更新已安装用户（无需重装工作台）

0.3.2修复TikBit数据迁移后提醒静音，兼容旧目录及插件`dataFolder`自定义目录。多标签调用应传入`TIKBIT_VAULT_ROOT`（知识库绝对路径）；Obsidian使用自定义配置目录时，同时传入`TIKBIT_OBSIDIAN_CONFIG_DIR`（知识库内单层目录名，默认`.obsidian`）。安装到设置入口时，把这两个值传给实际调用语音脚本的子进程；不要只在终端配置里设置，也不要把用户路径写进工具源码。

脚本从选定配置目录的`plugins/tikbit-claudian/data.json`读取可见标签与`dataFolder`。当前`<配置目录>/tikbit`或显式自定义数据目录一旦选定，不再逐文件回退到旧`.claudian`备份。老插件保留旧布局支持。新插件数据尚未准备好、配置损坏或归属不明时保持静音。

在新工具包目录先检查，再更新：

```bash
python update.py --check
python update.py
# 有两处安装或使用自定义目录时，显式指定目标：
python update.py --target "安装语音脚本的目录" --check
python update.py --target "安装语音脚本的目录"
```

更新器替换已安装的公开版引擎和VERSION，并安全合并四类规则；已存在且指纹受支持的Windows notify-gate按需更新，未安装gate不新增。保留音色、音频、自定义钩子及标记。自动检测`~/.claude` / `~/.task-voice`，存在歧义停止；接收公开0.3.0／0.3.1／0.3.2、已核实官方旧包及当前版。私有改动、未知旧版拒绝整次更新，不提供强制覆盖。引擎备份在`backups/voice-notification/`，规则备份在`backups/rules/`；规则失败同时恢复本轮引擎写入。重复执行不新增无变化备份，`--check`不写文件。

命令行更新现在自动处理安装指令第5步的规则；安装AI应回读两边实际目标。脚本下次调用生效；规则／环境／Hook是否被旧会话加载须分别验证。不要把Claude Hook事件写进GPT配置并宣称GPT已自动接入。

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
