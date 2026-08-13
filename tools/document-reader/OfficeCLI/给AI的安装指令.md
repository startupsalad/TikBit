# 给 AI 的安装指令（OfficeCLI）

> 把这份文件丢给 AI，让它照着装。本目录**不含二进制**，官方装脚本会自己下载（约 60MB）。
> 本机核对版本：officecli 1.0.143（2026-08-06 实测）

## 这是什么

面向 AI Agent 的 Office 文档读写工具，单二进制、**不依赖本机装 Microsoft Office**。
核心价值：把 .docx/.xlsx/.pptx 变成可用选择器查询、可精确改写、可渲染出图自查的结构化对象。

- GitHub：https://github.com/iOfficeAI/OfficeCLI
- Skill 文件：https://officecli.ai/SKILL.md
- 官网：https://officecli.ai

## 第 1 步：装二进制

**Windows（PowerShell）**

```powershell
irm https://d.officecli.ai/install.ps1 | iex
```

**macOS / Linux**

```bash
curl -fsSL https://d.officecli.ai/install.sh | bash
```

装完会：
- 二进制落到 `%LOCALAPPDATA%\OfficeCLI`（Win）并自动加 PATH — **要开新终端才生效**
- 自动探测本机的 Claude Code / Codex CLI，把 skill 装进 `~/.claude/skills/officecli/` 和 `~/.agents/skills/`

验证：

```bash
officecli --version     # 应输出 1.0.143 或更高
```

PATH 没生效时直接用全路径：`"$LOCALAPPDATA/OfficeCLI/officecli.exe" --version`

> 也有一步到位的 `officecli install`（装二进制 + skills + MCP），但首次装还没有 officecli 命令，所以先跑上面的脚本。

## 第 2 步：确认 skill 到位

本知识库已把 skill 同步到项目级 `.claude/skills/officecli/SKILL.md`，**拉到库就有，不用另装**。
其他项目/机器要用，靠第 1 步的自动安装，或手动拷这个文件。

⚠️ **不装 skill 也能用**，只是 AI 不会自动想起来调它，得你手动喊"用 officecli"。

## 第 3 步：确认能用（拿真实文件，别用空白文件）

```bash
officecli view <你的.pptx> stats        # 页数/形状数/字体分布
officecli view <你的.docx> outline      # 标题层级
officecli view <你的.xlsx> outline      # sheet + 公式数
```

## 本库已实测通过（2026-08-06）

用真实文件测的，不是官方 demo：

| 测项 | 结果 |
|:---|:---|
| 26 页客户 BP pptx | 26 页 / 911 形状 / 52 图 / 字体分布全对 |
| 项目统筹推进表 xlsx | 5 个 sheet + 各表公式数读准 |
| 标书模板 docx | 7 级标题层级 + 页脚 PAGE 域识别 |
| 中文 / emoji 路径 | 正常（`08_🔥TikBit` 这种直接吃） |
| 渲染截图 | 出图正常，中文字形完整不崩 |
| **改存量 pptx** | 43 处 9/9.5pt 精确定位并批量提到 14pt，`validate` 通过，963 元素无丢失 |

## 已知限制（别踩）

1. **不支持老格式**：`.doc/.xls/.ppt/.rtf/.wps/.et/.dps` 全不认（`create x.doc` 直接报 Unsupported）。老格式仍走 `文档读取编辑工具包/`。
2. **不能直接导 PDF**：`view <file> pdf` 报 "No exporter plugin found"，要装 exporter 插件。转 PDF 仍走现有方案。
3. **`view issues` 不认我们的规范**：对那份 9.5pt 超标的 BP 返回"0 issues"；另造测试件含 9.5pt+10pt，它也只报标点混排、字号一处没提。**要查字号必须显式 `query "run[size<14],run[effective.size<14]"`**，别信 issues。
4. **常驻模式占文件锁**：任何命令都会自动起常驻（默认 60 秒空闲超时，显式 `open` 是 12 分钟）。在企微微盘同步盘上直接开正式交付物有同步冲突风险 —— **建议拷到临时目录改完再拷回**，或改完立刻 `officecli close <file>`。
   - 关掉自动常驻：`OFFICECLI_NO_AUTO_RESIDENT=1`
   - 每次改动都落盘：`OFFICECLI_RESIDENT_FLUSH=each`
5. **交给非 officecli 程序读之前要 `save` 或 `close`**：python-docx/openpyxl、Word、渲染器、上传交付前都算。officecli 自己的 `get/query/view` 总能看到最新改动，中途不用存。
6. **新建 docx 用 `style=Heading1` 会告警**："style 'Heading1' not found in styles part"。新建的空 docx 样式表是最小集。正确写法先查 `officecli help docx paragraph`（**此项未实测出结论，别照抄 Heading1**）。
7. **首次运行会推断 locale**：提示 `locale 'zh-CN' inferred from OS user culture`，要改加 `--locale`。
8. **`size` 与 `effective.size` 互斥，必须逗号并集**：`size` 只匹配显式设了字号的 run，`effective.size` 只匹配靠继承的，**交集为 0**。测试件（2 处显式 + 4 处继承 docDefaults 11pt）：前者中 2、后者中 4、并集 6 全中；真实 26 页 BP 反过来：前者 291、后者 **0**。**只查一边必漏，一律写 `query "run[size<14],run[effective.size<14]"`。**
9. **`set` 不接受裸选择器**：`set <文件> "run[size<14]" --prop size=14` 报 `Bare selector ... is not allowed for 'set'`，加 `/body` 前缀也匹配不上。批量只有两条路：换文字用 `set <文件> "/body" --find "旧" --replace "新"`（pptx 挂 `/slide[N]`）；改属性用 `query --json` 取路径再 `batch <文件> --input x.json`。`--json` 结构是 `{"success":true,"data":{"matches":N,"results":[{"path":…}]}}`，**results 嵌在 data 里**。`--prop size=14` 不带单位也认，自动按 pt。

## 拿不准命令怎么写就查帮助，别猜

```bash
officecli help                      # 全部命令
officecli help docx                 # docx 所有元素
officecli help docx paragraph       # 完整 schema：属性/别名/示例
officecli help docx set paragraph   # 只看 set 能用的属性
officecli load_skill                # 10 个内置场景 skill 清单
officecli load_skill pitch-deck     # 读某个 skill 的完整规则
```

格式别名：`word`→`docx`，`excel`→`xlsx`，`ppt`/`powerpoint`→`pptx`。

