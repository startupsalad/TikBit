#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
对话长度提醒工具包 · 安装器
做两件事：
  1) 把 engine/context_reminder.py 复制到本机固定位置 ~/.context-reminder/（路径统一、不依赖同步盘）
  2) 检测到 Claude Code 就备份并安全合并 UserPromptSubmit 钩子；其它客户端打印手动说明
全程零外部依赖，只用 Python 标准库。
原理：钩子在用户每次发消息时量出"当前上下文 token 量"，到阈值就注入一句提醒，
让 AI 主动提示你开新对话/清上下文——长对话每轮重读全部历史，是 token 账单的主力。
"""
import json, os, platform, shutil, sys, time
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:
        pass

SRC = Path(__file__).resolve().parent
HOME = Path.home()
DEST = HOME / ".context-reminder"
PYEXE = sys.executable.replace("\\", "/")  # 把当前 python 绝对路径烘进钩子命令，最稳


def log(msg):
    print(msg, flush=True)


def copy_assets():
    DEST.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SRC / "engine" / "context_reminder.py", DEST / "context_reminder.py")
    log(f"[OK] 已复制提醒引擎到 {DEST}")


def hook_command():
    p = str(DEST / "context_reminder.py").replace("\\", "/")
    # 钩子在 bash 下执行（Win 也走 Git Bash），PYTHONUTF8=1 防中文乱码，失败也不阻塞用户
    return f'PYTHONUTF8=1 "{PYEXE}" "{p}" 2>/dev/null || true'


def wire_claude_code():
    """检测 Claude Code 并安全合并 UserPromptSubmit 钩子。返回 True 表示已接。"""
    cdir = HOME / ".claude"
    if not cdir.is_dir():
        return False
    settings = cdir / "settings.json"
    data = {}
    if settings.exists():
        try:
            data = json.loads(settings.read_text(encoding="utf-8"))
        except Exception:
            log("[!] 已有 settings.json 解析失败，跳过自动接钩子（避免写坏）。请用 AI 安装路线或手动接。")
            return False
        bak = settings.with_suffix(f".json.bak-{time.strftime('%Y%m%d-%H%M%S')}")
        shutil.copy2(settings, bak)
        log(f"[OK] 已备份原 settings.json → {bak.name}")

    hooks = data.setdefault("hooks", {})

    def already(event, needle):
        for grp in hooks.get(event, []):
            for h in grp.get("hooks", []):
                if needle in h.get("command", ""):
                    return True
        return False

    if already("UserPromptSubmit", "context_reminder"):
        log("[OK] 钩子已存在，无需重复添加。")
    else:
        hooks.setdefault("UserPromptSubmit", []).append(
            {"hooks": [{"type": "command", "command": hook_command()}]})
        settings.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        log("[OK] 已给 Claude Code 接好对话长度提醒钩子（UserPromptSubmit）")
    log("  提示：需重启 Claude Code 才生效。")
    return True


def main():
    log("==== 对话长度提醒工具包 · 安装 ====")
    copy_assets()
    wired = wire_claude_code()
    log("\n==== 完成 ====")
    if wired:
        log("Claude Code 用户：重启后，对话上下文涨到阈值时，AI 会主动提醒你开新对话/清上下文。")
        log("阈值默认 130K / 230K / 350K token，想调改 ~/.context-reminder/context_reminder.py 顶部的 BANDS。")
    else:
        log("没检测到 Claude Code。其它 AI 客户端：把『给AI的安装指令.md』丢给你的 AI，")
        log("让它把本引擎接到该客户端的『用户发消息』钩子上（输出会注入上下文即可生效）。")


if __name__ == "__main__":
    main()
