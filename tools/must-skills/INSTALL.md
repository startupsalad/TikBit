# 必装 Skill 安装

## 安装前检查

先检查以下目录是否已有对应 Skill：

- Claude：`~/.claude/skills/{docx,xlsx,pptx,pdf,kb-retriever,skill-creator,defuddle}`
- GPT(Codex)：`~/.codex/skills/{docx,xlsx,pptx,pdf,kb-retriever,skill-creator,defuddle}`

已有同名目录时不要重复安装；确认版本后再决定是否用本包覆盖更新。

## 标准安装

在本目录运行：

```bash
node install-core.js
```

安装器会把 7 个 Skill 复制到 Claude 和 Codex 的系统 Skill 目录，并在全局及已登记的 Obsidian 知识库 `CLAUDE.md` / `AGENTS.md` 写入幂等提示。它会优先使用包内便携 Python（若用户拿的是旧平台包），Git 源码包没有便携 Python 时则检查本机 `python3`（Windows 为 `python` 或 `py`）。

文档类 Skill 的常用依赖：

```bash
python3 -m pip install python-docx openpyxl python-pptx pypdf pdfplumber reportlab pandas
```

Windows 可将 `python3` 换成 `python`。缺少 OCR、LibreOffice 或 Poppler 时，按具体任务另行安装。

## 卸载

```bash
node install-core.js --uninstall
```

卸载只移除本工具写入的提示块；通用 Skill 目录不会自动删除，避免误伤其他工具的依赖。
