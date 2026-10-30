# 任务语音通知工具包 - AI 安装指令（统一版）

> **给 AI 的话**：这是跨平台、跨客户端的语音通知工具包。会自动检测运行环境，智能选择最佳版本：
> - 检测到 **Obsidian Claudian 插件** → 安装多标签识别版（播"对话N搞定啦"）
> - 其他环境（Claude Code 桌面端 / VSCode / CodeBuddy 等） → 安装通用版

---

## 0.3.1 安装与升级边界

这是可选工具，不是插件默认功能。升级已安装用户请优先执行 `python update.py --check`，确认后执行 `python update.py`，必要时显式指定 `--target`；不要重跑整套安装覆盖用户选择、私有引擎或自定义钩子。私有改版请备份后人工合并。脚本更新与 AI 记忆规则须同时处理；插件 OTA 不会替换这套引擎。

只允许主对话发出用户提醒。后台子代理不得调用 done/stuck/ask/perm/say 等模式，不得因为自己的子任务完成就宣布整项任务完成。受控子分支应设置 `TIKBIT_VOICE_SUPPRESS=1`，不要把该变量设置到主对话或全局用户环境。Codex子线程有原生身份校验；独立Claude/第三方客户端仍须由任务规则及显式分支静音兜住，不虚称全客户端自动识别。

## 第 1 步：环境检测与版本选择

运行以下检测逻辑（**不要跳过**）：

```python
from pathlib import Path
import os

# 获取当前工作目录（应该是知识库根目录）
cwd = Path.cwd()

# 检测 Claudian 插件特征
claudian_sessions = cwd / ".claudian" / "sessions"
claudian_data = cwd / ".obsidian" / "plugins" / "tikbit-claudian" / "data.json"

is_claudian = claudian_sessions.exists() and claudian_data.exists()

if is_claudian:
    print("✅ 检测到 Obsidian Claudian 插件环境")
    print("📦 将安装：多标签识别版（支持\"对话1搞定啦\"等多标签播报）")
    version = "claudian"
else:
    print("✅ 检测到通用环境（Claude Code / VSCode / CodeBuddy 等）")
    print("📦 将安装：通用版")
    version = "generic"

print(f"\n选定版本: {version}")
```

---

## 第 2 步：复制引擎和音频到本机

### A. 复制通用引擎（所有环境都需要）

```bash
# Windows
cp "engine/notify-voice.ps1" "~/.claude/"
cp "engine/pick-voice.ps1" "~/.claude/"

# Mac (如果是 Mac 环境，改用 .sh)
cp "engine/notify-voice.sh" "~/.claude/"
cp "engine/pick-voice.sh" "~/.claude/"
```

### B. 复制音频文件

```bash
mkdir -p ~/.claude/voice_clips
cp -r voice_clips/* ~/.claude/voice_clips/
```

复制完的目录结构（**结构别改，脚本按这个路径找文件**）：

```
~/.claude/voice_clips/
├── xiaoxiao/            # 四种音色，各含 done/ask/perm/stuck/error/wait.mp3
├── xiaoyi/
├── yunxi/
├── yunyang/
└── claudian_multitab/   # 多标签音频，dialog1~10 × 6 种话术 = 60 个
```

### C. 可选的多标签集成

多标签集成需要用户自行设置 `TIKBIT_VAULT_ROOT` 环境变量，指向自己的知识库路径（见第 3 步）。本公开版不携带任何特定用户的知识库路径。

播报时按 `voice_clips/claudian_multitab/dialog<N>_<话术>.mp3` 取音频，六种话术 `done / perm / stuck / wait / ask / error` 都带编号。找不到音频也不会退成"没编号"——脚本会用 SAPI 直接念出"对话N，……"，编号信息一定保留。

### D. 开超过 10 个标签时补音频

成品带 1~10 号。用户常开更多标签就跑 `engine/gen-clips.py` 补：

```bash
pip install edge-tts imageio-ffmpeg     # imageio-ffmpeg 自带二进制，不用装系统 ffmpeg
python engine/gen-clips.py --start 11 --tabs 12

# 只补某几种话术（不重跑已有的）
python engine/gen-clips.py --kinds stuck,wait
```

跑完每个文件会自检打印 `OK 48kbps`，出现 `WARN: 首帧 64kbps` 就是编码参数被改坏了。

⚠️ **别手工拿 ffmpeg 默认参数转 mp3**。Windows 版播放走 MCI，它算长度用「文件大小 ÷ 首帧码率」而不是真解码，`play ... wait` 又依赖这个长度决定何时 close，长度算错声音就被掐断。必须锁 CBR（`-b:a 48k`，不能用 `-q:a`）并禁 Xing 头帧（`-write_xing 0`）；另外前面焊 350ms 静音抵声卡冷启动延迟。三条都写进 `gen-clips.py` 了，直接用它最稳，细节见该脚本文件头注释。

---

## 第 3 步：设置知识库路径（**仅 Claudian 版需要**）

如果 `version == "claudian"`，给用户设一个 `TIKBIT_VAULT_ROOT` 环境变量指向知识库根目录。**脚本不再内嵌任何路径**，不用改脚本内容。

### 3.1 设置环境变量（用户级、永久生效）

```powershell
# Windows：把路径换成用户知识库根目录的实际路径（正斜杠或反斜杠都行）
[Environment]::SetEnvironmentVariable(
  "TIKBIT_VAULT_ROOT",
  "C:/Users/你的用户名/path/to/vault",
  "User")
```

```bash
# Mac：写进 shell 配置
echo 'export TIKBIT_VAULT_ROOT="/Users/你的用户名/path/to/vault"' >> ~/.zshrc
```

> 设完要**重启 AI 客户端**（甚至重新登录）才读得到新环境变量。未设置时按独立模式处理；已设置却路径错误或身份不唯一时静音，不退到匿名播报。

### 3.2 验证语法和取值

```powershell
# 语法检查（无输出即通过）
powershell -NoProfile -ExecutionPolicy Bypass -Command "
  [void][System.Management.Automation.Language.Parser]::ParseFile(
    (Resolve-Path ~/.claude/notify-voice.ps1), [ref]\$null, [ref]\$errs)
  if (\$errs) { \$errs } else { 'Parser OK' }"

# 只读检查：allowed=true且tab>=1才是当前可见主对话；不再点源脚本猜号
powershell -NoProfile -ExecutionPolicy Bypass -File "$HOME/.claude/notify-voice.ps1" -Mode done -DryRun
# Mac：bash "$HOME/.claude/notify-voice.sh" done --dry-run
```

---

## 第 4 步：接钩子到 Claude Code 配置

编辑 `~/.claude/settings.json`（**先备份原文件**）：

### A. 通用版钩子配置

```json
"hooks": {
  "PreToolUse": [
    {
      "matcher": "AskUserQuestion|ExitPlanMode",
      "hooks": [
        {
          "type": "command",
          "command": "powershell.exe -NoProfile -ExecutionPolicy Bypass -File \"$HOME/.claude/notify-voice.ps1\" -Mode ask 2>/dev/null || true"
        }
      ]
    }
  ],
  "Notification": [
    {
      "hooks": [
        {
          "type": "command",
          "command": "powershell.exe -NoProfile -ExecutionPolicy Bypass -File \"$HOME/.claude/notify-voice.ps1\" -Mode notify 2>/dev/null || true"
        }
      ]
    }
  ]
}
```

### B. Claudian 版额外钩子（**开 YOLO 就别装，会误报**）

**先问用户一句：YOLO 模式是开着的吗？**（Claudian 插件 UI 顶部那个 YOLO 开关）

| 用户情况 | 怎么配 |
|:---|:---|
| **开着 YOLO**（推荐，多数人） | **跳过本节**，只用上面 A 的配置。YOLO 下工具自动授权、根本不弹授权窗，装了 notify-gate 只会误报"需要授权一下" |
| **关着 YOLO**（手动授权每个操作） | 按下面加 notify-gate 的两个钩子 |

下面这套仅"关着 YOLO"时才加 —— PreToolUse 打标记、PostToolUse 清标记，超时没清掉说明授权窗挂着，才播报：

```json
"hooks": {
  "PreToolUse": [
    {
      "matcher": "AskUserQuestion|ExitPlanMode",
      "hooks": [
        {
          "type": "command",
          "command": "powershell.exe -NoProfile -ExecutionPolicy Bypass -File \"$HOME/.claude/notify-voice.ps1\" -Mode ask 2>/dev/null || true"
        }
      ]
    },
    {
      "matcher": "*",
      "hooks": [
        {
          "type": "command",
          "command": "powershell.exe -NoProfile -ExecutionPolicy Bypass -File \"$HOME/.claude/notify-gate.ps1\" -Mode arm 2>/dev/null || true"
        }
      ]
    }
  ],
  "PostToolUse": [
    {
      "matcher": "*",
      "hooks": [
        {
          "type": "command",
          "command": "powershell.exe -NoProfile -ExecutionPolicy Bypass -File \"$HOME/.claude/notify-gate.ps1\" -Mode clear 2>/dev/null || true"
        }
      ]
    }
  ],
  "Notification": [
    {
      "hooks": [
        {
          "type": "command",
          "command": "powershell.exe -NoProfile -ExecutionPolicy Bypass -File \"$HOME/.claude/notify-voice.ps1\" -Mode notify 2>/dev/null || true"
        }
      ]
    }
  ]
}
```

**注意**：
- Mac 环境把 `powershell.exe` 改成 `bash`，把 `.ps1` 改成 `.sh`
- Windows 路径请使用当前用户的 `$HOME/.claude/`；不要写死用户名或机器路径

---

## 第 5 步：更新 AI 记忆规则

让 AI 记住“只有主对话整轮完成才主动播报”的规则；已有用户必须替换旧的无条件完成规则。

告诉用户的 AI（通过自然语言，不需要手动编辑文件）：

> **请记住**：只有直接面向用户的主对话，在整轮回答全部完成（所有步骤跑完、验证和最终答复均已就绪）时，才主动运行一次：
> 
> ```bash
> powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$HOME/.claude/notify-voice.ps1" -Mode done
> ```
> 
> **子代理/后台任务禁止直接播报**：子任务做完只把结果交给主对话，不能喊 done 或改用 say/perm 绕过；确需人工介入也由主对话统一提醒。受控分支可设置 `TIKBIT_VOICE_SUPPRESS=1`（仅分支，不设全局）。
>
> **中途动文件不单独喊，攒到最后整轮收尾时喊一次**——用户要验收的是最终结果，不是某个中间步骤。纯聊天/纯问答不喊。编号解析失败不手填、不猜别的标签，不恢复 flag/Stop 自动播报。
>
> macOS收尾命令改为 `bash "$HOME/.claude/notify-voice.sh" done`；使用install.py安装的用户将目录改为 `~/.task-voice/`。

---

## 第 6 步：重启客户端

- **Obsidian Claudian** → 重启 Obsidian
- **Claude Code 桌面端 / VSCode** → 重启客户端或终端

---

## 第 7 步：测试

### 测试完成播报（所有版本）

```bash
powershell -ExecutionPolicy Bypass -File ~/.claude/notify-voice.ps1 -Mode done
```

- **通用版**：应该播"搞定啦"
- **Claudian 版**：应该播"对话N搞定啦"（N 是调用者对应的真实可见标签编号，不跟随你临时切到的活动标签）

### 测试决策提醒（所有版本）

让 AI 随便跑个命令，如果弹选择窗口（AskUserQuestion），应该播"需要你拿个主意"。

### 无声核对身份

运行第3.2节的DryRun，检查 `allowed`、`tab`、`reason`。通用分发版不写私有的voice-notify.log，不要求用户上传完整会话或日志。验证主对话放行后再按用户同意的方式试听一次；对子线程测试只检查拒播，禁止拿它反复喊“搞定”。

---

## 故障排查

### 通用版：播的是机械音

说明 mp3 播放失败，降级到 SAPI。检查：
- `~/.claude/voice_clips/<音色>/done.mp3` 是否存在
- 重新复制音频文件

### Claudian 版：没有播报或编号不对

先运行只读 DryRun（Windows `-Mode done -DryRun`，Mac `done --dry-run`）。`no-unique-visible-tab` 表示当前线程不属于唯一可见标签：可能是后台子任务、新主对话ID未落盘、已关闭标签、重复/损坏数据。新版会静音，不猜最新空标签、不按历史数量造号。等主对话有精确归属后由主对话正常收尾；不要清空历史表或伪造环境ID绕过门禁。

未启用多标签的独立Codex，`codex-context-unverified` 表示有界原生元数据检查未能确认主线程；检查 `CODEX_HOME` 和对应线程首行session_meta，不输出完整会话内容。`codex-subagent` 是后台子任务，静音正常。Mac的 `python3-required` 表示需先安装Python3.8+；不要退回猜号。普通不带Codex身份的其他客户端仍可通用播报。

### 声音开头/结尾被切掉（"对话三搞定啦"听成"话三搞定啦"）

用播放器单独打开 mp3 是正常的、只有脚本播出来才缺字 —— 那就不是音频本身的问题，是 Windows MCI 的两个老毛病。成品包已修，**自己重新生成过音频才会碰到**：

| 症状 | 原因 | 怎么修 |
|:---|:---|:---|
| 开头缺字 | 声卡省电态要 300~500ms 才转起来，`open` 完立刻 `play` 就把开头吞了 | 文件头焊 350ms 静音（`adelay=350:all=1`），被吞掉的就是静音 |
| 结尾被掐 | MCI 算长度用「文件大小 ÷ **首帧**码率」而非真解码，`play ... wait` 依赖这个长度决定何时 close。VBR 或带 Xing 头帧都会让它算错 → 提前 close | 锁 CBR `-b:a 48k`（不能用 `-q:a`）+ 禁 Xing `-write_xing 0` |

用 `engine/gen-clips.py` 生成就三条全带上了。**自检办法**：MCI 报的长度应该 ≈ 文件大小 ÷ 6000 ÷ 1000 秒，差 <50ms；差成 0.75 倍就是 Xing 头帧混进来了（48kbps/24000Hz 的 MPEG-2 帧只有 144 字节、装不下 Xing 的 100 字节 TOC，ffmpeg 会把首帧提到 64kbps，MCI 读到 64 就按 8000 B/s 算整个文件）。也可以直接看首帧字节：`FF F3 64 ...` 对，`FF F3 84 ...` 错。

### 一直误报"需要授权一下"，但根本没弹窗

**十有八九是开了 YOLO 还装了 notify-gate**。YOLO 下工具自动授权、不会弹授权窗，notify-gate 那套"超时未清标记就报警"的判定必然误触发。

修法：从 `settings.json` 删掉 notify-gate 的两条钩子（PreToolUse 的 `arm` + PostToolUse 的 `clear`，matcher 都是 `*`），保留 `AskUserQuestion|ExitPlanMode` 那条，重启客户端。清一下残留标记：

```bash
rm -f ~/.claude/.voice_gate/*.pending
```

删掉后仍然保留的提醒：AI 让你选方案、确认计划时照样播报 —— 这才是 YOLO 下真正会卡住等人的场景。

---

## 💡 强烈建议：开启 YOLO 模式（Claudian 用户）

**装完记得告诉用户开 YOLO**，在 Claudian 插件 UI 顶部那个 **YOLO** 开关。

**为什么建议开**：
- 不用再手动授权 Write/Edit/Bash，工作流不被打断
- 知识库外的路径操作（写桌面、读系统文件）也不卡了
- 配合"跳过 notify-gate"的配置，语音提醒零误报

**开了 YOLO 后语音还剩什么**：
- ✅ 干完活播"对话N搞定啦" —— 主力功能，照常
- ✅ 要你选方案/确认计划播"需要你拿个主意" —— 真正会卡住的场景，照常
- ❌ 授权提醒 —— 用不上了（因为不再有授权窗），别装 notify-gate

**注意**：YOLO 下 AI 能自由操作文件系统。不放心就保持关闭、按第 4 步 B 装 notify-gate，代价是每个越界操作都要手点一次授权。

---

## 回退与卸载

### 卸载语音通知

```bash
rm -rf ~/.claude/notify-voice.ps1 ~/.claude/notify-gate.ps1 ~/.claude/pick-voice.ps1
rm -rf ~/.claude/voice_clips
```

然后从 `settings.json` 移除所有相关钩子，重启客户端。

---

## 技术说明

### 为什么中文话术在脚本里是 base64？

PowerShell `.ps1` 被 Git Bash 以 GBK 解析时中文会乱码。所以脚本里的中文播报话术一律 base64 存、运行时解码（`$SFX`/`$PRE`/`$NUMS` 三张表）。知识库路径不走这套 —— 它从 `TIKBIT_VAULT_ROOT` 环境变量读，不进脚本正文。

### 为什么 Claudian 版能识别标签编号？

读 Claudian 插件自己的数据文件，**顺序是从标签列表出发**（不是扫 sessions 目录，那样在多对话下会拿错）：

1. 优先使用 `CODEX_THREAD_ID`，否则使用 `CLAUDE_CODE_SESSION_ID`，避免继承的旧Claude变量串号
2. 读 `.obsidian/plugins/tikbit-claudian/data.json` 的 `tabManagerState.openTabs` 数组，数组顺序 = 界面上标签顺序
3. 按顺序遍历，用每个元素的 `conversationId` 去读 `.claudian/sessions/<id>.meta.json`
4. 该 meta 的 `sessionId`、`providerState.providerSessionId` 或 `providerState.threadId` 唯一命中当前会话/thread → 返回界面编号（第1个元素=对话1）
5. 未命中或重复命中 → 静音。绝不按更新时间猜新标签，也不从历史登记表分配编号
6. 播 `voice_clips/claudian_multitab/dialog<N>_<话术>.mp3`；音频缺失就用 SAPI 念"对话N，……"，编号绝不丢

**零侵入**：不改插件源码，只读已有数据文件，插件更新不受影响。

---

**安装完成**！现在 AI 干完活会主动喊你，卡住等你决策时也会提醒。

**音色**：默认使用晓晓（zh-CN-XiaoxiaoNeural）神经语音，自然流畅。如需切换音色，运行双击 `选择语音.bat`（Windows）或 `选择语音.command`（Mac）。

**更新日期**：2026-10-30（0.3.1：双平台子任务门禁、唯一精确编号、独立模式兼容、无声检查及安全更新器）
