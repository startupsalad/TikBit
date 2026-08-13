# 任务语音通知工具包 - AI 安装指令（统一版）

> **给 AI 的话**：这是跨平台、跨客户端的语音通知工具包。会自动检测运行环境，智能选择最佳版本：
> - 检测到 **Obsidian Claudian 插件** → 安装多标签识别版（播"对话N搞定啦"）
> - 其他环境（Claude Code 桌面端 / VSCode / CodeBuddy 等） → 安装通用版

---

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
└── claudian_multitab/   # 可选：由用户自行生成的多标签音频
```

### C. 可选的多标签集成

多标签集成需要用户自行设置 `TIKBIT_VAULT_ROOT` 环境变量，指向自己的知识库路径。本公开版不携带任何特定用户的知识库路径。

多标签版播报时按 `voice_clips/claudian_multitab/dialog<N>_done.mp3` 取音频，找不到就自动降级播通用 `done`，不会报错。

### D. 开超过 6 个标签时补音频

成品只带 1~6 号。用户常开更多标签就跑 `engine/gen-clips.py` 补：

```bash
pip install edge-tts imageio-ffmpeg     # imageio-ffmpeg 自带二进制，不用装系统 ffmpeg
python engine/gen-clips.py --start 7 --tabs 12
```

跑完每个文件会自检打印 `OK 48kbps`，出现 `WARN: 首帧 64kbps` 就是编码参数被改坏了。

⚠️ **别手工拿 ffmpeg 默认参数转 mp3**。Windows 版播放走 MCI，它算长度用「文件大小 ÷ 首帧码率」而不是真解码，`play ... wait` 又依赖这个长度决定何时 close，长度算错声音就被掐断。必须锁 CBR（`-b:a 48k`，不能用 `-q:a`）并禁 Xing 头帧（`-write_xing 0`）；另外前面焊 350ms 静音抵声卡冷启动延迟。三条都写进 `gen-clips.py` 了，直接用它最稳，细节见该脚本文件头注释。

---

## 第 3 步：修改知识库路径（**仅 Claudian 版需要**）

如果 `version == "claudian"`，**必须**修改脚本中的知识库路径 base64：

### 3.1 生成当前知识库路径的 base64

```python
import base64
from pathlib import Path

vault_path = str(Path.cwd()).replace("\\", "/")  # 当前工作目录
vault_b64 = base64.b64encode(vault_path.encode('utf-8')).decode()

print(f"知识库路径: {vault_path}")
print(f"Base64: {vault_b64}")
```

### 3.2 替换两个脚本中的 base64

编辑以下两个文件，找到 `$vaultB64 = "QzovVXNlcnMv..."` 这一行，把双引号里的内容替换成上面生成的 base64：

- `~/.claude/notify-voice.ps1`
- `~/.claude/notify-gate.ps1`

### 3.3 验证语法

```bash
# Windows PowerShell 语法检查
powershell -NoProfile -ExecutionPolicy Bypass -Command ". '~/.claude/notify-voice.ps1'"
powershell -NoProfile -ExecutionPolicy Bypass -Command ". '~/.claude/notify-gate.ps1'"
```

无报错说明改对了。

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

让 AI 记住"任务完成时主动播报"的规则。

告诉用户的 AI（通过自然语言，不需要手动编辑文件）：

> **请记住**：整轮回答全部完成（所有步骤跑完、最终结果出来了）才主动运行一次：
> 
> ```bash
> powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$HOME/.claude/notify-voice.ps1" -Mode done
> ```
> 
> **中途动文件不单独喊，攒到最后整轮收尾时喊一次**——用户要验收的是最终结果，不是某个中间步骤。纯聊天/纯问答不喊。

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
- **Claudian 版**：应该播"对话N搞定啦"（N 是当前活动标签编号 1-6）

### 测试决策提醒（所有版本）

让 AI 随便跑个命令，如果弹选择窗口（AskUserQuestion），应该播"需要你拿个主意"。

### 查看日志

```bash
tail ~/.claude/voice-notify.log
```

- 通用版日志示例：`done: fallback (tab=0)`
- Claudian 版日志示例：`done: tab3 mp3 (xiaoxiao)`

---

## 故障排查

### 通用版：播的是机械音

说明 mp3 播放失败，降级到 SAPI。检查：
- `~/.claude/voice_clips/<音色>/done.mp3` 是否存在
- 重新复制音频文件

### Claudian 版：播的是"搞定啦"不带编号

日志显示 `done: fallback (tab=N)`，两种情况分开看：

| 日志 | 原因 | 怎么修 |
|:---|:---|:---|
| `tab=0` | 没认出标签编号 | ①知识库路径 base64 不对 → 重新生成替换 ②`.claudian/sessions/` 或 `data.json` 不存在 → 确认真在 Claudian 环境 ③新建对话还没进 `openTabs` → 正常，先发一轮消息就有了 |
| `tab=3` 却仍 fallback | 认出编号了但找不到音频 | 检查 `~/.claude/voice_clips/claudian_multitab/dialog3_done.mp3` 在不在 —— 多标签音频必须在 `claudian_multitab/` 子目录下，别摊平到 `voice_clips/` 根目录 |

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

### 为什么 Claudian 版需要 base64 编码路径？

PowerShell `.ps1` 文件被 Git Bash 以 GBK 解析，中文路径会乱码。解决方案是把路径 base64 编码后写入脚本，运行时解码。

### 为什么 Claudian 版能识别标签编号？

通过读取 Claudian 插件的数据文件：
1. 从钩子 payload 拿到 `session_id`
2. 扫描 `.claudian/sessions/*.meta.json` 找到对应的 `conversationId`
3. 读 `.obsidian/plugins/tikbit-claudian/data.json` 的 `openTabs` 数组
4. 找到 `conversationId` 匹配的元素，拿到数组索引（0=标签1，1=标签2...）
5. 播放 `voice_clips/claudian_multitab/dialog<N>_done.mp3`，缺文件就降级播通用 `done`

**零侵入**：不修改插件源码，完全基于已有数据文件，插件更新不受影响。

---

**安装完成**！现在 AI 干完活会主动喊你，卡住等你决策时也会提醒。

**音色**：默认使用晓晓（zh-CN-XiaoxiaoNeural）神经语音，自然流畅。如需切换音色，运行双击 `选择语音.bat`（Windows）或 `选择语音.command`（Mac）。

**更新日期**：2026-07-31
