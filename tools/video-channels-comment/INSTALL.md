# 🎥 视频号评论导出工具 · 安装说明（这份是写给 AI 看的，请你——用户的 AI 助手——读我）

> **你好，我是用户电脑上的安装向导。这份文档是写给你（用户的 AI 助手 Claude）看的，不是给人看的。**
> 用户把这个文件夹交给你，说「帮我装上这个工具」时，请**先完整读完这份文档**，再动手。
> 装好后，用一句活泼、人话的总结告诉用户「装好了，现在能干嘛」，**不要**把命令、路径、报错原样念给用户听。

---

## 🧠 第零原则：你是聪明的安装者，不是脚本复读机

这份说明给你一条**默认的安装路径**（见下面「标准安装」）。但每台电脑环境不同——有的装过这装过那、有的是全新机器、有的 Mac 有的 Windows。所以：

1. **先观察，再动手**：用一两条命令搞清楚当前环境（什么系统？node/python 在哪？playwright 装了没？），再决定怎么做。
2. **优先走标准路径**：标准安装是最稳做法，能走通就别自己另发明。
3. **遇到障碍，用你的知识灵活解决**：如果某一步卡住了（缺东西、路径不对、权限问题），**别立刻放弃、也别死磕同一条命令**——你完全有能力诊断根因、用最适合这台电脑的方式绕过去。这正是「让 AI 来装」比「双击安装包」强的地方。
4. **守住安全底线**：只动这个工具相关的文件（见「会改动哪些文件」），绝不乱删用户的笔记、配置、密钥。
5. **失败两次就换思路**：同一个办法试两次还不行，停下来分析根因，换一条路。

---

## 一、这个工具是干什么的、怎么工作的（动手前必须懂）

**作用**：帮用户把自己**视频号后台**的所有视频评论批量导出成表格——评论者昵称、评论内容、时间、点赞数、作者回复，一条不漏，生成 Markdown / CSV / JSON 三种格式。用户可以拿来分析读者关注什么、找选题、看哪条被赞最多。

**技术原理（这是它最聪明的地方）**：
1. 核心是一个 **Python 脚本** `视频号评论导出工具.py`（这个文件夹里就有）。
2. 它通过 **Chrome 调试协议（CDP）** 连上用户**已经登录**的 Chrome 浏览器，读取视频号助手后台（channels.weixin.qq.com）页面上的评论数据。
3. **评论数据是直接从页面 DOM 读取的，不破解任何接口、不碰签名参数**——所以完全合规、稳定，比抓抖音/小红书还简单。
4. 走的是用户自己登录的官方后台，**只能读用户自己账号的评论**（这是产品的诚实边界，也是合规的保证）。

**为什么交给你装、不做双击安装包**：这个工具安装动作很简单（拷个脚本 + 装个 Python 库 + 给 CLAUDE.md 加段说明），而你能根据这台电脑的真实情况把它装对、把依赖补齐——比一个在各种系统上反复踩坑的双击脚本可靠得多。

---

## 二、标准安装（默认走这条）

这个文件夹里有个跨平台的**安装引擎** `install-core.js`，它会自动完成：建目录、拷脚本、给全局和每个 Obsidian 知识库的 CLAUDE.md 追加使用指令块（**幂等**，重复装不叠加）。你要做的就是**找到 node、把它跑起来**，然后**确保 Python 依赖装好**。

### 第 1 步：搞清楚环境
```bash
# 看系统
uname -a            # Mac/Linux；Windows 上你自己判断

# 找 Node（工作台装过 Claude Code 就一定有 node）
ls -l ~/.local/bin/node 2>/dev/null
command -v node 2>/dev/null

# 找 Python（本工具用 Python 跑）
command -v python3 2>/dev/null || command -v python 2>/dev/null
```
- **找不到 python3** → 引导用户装 Python 3（Mac 可 `brew install python3`；Windows 去 python.org 下载，安装时勾选「Add to PATH」）。或者你判断当前 Claude 环境里有没有可用的 python。

### 第 2 步：装 Python 依赖 playwright（关键！）
本工具依赖 `playwright` 库。先检查：
```bash
python3 -c "import playwright" 2>/dev/null && echo "已装" || echo "未装"
```
如果**未装**，自动安装：
```bash
pip3 install playwright --user
# 如果 pip3 不存在，试 pip 或 python3 -m pip
python3 -m pip install playwright --user
```
> ⭐ **重要**：装完 **不需要** 再跑 `playwright install`。因为本工具是**连接用户已打开的 Chrome**（通过 CDP），不需要 playwright 自带的浏览器。这一步能省掉几百 MB 下载。

### 第 3 步：跑安装引擎
```bash
# <node> 换成第1步找到的真实路径；两个文件都在你正读的这个文件夹里
"<node>" "这个文件夹/core/install-core.js" "这个文件夹/core/视频号评论导出工具.py"
```
引擎会打印每一步的 ✓。看到「🎥 视频号评论导出工具安装成功！」就成了。

> **如果 `install-core.js` 因为任何原因跑不起来**，别卡住——你完全可以读懂下面「三、安装到底做了什么」，**自己手动把这些步骤做一遍**。引擎只是帮你省事，不是唯一手段。

---

## 三、安装到底做了什么（万一要手动做 / 排错时照这个）

如果你需要绕过 `install-core.js` 自己装，照着做这几件事即可：

1. **建目录**：`~/.claude/channels-comment/`。
2. **拷脚本**：把这个文件夹里的 `视频号评论导出工具.py` 拷到 `~/.claude/channels-comment/channels-comment-export.py`。
3. **确保 playwright 已装**（见第二节）。
4. **给 CLAUDE.md 和 AGENTS.md 各加使用指令块**（双模型：Claude 读 CLAUDE.md、GPT/Codex 读 AGENTS.md，本工具两个大脑都能调）：往 `~/.claude/CLAUDE.md` + `~/.codex/AGENTS.md`（全局兜底）**以及每个 Obsidian 知识库根目录的 CLAUDE.md + AGENTS.md** 里，各追加告诉「未来的你」何时/如何调用这个工具的说明，用 `<!-- CHANNELS-COMMENT-BEGIN ... -->` 和 `<!-- CHANNELS-COMMENT-END -->` 包起来（这段指令是大脑中立的，两文件写同一份即可；重复装能整段替换、不叠加）。
   - ⚠️ **关键**：AI 在 Obsidian 里跑时，加载的是**知识库自己的**说明书（Claude 读 CLAUDE.md、GPT 读 AGENTS.md），不是全局那个。所以指令一定要两个都写进知识库。
   - 这段指令块的标准内容，直接看 `install-core.js` 里的 `CLAUDE_BLOCK` 常量照抄即可。

**装完后会改动这些文件**（排错时心里有数）：`~/.claude/channels-comment/`（脚本）、全局 `~/.claude/CLAUDE.md` 和 `~/.codex/AGENTS.md`、各知识库的 `CLAUDE.md` 和 `AGENTS.md`。

---

## 四、用户要用时，你（AI）怎么带他跑（核心使用流程）

当用户说「导出我视频号的评论」时，按这个流程：

### 第 1 步：让用户用「调试模式」打开 Chrome
这一步是为了让工具能连上 Chrome 读到用户已登录的视频号后台。给用户这条命令让他在终端跑（会保留他的登录，不影响日常）：
```bash
# Mac:
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222 --user-data-dir="$HOME/chrome-debug" &

# Windows:
start chrome.exe --remote-debugging-port=9222 --user-data-dir="%USERPROFILE%\chrome-debug"
```
> 提示用户：**先完全退出现有的 Chrome，再跑这条命令**（否则新参数不生效）。

### 第 2 步：让用户在这个 Chrome 里登录并打开评论页
引导用户：
1. 打开 `channels.weixin.qq.com`，扫码登录视频号助手
2. 点左侧「互动管理 → 评论」，停在这个页面

### 第 3 步：你运行工具
```bash
python3 ~/.claude/channels-comment/channels-comment-export.py
# 想快速试可加 --max 20（只抓前20个）
```
- 跑之前提醒用户：**别去动那个 Chrome 窗口**，工具在自动点击遍历。
- 视频多的话（上百个）可能要几分钟，耐心等。

### 第 4 步：告诉用户结果
- 产物在 `<知识库根目录>/视频号评论导出/` 下，三个文件（.md/.csv/.json，带时间戳）。
- 用 Markdown 那份给用户看总表，或直接帮他做**评论分析**（读者最关心什么、哪类内容互动最高、能挖什么新选题）——这是这个工具真正的价值。

---

## 五、排错（用户说"用不了"时按这个查）

- 报 **"连不上 Chrome 调试端口"** → 用户没用调试模式开 Chrome，或没退出旧 Chrome。重走第四节第 1 步。
- 报 **"没找到视频号助手页面"** → 用户没在那个 Chrome 里打开 channels.weixin.qq.com。让他打开并登录。
- 报 **"找不到评论 iframe"** → 用户不在「互动管理→评论」页。让他点进去。
- 报 **`ModuleNotFoundError: playwright`** → playwright 没装好，重跑 `pip3 install playwright --user`。
- **抓到 0 条评论 / 只抓到一部分** → 页面可能没加载完，或用户中途动了 Chrome。让他保持页面不动，重跑一次。
- **视频号助手打不开 / 提示没权限** → 用户这个微信号可能没开通视频号，或不是创作者。这是账号问题，工具无能为力。

---

## 六、安全兜底原则（动手时守住）
- 只动这个工具相关的文件：`~/.claude/channels-comment/` 和 CLAUDE.md / AGENTS.md 里 `CHANNELS-COMMENT-BEGIN...END` 之间的内容。**别碰用户的笔记、别动 CLAUDE.md / AGENTS.md 其他部分。**
- 工具只**读取**用户已登录的浏览器页面，**不修改**视频号后台的任何数据（不删评论、不改设置）。
- 导出的评论数据只存在用户本地知识库里，**不上传任何地方**。

---

## 七、终极手段：重新来一遍
如果环境被搞乱了，最干净的做法是让用户重新解压这个安装包，把整个文件夹再交给你一次，你重跑 `install-core.js`。它是**幂等**的（重复装不叠加指令块），会用最新的脚本覆盖旧的。

---

**由创业沙拉 | TikBit 维护**
