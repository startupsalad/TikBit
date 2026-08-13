# 给 AI 的安装指令（把本文件连同所在工具包文件夹一起给你的 AI）

> **给 AI 的话**：用户想要"AI 对话太长时，自动提醒该开新对话 / 清理上下文以省 token"。本工具包是一个 **Claude Code 钩子**：在用户每次发消息时，量出当前对话的上下文 token 量，到阈值就把一句提醒注入到你的上下文里——于是你（AI）一定看得到，会主动提醒用户。请你**在用户本机自动完成安装**，全程别让用户手敲命令——你自己调工具执行、自己测试、把结果告诉用户。遇到与本机实际不符处（路径、用户名、客户端），**以本机探测为准**。

## 它解决什么

长对话最烧钱的地方不是"干活"，而是**每说一句话都要把前面全部历史重读一遍**（全价计费）。对话开到几百轮、挂十几小时，账单主力全在这。靠"AI 自觉数轮次"不可靠（对话越长、上下文被压缩，AI 越想不起来提醒）。本工具用**外部钩子**兜底：不依赖 AI 自觉，到点强制注入提醒。

本工具包目录（你能读到的就是它）：

```
对话长度提醒工具包/
├── install.py                  # 跨平台安装器（复制引擎 + 安全合并 Claude Code 钩子）
├── engine/
│   └── context_reminder.py     # 钩子引擎（读 transcript 量上下文，跨档位时注入提醒）
├── 给AI的安装指令.md            # 本文件
└── 📖 使用说明.md
```

---

## 最省事的装法：直接调用自带安装器

本机有 Python（3.6+）时，**首选直接跑安装器**，它已把所有步骤封装好（复制到 `~/.context-reminder/`、检测并安全合并 Claude Code 钩子、改前自动备份、幂等不重复加）：

```bash
python "<本工具包目录>/install.py"      # 或 python3
```

跑完就装好了。**装完务必跑一次下面的"测试"确认生效，再告诉用户重启 Claude Code。**

---

## 手动步骤（没 Python，或非 Claude Code 客户端时）

### 第 1 步 · 复制引擎到本机固定位置
把 `engine/context_reminder.py` 复制到用户主目录的 `~/.context-reminder/context_reminder.py`。
> 为什么复制到这：路径统一、不依赖同步盘、自包含可移动。引擎只用 Python 标准库，无需装任何依赖。

### 第 2 步 · 接钩子

**A) Claude Code** —— 编辑 `~/.claude/settings.json`，**先备份**，再往 `hooks.UserPromptSubmit` 里**合并**（别覆盖用户已有内容）一段。命令里 python 用本机实际解释器的绝对路径（探测：`python -c "import sys;print(sys.executable)"`），脚本路径用本机绝对路径：

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "PYTHONUTF8=1 \"<python绝对路径>\" \"<主目录>/.context-reminder/context_reminder.py\" 2>/dev/null || true"
          }
        ]
      }
    ]
  }
}
```

改完用 JSON 解析器验一遍合法性。告诉用户：**改了钩子要重启 Claude Code 才生效**。

**B) 其它客户端（CodeBuddy 等不认 `~/.claude` 钩子的）** —— 查该客户端是否有"用户发消息前"的钩子/中间件，且其 stdout 能注入上下文。有就接上去，把本引擎当命令调（它从 stdin 读 `{"session_id","transcript_path"}`，transcript 是该客户端的会话 jsonl）。没有这类钩子的，退一步：**让该 AI（也就是你）养成习惯——回复时自己留意对话长度，长了就提醒用户开新对话**（但要说清这种自觉提醒不如钩子可靠）。

---

## 测试（装完必做）

引擎从 stdin 读 JSON、stdout 输出提醒。拿用户当前任一会话的 transcript 路径测：

```bash
# 找一个真实会话 jsonl（Claude Code 在 ~/.claude/projects/<编码后的项目路径>/*.jsonl）
echo '{"session_id":"test","transcript_path":"<某个会话.jsonl的绝对路径>"}' | PYTHONUTF8=1 python ~/.context-reminder/context_reminder.py
```

- 若该会话上下文已超 130K，应打印一行 `[对话长度提醒｜系统自动] ...`；没超则无输出（正常）。
- 不管怎样 `echo $?` 都应是 0（钩子绝不阻塞用户发消息）。
- 同一 session 重复喂、同档位只提醒一次（防刷屏，记在 `~/.context-reminder/state.json`）。

---

## 阈值与原理速查

- 触发档位（`engine/context_reminder.py` 顶部 `BANDS`，可改）：**130K**（轻提醒）/ **230K**（建议清）/ **350K**（强烈建议立刻开新对话）token。
- 触发量 = transcript 里最后一条 usage 的 `input + cache_read + cache_creation`，即"当前每轮要重读的上下文规模"。
- `/clear`、`/compact` 后上下文回落，档位自动重置，涨上来会重新提醒；同档位不重复打扰。
- 任何异常（读不到 transcript、stdin 空、解析失败）都静默 exit 0，不影响用户正常使用。

## 卸载
删掉 `~/.context-reminder/` 文件夹；Claude Code 用户再把 `~/.claude/settings.json` 里 `UserPromptSubmit` 下含 `context_reminder` 的那段钩子删掉，重启。
