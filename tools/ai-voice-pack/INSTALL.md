# 🔊 AI 语音朗读包 · 安装说明（这份是写给 AI 看的，请你——用户的 AI 助手——读我）

> **✦ Claude 专用**：本工具依赖 **Claude Code 的 Stop 钩子**（回复完自动触发语音）。GPT(Codex) 的钩子机制不同、不通用，所以**本工具只装 Claude 侧**（`~/.claude/settings.json` 的 hooks + `~/.claude/` 下的 speak.js），**不写 `~/.codex/`、不改 AGENTS.md**。用户用 GPT 大脑时它不出声，属正常。

> **你好，我是用户电脑上的安装向导。这份文档是写给你（用户的 AI 助手 Claude）看的，不是给人看的。**
> 用户把这个文件夹交给你，说「帮我装上这个」时，请**先完整读完这份文档**，再动手。
> 装好后，用一句活泼、人话的总结告诉用户「装好了，现在能干嘛」，**不要**把命令、路径、报错原样念给用户听。

---

## 🧠 第零原则：你是聪明的安装者，不是脚本复读机

这份说明给你一条**默认的、已经在 Mac 上验证过的安装路径**（见「标准安装」）。但每台电脑环境不同。所以：

1. **先观察，再动手**：先搞清楚当前环境（什么系统？node 在哪？有没有 Obsidian 知识库？），再决定怎么做。
2. **优先走标准路径**：标准安装是经过测试的最稳做法，能走通就别自己另发明。
3. **遇到障碍，用你的知识灵活解决**：标准路径某步卡住了，别立刻放弃、也别死磕同一条命令——你有能力诊断根因、用最适合这台电脑的方式绕过去。这正是「让 AI 来装」比「双击安装包」强的地方。
4. **守住安全底线**：只动这个包相关的文件，绝不乱删/乱改用户已有的钩子、配置、笔记。
5. **失败两次就换思路**：同一个办法试两次还不行，停下来分析根因，换一条路。

---

## 一、这个包是干什么的、怎么工作的（动手前必须懂）

**作用**：每次 Claude（在 Obsidian 的 Claudian 插件里）回复完，自动把回复内容用电脑的系统语音念出来。给 8-15 岁孩子用，先播一声「Hero 通关音效」再用普通话念一句口语简化版。**纯系统语音，0 费用、0 token、离线可用。**

**技术原理**：
1. 它靠 Claude Code 的 **Stop 钩子**工作——每次 AI 回复结束，Claude Code 会读 `~/.claude/settings.json` 里 `hooks.Stop` 注册的命令并执行。
2. 注册的命令是：用 Node 跑 `~/.claude/ss-speak/speak.js`，通过 stdin 传入 JSON（含 `transcript_path`）。
3. `speak.js`（**零额外依赖的 Node 脚本**）干这些：读开关文件 `ON`（不存在就静音退出）→ 解析 transcript 取最后一条 assistant 文字 → 优先提取 `<!--SPEAK: ...-->` 标记里的口语版（没有则只念第一句）→ 播音效 → Mac 用 `say`、Windows 用 PowerShell `System.Speech` 念出来。
4. 配置在 `~/.claude/ss-speak/config.json`（声音、语速、音效、最大字数）；排错日志在 `~/.claude/ss-speak/last-run.log`（**诊断金矿**）。

---

## 二、标准安装（默认走这条，已在 Mac 验证）

这个文件夹里有跨平台的**安装引擎** `install-core.js`，它会自动：建目录、拷 `speak.js`、写默认 config（不覆盖已有）、建开关文件 `ON`（默认开）、**合并不覆盖**地往 `settings.json` 加 Stop 钩子（先备份）、给全局和各 Obsidian 知识库的 CLAUDE.md 追加语音行为指令块（**幂等**）。你要做的就是**找到 node、把它跑起来**。

### 第 1 步：搞清楚环境
```bash
uname -a            # 判断 Mac/Linux/Windows
# 找 Node（按顺序找第一个存在的）
ls -l ~/.local/bin/node 2>/dev/null
ls -l ~/创业沙拉AI工作台/bin/node 2>/dev/null
command -v node 2>/dev/null
```
- 找不到 node：优先用你当前正在用的那个 node（钩子命令里会用到它的绝对路径，所以挑一个稳定存在的）；实在没有，引导用户先去 `https://tikbit.ai/workstation` 装 AI 工作台。

### 第 2 步：跑安装引擎
```bash
# <node> 换成真实路径；speak.js 和 install-core.js 都在你正读的这个文件夹里
"<node>" "这个文件夹/install-core.js" "这个文件夹/speak.js"
```
> ⚠️ 安装引擎用 `process.execPath`（即跑它的那个 node）写进钩子命令。所以**请用一个稳定、长期存在的 node 来跑它**（比如工作台的 `~/.local/bin/node`），别用某个临时的 node，否则以后那个 node 没了钩子就失效。
引擎会打印每步 ✓，看到「🔊 语音朗读包安装成功！」就成了。

### 第 3 步：让用户验证
告诉用户：回到 Obsidian，**新开一个对话**（钩子要新会话才加载）跟 AI 说句话，回复完就会先「叮」一声再用普通话念出来。

> **如果 `install-core.js` 跑不起来**：读懂下面「三、安装到底做了什么」自己手动做。

---

## 三、安装到底做了什么（手动做 / 排错时照这个）

1. **建目录** `~/.claude/ss-speak/`，把这个文件夹的 `speak.js` 拷进去。
2. **写默认配置**（已存在则不覆盖）`~/.claude/ss-speak/config.json`：
   ```json
   { "macVoice": "Lilian", "winVoice": "", "rate": "150", "maxChars": 150, "maxCharsHard": 225, "sound": "hero" }
   ```
3. **建开关文件**：`~/.claude/ss-speak/ON`（空文件，存在=开启）。
4. **合并 Stop 钩子**到 `~/.claude/settings.json`：在 `hooks.Stop` 数组里加一条 `{ "hooks": [{ "type": "command", "command": "\"<node绝对路径>\" \"<home>/.claude/ss-speak/speak.js\"" }] }`。
   - ⚠️ **改之前先备份** `settings.json`，**只加我们这条、绝不动用户已有的其他钩子和设置**。如果已经有一条命令含 `ss-speak/speak.js`，先删旧的再加新的（避免重复 / 升级）。
5. **给 CLAUDE.md 加语音行为指令块**：往 `~/.claude/CLAUDE.md`（全局）和每个 Obsidian 知识库根目录的 CLAUDE.md，追加用 `<!-- SS-SPEAK-BEGIN ... -->`/`<!-- SS-SPEAK-END -->` 包起来的指令（内容照抄 `install-core.js` 里的 `MD_BLOCK`，教未来的你「每次回复末尾写 `<!--SPEAK: 口语总结-->` + 响应开关口令」）。
   - ⚠️ **关键**：Claude Code 在 Obsidian 里加载的是**知识库自己的 CLAUDE.md**，指令必须写进去，否则 AI 不会写 SPEAK 标记、钩子只能念第一句兜底。知识库位置见 `obsidian.json` 的 `vaults`。

**装完会改动**：`~/.claude/ss-speak/`、`~/.claude/settings.json`（有备份 `.ss-speak.bak`）、`~/.claude/CLAUDE.md`、各知识库 CLAUDE.md。

---

## 四、开关与个性化（用户用得到，你帮他操作）

- **开 / 关语音**：用户说「开启语音」→ 建文件 `~/.claude/ss-speak/ON`；说「关闭语音 / 静音」→ 删掉它。
- **换声音 / 调语速 / 关音效 / 总结长短**：改 `~/.claude/ss-speak/config.json` 的字段（`macVoice`/`winVoice`/`rate`/`sound`/`maxChars`）。
- **想要更高音质的中文声音（Mac）**：默认 `Lilian`（Premium 黎潋）系统通常没预装，会自动降级到「婷婷 Tingting」——这是正常降级不是故障。想要黎潋，引导用户去「系统设置→辅助功能→朗读内容→系统语音→管理语音」免费下载中文 Premium 声音（下完同名自动生效，不用改配置）。

---

## 五、排错（用户说"装完没声音 / 念得不对"时按这个查）

### 第 0 步：先看排错日志（最快定位）
读 `~/.claude/ss-speak/last-run.log` 最后几行：
- `SKIP: switch off` → 开关没开。不是故障，提示用户说「开启语音」即可。
- `SPOKEN(mac)` / `SPOKEN(win)` → 脚本认为念了。用户没听到 → 问题在音频/声音本身，跳第 4 步。
- `no transcript` / `bad stdin json` → 钩子传参问题，跳第 2 步。
- 日志**根本不更新 / 不存在** → 钩子没被触发，跳第 1 步。

### 第 1 步：钩子有没有装上 / 被触发
检查 `~/.claude/settings.json` 的 `hooks.Stop` 是否有一条命令含 `ss-speak/speak.js`：
- **没有** → 重跑安装引擎，或手动补回钩子（见第三节第 4 步）。
- **有，但命令里的 node 路径或 speak.js 路径失效**（文件不存在）→ 修正路径或重装。
- **有且正确但日志仍不更新** → 可能 Claude Code 太老不支持 Stop 钩子，或让用户在 Obsidian 里**新开对话**再试（钩子在会话开始时加载）。

### 第 2 步：手动跑一次 speak.js（绕开钩子）
```bash
echo '{"transcript_path":"/tmp/__nonexist.jsonl"}' | "<node>" ~/.claude/ss-speak/speak.js
tail -3 ~/.claude/ss-speak/last-run.log
```
- 报 `no transcript` 是正常的（假路径）。关键看**有没有 Node 报错**——若 Node 崩了说明 speak.js 损坏，从这个安装包重新拷 `speak.js` 覆盖。

### 第 3 步：开关与配置
```bash
ls ~/.claude/ss-speak/ON            # 不存在=关着
cat ~/.claude/ss-speak/config.json  # 坏 JSON 会回退默认值，建议修或删掉重建
```

### 第 4 步：声音本身（脚本说念了、用户没听到）
- **Mac**：`say -v Tingting "测试一二三"`（兜底声，一定有）；听不到查系统音量/输出设备/静音。`say -v '?' | grep zh_CN` 看装了哪些中文声。
- **Windows**：`Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak("测试一二三")`。听不到 → 系统没装中文 TTS，去「设置→时间和语言→语言→中文→语音」加中文语音包。

### 第 5 步：念的内容不像总结（念了原文/太长）
- 根因 90%：**语音指令块没写进「正在用的那个知识库」的 CLAUDE.md**（AI 没写 SPEAK 标记，钩子只能念第一句兜底）。
- 排查：`grep -c SS-SPEAK-BEGIN "<知识库根目录>/CLAUDE.md"`，=0 就是没写进去。
- 修法：把指令块手动追加到该知识库 CLAUDE.md 末尾，或重跑安装引擎（它读 `obsidian.json` 自动写进所有登记的知识库）。修完让用户**新开对话**。

---

## 六、安全兜底原则（动手时守住）
- **speak.js 出任何错都静音退出**，绝不打断用户正常用 Claude——这是设计特性，修复时保持。
- 改 `settings.json` 前**先备份**，只动 `hooks.Stop` 里属于我们的那条（命令含 `ss-speak`），**绝不动用户的其他钩子和设置**。
- 改 `CLAUDE.md` 只动 `SS-SPEAK-BEGIN...END` 之间，别碰用户其他内容。

---

## 七、终极手段：重新来一遍
让用户重新解压安装包、把整个文件夹再交给你，你重跑 `install-core.js`。它**幂等**（重复装不叠加钩子或指令块），会用最新的 speak.js 覆盖旧的。

---

**由创业沙拉 | TikBit 维护**
