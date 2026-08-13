# PPT 制作工具包 - AI 自动安装指令

> **📌 本文档是给 AI 看的自动化安装指令**
> 
> 人类用户把本工具包下载后，让自己的 AI（Claude / GPT / Codex / Cursor 等）读这个文件，AI 会自动执行所有安装步骤。

---

## 安装任务

你（AI）现在要帮用户安装"PPT 制作工具包"，包括：

1. **8 个 skills** 安装到项目级 `.claude/skills/`（或对应的 AI skills 目录）
2. **工具脚本** 复制到用户工作目录
3. **流程文档** 供 AI 读取（不需要用户手动看）
4. **CLAUDE.md 配置** 追加到用户的 CLAUDE.md

---

## 第 0 步：解压核心内容包（必做，先于一切）

> **⚠️ 本工具包内容全部打包进 `PPT制作工具包_核心内容.zip`**（skills/、工具脚本/、流程文档/、编辑风HTML版式库/）。
> 这样做是因为整包 2.5 万+ 碎小文件（上万 SVG 图标），散着经网盘/微盘同步极易漏传，压成一个大文件才能可靠传输。
> **你（AI）必须先解压这个 zip，把这些目录还原出来，后续步骤才能找到 `skills/` 等目录。**

```bash
# 进到工具包根目录（本 README 所在目录）
cd "$(dirname "$0")" 2>/dev/null || true

ZIP="PPT制作工具包_核心内容.zip"
if [ ! -f "$ZIP" ]; then
    echo "❌ 没找到 $ZIP，请确认工具包下载完整"
    exit 1
fi

# 解压到当前目录（还原 skills/ 工具脚本/ 流程文档/ 编辑风HTML版式库/）
if command -v unzip &> /dev/null; then
    unzip -o "$ZIP" -d .
elif command -v 7z &> /dev/null; then
    7z x -y "$ZIP"
elif command -v powershell.exe &> /dev/null; then
    powershell.exe -NoProfile -Command "Expand-Archive -Path '$ZIP' -DestinationPath '.' -Force"
else
    echo "❌ 未找到解压工具（unzip / 7z / powershell），请手动解压 $ZIP 到当前目录"
    exit 1
fi

echo "✅ 核心内容已解压，skills/ 等目录已还原"
ls -d skills 工具脚本 流程文档 编辑风HTML版式库 2>/dev/null
```

解压成功后，工具包目录会出现 `skills/`、`工具脚本/`、`流程文档/`、`编辑风HTML版式库/`，继续下面的步骤。

---

## 第 1 步：检测环境

先确认用户的 AI 环境和项目路径：

```bash
# 检测 AI 环境（Claude Code / Codex / Cursor）
if [ -d "$HOME/.claude" ]; then
    AI_ENV="claude"
    SKILLS_DIR="$HOME/.claude/skills"
elif [ -d "$HOME/.codex" ]; then
    AI_ENV="codex"
    SKILLS_DIR="$HOME/.codex/skills"
elif [ -d "$HOME/.cursor" ]; then
    AI_ENV="cursor"
    SKILLS_DIR="$HOME/.cursor/skills"
else
    echo "未检测到已知 AI 环境，请用户手动指定 skills 目录"
    exit 1
fi

# 确认当前工作目录
WORK_DIR=$(pwd)
echo "AI 环境：$AI_ENV"
echo "Skills 目录：$SKILLS_DIR"
echo "工作目录：$WORK_DIR"
```

**询问用户**："检测到你的 AI 环境是 $AI_ENV，skills 将安装到 $SKILLS_DIR，工具脚本将复制到 $WORK_DIR，是否继续？"

用户确认后继续。

---

## 第 2 步：安装 8 个 Skills

```bash
# 创建 skills 目录（如果不存在）
mkdir -p "$SKILLS_DIR"

# 复制 8 个 skills
cp -r skills/allaction-ppt-design "$SKILLS_DIR/"
cp -r skills/space-multi-design-ppt "$SKILLS_DIR/"
cp -r skills/html-ppt "$SKILLS_DIR/"
cp -r skills/slide-maker "$SKILLS_DIR/"
cp -r skills/guizang-ppt "$SKILLS_DIR/"
cp -r skills/ppt-master "$SKILLS_DIR/"
cp -r skills/ultimate-ppt-master "$SKILLS_DIR/"
cp -r skills/huashu-design "$SKILLS_DIR/"

echo "✅ 8 个 skills 安装完成"
```

**Skills 清单**：
- `allaction-ppt-design` — 立即行动科技 PPT 排版规范（A/B/C/D/E 五模式决策树）
- `space-multi-design-ppt` — 62 种品牌风格引擎（Apple/Claude/Notion/Stripe/Linear/Tesla 等）
- `html-ppt` — C 模式（HTML slides + 36 主题 + 47 种动画 + 演讲者模式）
- `slide-maker` — D 模式（多代理学术/技术评审）
- `guizang-ppt` — E 模式（杂志风 / 瑞士国际主义）
- `ppt-master` — F1 工具（简单文档 → PPTX 快速转换）
- `ultimate-ppt-master` — F2 工具（复杂文档 → 多格式输出）
- `huashu-design` — 设计资源库（UI 组件 / 插画 / 配色 / 动画）

---

## 第 3 步：复制工具脚本

```bash
# 复制 GPT 工具包到工作目录
cp -r 工具脚本/GPT工具包 "$WORK_DIR/02_🛠️工具库/通用工具/" || cp -r 工具脚本/GPT工具包 "$WORK_DIR/"

# 复制可编辑 PPT 版式库
cp -r 工具脚本/可编辑PPT版式库 "$WORK_DIR/02_🛠️工具库/通用工具/" || cp -r 工具脚本/可编辑PPT版式库 "$WORK_DIR/"

echo "✅ 工具脚本复制完成"
```

**包含内容**：
- `GPT做PPT工具.py` — A 模式（GPT-Image 出图）
- `可编辑PPT版式库/` — B 模式（python-pptx 可编辑，字号自检 + 4 轮修补）
- `MD模板.md` + `PPT设计决策手册.md` — 写 PPT 大纲的参考文档

---

## 第 4 步：安装依赖（可选）

如果用户需要用 python-pptx 或 GPT 生图，需要安装 Python 依赖：

```bash
# 检测 Python 环境
if command -v python3 &> /dev/null; then
    echo "检测到 Python，开始安装依赖..."
    pip install python-pptx Pillow openai requests -q
    echo "✅ Python 依赖安装完成"
else
    echo "⚠️ 未检测到 Python，如需使用 A/B 模式请手动安装"
fi
```

**依赖清单**：
- `python-pptx` — B 模式（可编辑 PPTX）
- `Pillow` — 图片处理
- `openai` — A 模式（GPT-Image 生图）
- `requests` — HTTP 请求

**⚠️ 重要：GPT API 密钥配置**

本工具包的 GPT 工具脚本**不包含 API 密钥**（安全原因）。

用户需要自己配置：

**方式 1：环境变量（推荐）**
```bash
export GPT_API_KEY="用户自己的密钥"
export GPT_BASE_URL="https://api.openai.com/v1"
```

**方式 2：配置文件**
在工具脚本所在目录创建 `gpt_config.md`，写入：
```markdown
---
api_key: 用户自己的密钥
base_url: https://api.openai.com/v1
image_model: gpt-image-2
---
```

**告诉用户**："GPT 生图功能需要你自己的 OpenAI API 密钥。如果不用 GPT 生图（A 模式），可以跳过这一步，其他模式（B/C/D/E/F/G）都不需要密钥。"

---

## 第 5 步：配置 CLAUDE.md

读取 `CLAUDE.md片段.txt` 的内容，追加到用户的 CLAUDE.md 文件：

```bash
# 检测用户的 CLAUDE.md 路径
if [ -f "$WORK_DIR/CLAUDE.md" ]; then
    CLAUDE_MD="$WORK_DIR/CLAUDE.md"
elif [ -f "$HOME/.claude/CLAUDE.md" ]; then
    CLAUDE_MD="$HOME/.claude/CLAUDE.md"
else
    echo "⚠️ 未找到 CLAUDE.md，请用户手动配置"
    exit 1
fi

# 追加配置
cat CLAUDE.md片段.txt >> "$CLAUDE_MD"
echo "✅ CLAUDE.md 配置完成"
```

**配置内容**：
```
| **做 PPT（通用场景）** | 调`space-multi-design-ppt` skill（`.claude/skills/space-multi-design-ppt/SKILL.md`）：62 种品牌风格（Apple/Claude/Notion/Stripe/Linear/Tesla 等）+ 智能推荐 + DEMO 先行 + HTML/PPTX/PDF 输出。**标准工作流**：框架确认 → 风格 DEMO → 批量制作，见 `流程文档/ppt-workflow-standard.md` |
```

**告诉用户**："已在你的 CLAUDE.md 增加 PPT 工具链触发行，以后说'做 PPT'我就自动执行标准工作流"

---

## 第 6 步：创建项目级记忆（可选）

如果用户有项目级 memory 目录（如 `.claude/projects/xxx/memory/`），可以复制流程文档：

```bash
# 检测项目级 memory
if [ -d ".claude/projects" ]; then
    PROJECT_MEMORY=$(find .claude/projects -name "memory" -type d | head -1)
    if [ -n "$PROJECT_MEMORY" ]; then
        cp 流程文档/*.md "$PROJECT_MEMORY/"
        echo "✅ 流程文档已复制到项目记忆"
    fi
fi
```

**流程文档清单**：
- `ppt-workflow-standard.md` — 标准工作流（框架确认 → 风格 DEMO → 批量制作）
- `ppt-five-mode-complete-integration.md` — A/B/C/D/E 五模式完整决策树
- `space-multi-design-ppt-integration.md` — G 工具（62 种品牌风格引擎）
- `html-ppt-skill-integration.md` — C 模式整合文档
- `slide-maker-integration.md` — D 模式整合文档
- `guizang-ppt-integration.md` — E 模式整合文档
- `ppt-master-integration.md` — F1 工具整合文档
- `ultimate-ppt-master-integration.md` — F2 工具整合文档
- `huashu-design-integration.md` — 设计资源库整合文档

---

## 第 7 步：验证安装

```bash
# 验证 skills 安装
echo "验证 skills 安装..."
for skill in allaction-ppt-design space-multi-design-ppt html-ppt slide-maker guizang-ppt ppt-master ultimate-ppt-master huashu-design; do
    if [ -d "$SKILLS_DIR/$skill" ]; then
        echo "✅ $skill"
    else
        echo "❌ $skill 安装失败"
    fi
done

# 验证工具脚本
echo "验证工具脚本..."
if [ -d "$WORK_DIR/02_🛠️工具库/通用工具/GPT工具包" ] || [ -d "$WORK_DIR/GPT工具包" ]; then
    echo "✅ GPT工具包"
else
    echo "❌ GPT工具包安装失败"
fi

echo "---"
echo "🎉 PPT 制作工具包安装完成！"
```

---

## 安装完成后告诉用户

安装完成后，向用户说明：

```
🎉 PPT 制作工具包安装完成！

已安装内容：
✅ 8 个 skills（A/B/C/D/E 五模式 + F1/F2 文档转换 + 设计资源库）
✅ GPT 工具包（A 模式 GPT 出图 + B 模式可编辑版式库）
✅ 流程文档（标准工作流 + 五模式决策树）
✅ CLAUDE.md 配置（触发词已注册）

使用方式：
1. 直接跟我说"做 PPT"，我会按标准流程执行：
   - Phase 1: 出框架确认
   - Phase 2: 推荐风格 + 生成 DEMO（1-2 页）
   - Phase 3: 你选风格后批量制作
   - Phase 4: 交付 HTML / PPTX / PDF

2. 指定品牌风格："用 Claude 风格做产品发布 PPT"
3. 指定模式："用杂志风做品牌发布"（E 模式）
4. 文档转换："把这份报告转成 PPT"（F 工具）

核心能力：
- 62 种品牌风格（Apple、Claude、Notion、Stripe、Linear、Tesla 等）
- 智能风格推荐（根据内容自动匹配 5 种 + 智能匹配）
- DEMO 先行（不是做好再换风格，而是先看 DEMO 再批量制作）
- 多格式输出（HTML 在线演示 / PPTX 可编辑 / PDF 归档）
- 可选 GPT 生图（你明确要视觉冲击时才调用）

详细文档：
- 标准工作流：流程文档/ppt-workflow-standard.md
- 五模式决策树：流程文档/ppt-five-mode-complete-integration.md
- 62 种品牌风格速查：.claude/skills/space-multi-design-ppt/references/brand-registry.md

现在可以试试："帮我做个产品发布会 PPT，12 页" 🎯
```

---

## 常见问题

**Q：安装失败怎么办？**
A：检查以下几点：
1. 确认有写权限（`$SKILLS_DIR` 和 `$WORK_DIR`）
2. 确认路径正确（不同 AI 环境的 skills 目录不同）
3. 手动复制：`cp -r skills/* ~/.claude/skills/`

**Q：不想安装所有 skills，只要部分可以吗？**
A：可以。最小安装只需：
- `space-multi-design-ppt`（G 工具，62 种品牌风格）
- `allaction-ppt-design`（五模式决策树）

**Q：工具脚本必须复制吗？**
A：不是。工具脚本是给 AI 调用的，放在任何 AI 能读到的地方都行。

**Q：如何卸载？**
A：删除对应目录：
```bash
rm -rf ~/.claude/skills/space-multi-design-ppt
rm -rf ~/.claude/skills/allaction-ppt-design
# ... 删除其他 skills
```

---

## 技术细节

**安装位置**：
- Claude Code: `~/.claude/skills/` 或项目级 `.claude/skills/`
- Codex: `~/.codex/skills/`
- Cursor: `~/.cursor/skills/`

**文件结构**（下载态 → 解压态）：
```
PPT制作工具包/
├── README.md                      # 总说明
├── README_AI_INSTALL.md           # 本文件（AI 自动安装指令）
├── README_USER.md                 # 用户说明文档
├── VERSION.md                     # 版本
├── 安全须知_API密钥.md            # 密钥安全
├── CLAUDE.md片段.txt              # 配置片段
├── 工具包制作工作记录.md          # 制作记录
└── PPT制作工具包_核心内容.zip     # 🔑 核心内容包（第 0 步解压）
        └─ 解压后还原出 ↓
           ├── skills/             # 8 个 skills（含上万 SVG 图标库）
           ├── 工具脚本/           # GPT 工具包 + 可编辑版式库
           ├── 流程文档/           # 9 份整合文档
           └── 编辑风HTML版式库/   # 34 套编辑风 HTML 版式
```

> **为什么打包 zip**：skills 内两个 ppt-master 系各带上万 SVG 图标，整包 2.5 万+ 碎文件，散着经微盘/网盘同步易漏传。压成单个 zip 传输可靠，AI 装前解压即可。**说明文件全部留在顶层明文，不进 zip**，方便人和 AI 直接看。

**工作流引擎**：
- 标准入口：`space-multi-design-ppt` skill
- 决策路由：`allaction-ppt-design` skill
- 五模式执行器：A（GPT 出图）/ B（可编辑）/ C（HTML slides）/ D（多代理评审）/ E（杂志风）
- F 工具层：F1（简单文档转换）/ F2（复杂文档多格式输出）
- 设计资源层：Huashu Design（独立调用）

---

**安装完成后，你（AI）要主动读取以下文档建立工作记忆**：
1. `流程文档/ppt-workflow-standard.md`（标准工作流，必读）
2. `流程文档/ppt-five-mode-complete-integration.md`（五模式决策树，必读）
3. `.claude/skills/space-multi-design-ppt/SKILL.md`（G 工具使用说明）

读完后，你就完全掌握了"PPT 制作工具包"的使用方式。用户说"做 PPT"时，你自动执行标准工作流。

---

**最后，提醒用户**：
> 本工具包是给 AI 用的，不是给人手动操作的。你（用户）只需要：
> 1. 下载工具包
> 2. 让 AI 读这个文件
> 3. AI 自动安装
> 4. 以后跟 AI 说"做 PPT"即可
>
> AI 会自动调用 8 个 skills、读取流程文档、执行标准工作流、生成 DEMO、批量制作、交付文件。
>
> 你不需要记住任何命令、不需要手动跑脚本、不需要看技术文档。AI 全帮你搞定 🎯
