#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务语音通知工具包 · 安装器
做三件事：
  1) 把 engine/ 和 voice_clips/ 复制到本机固定位置 ~/.task-voice/（路径统一、不依赖同步盘）
  2) 让用户选音色（试听 + 存 choice.txt）
  3) 检测到 Claude Code 就备份并接好钩子（Stop/Notification/PreToolUse）；其它客户端打印一行手动说明
全程零外部依赖，只用 Python 标准库。
"""
import json, os, platform, shutil, subprocess, sys, time
from pathlib import Path

# Windows 控制台默认 GBK，强制 stdout/stderr 走 UTF-8，避免中文/符号编码崩溃
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:
        pass

SRC = Path(__file__).resolve().parent          # 工具包源目录（同步盘里）
HOME = Path.home()
DEST = HOME / ".task-voice"                     # 本机安装目标
IS_WIN = platform.system() == "Windows"
IS_MAC = platform.system() == "Darwin"


def log(msg): print(msg, flush=True)


def copy_assets():
    DEST.mkdir(parents=True, exist_ok=True)
    # 复制 engine 内容到 DEST 根（notify/pick/gate 脚本直接躺在 ~/.task-voice/）
    for f in (SRC / "engine").iterdir():
        if f.is_file():
            shutil.copy2(f, DEST / f.name)
    # 复制 voice_clips（整目录）
    dst_clips = DEST / "voice_clips"
    if dst_clips.exists():
        shutil.rmtree(dst_clips)
    shutil.copytree(SRC / "voice_clips", dst_clips)
    # Mac 给 .sh 加执行权限
    if not IS_WIN:
        for sh in DEST.glob("*.sh"):
            os.chmod(sh, 0o755)
    # 清掉旧机制遗留的长任务标记（完成播报已改主动喊 done，不再用标记）
    old_flag = DEST / ".flag"
    if old_flag.exists():
        try:
            old_flag.unlink()
        except Exception:
            pass
    log(f"[OK] 已复制语音引擎和音频到 {DEST}")


def pick_voice():
    """调选音色工具让用户试听+选择。"""
    log("\n--- 选择你喜欢的声音 ---")
    try:
        if IS_WIN:
            subprocess.call(["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
                             "-File", str(DEST / "pick-voice.ps1")])
        else:
            subprocess.call(["bash", str(DEST / "pick-voice.sh")])
    except Exception as e:
        log(f"（选音色工具没跑起来，先用默认晓晓，回头可手动运行 pick-voice。{e}）")
    if not (DEST / "choice.txt").exists():
        (DEST / "choice.txt").write_text("xiaoxiao", encoding="utf-8")


def notify_command(mode):
    """生成指向已安装引擎的钩子命令字符串。"""
    if IS_WIN:
        p = str(DEST / "notify-voice.ps1").replace("\\", "/")
        return (f'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "{p}" '
                f'-Mode {mode} 2>/dev/null || true')
    else:
        p = str(DEST / "notify-voice.sh")
        return f'bash "{p}" {mode} 2>/dev/null || true'


def wire_claude_code():
    """检测 Claude Code/Codex 并安全合并钩子（Notification/PreToolUse + 授权检测 gate）。返回 True 表示已接。"""
    # Both clients use hooks now
    claude_settings = HOME / ".claude" / "settings.json"
    codex_hooks = HOME / ".codex" / "hooks.json"
    
    wired_any = False
    
    # ===== Claude Code =====
    if (HOME / ".claude").is_dir():
        wired_any |= wire_settings_json(claude_settings, "Claude Code")
    
    # ===== Codex =====
    if (HOME / ".codex").is_dir():
        wired_any |= wire_hooks_json(codex_hooks, "Codex")
    
    return wired_any


def wire_settings_json(settings, label):
    """Wire Claude Code settings.json."""
    if not settings.exists() and not settings.parent.is_dir():
        return False
    
    data = {}
    if settings.exists():
        try:
            data = json.loads(settings.read_text(encoding="utf-8"))
        except Exception:
            log(f"[!] {label} {settings.name} 解析失败，跳过自动接钩子（避免写坏）。")
            return False
        bak = settings.with_suffix(f".json.bak-{time.strftime('%Y%m%d-%H%M%S')}")
        shutil.copy2(settings, bak)
        log(f"[OK] 已备份 {label} {settings.name} → {bak.name}")
    
    hooks = data.setdefault("hooks", {})
    
    def already(event, needle):
        for grp in hooks.get(event, []):
            for h in grp.get("hooks", []):
                if needle in h.get("command", ""):
                    return True
        return False
    
    # 迁移：摘掉早期版本装的 Stop→done-if-flagged 钩子
    stop = hooks.get("Stop", [])
    if stop:
        kept = [g for g in stop if not any(
            ("notify-voice" in h.get("command", "")) and ("done-if-flagged" in h.get("command", ""))
            for h in g.get("hooks", []))]
        if len(kept) != len(stop):
            if kept:
                hooks["Stop"] = kept
            else:
                hooks.pop("Stop", None)
            log(f"[OK] {label} 已摘掉旧版 Stop→done-if-flagged 钩子")
    
    changed = False
    if not already("Notification", "notify-voice"):
        hooks.setdefault("Notification", []).append(
            {"hooks": [{"type": "command", "command": notify_command("notify")}]})
        changed = True
    if not already("PreToolUse", "notify-voice"):
        hooks.setdefault("PreToolUse", []).append(
            {"matcher": "AskUserQuestion|ExitPlanMode",
             "hooks": [{"type": "command", "command": notify_command("ask")}]})
        changed = True
    
    # 新增：gate 授权检测钩子（matcher *）
    if not already("PreToolUse", "notify-gate"):
        hooks.setdefault("PreToolUse", []).append(
            {"matcher": "*",
             "hooks": [{"type": "command", "command": gate_command("arm")}]})
        changed = True
    if not already("PostToolUse", "notify-gate"):
        hooks.setdefault("PostToolUse", []).append(
            {"matcher": "*",
             "hooks": [{"type": "command", "command": gate_command("clear")}]})
        changed = True
    
    if changed:
        settings.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        log(f"[OK] {label} 已接钩子：Notification→等待/PreToolUse→让你拿主意+授权检测gate")
        log("  完成播报由 AI 干完那轮主动喊 done（见『给AI的安装指令.md』第 4 步）。")
        log(f"  提示：需重启 {label} 才生效。")
    return True


def wire_hooks_json(hooks_file, label):
    """Wire Codex hooks.json."""
    if not hooks_file.parent.is_dir():
        return False
    
    data = {}
    if hooks_file.exists():
        try:
            data = json.loads(hooks_file.read_text(encoding="utf-8"))
        except Exception:
            log(f"[!] {label} {hooks_file.name} 解析失败，跳过。")
            return False
        bak = hooks_file.with_suffix(f".json.bak-{time.strftime('%Y%m%d-%H%M%S')}")
        shutil.copy2(hooks_file, bak)
        log(f"[OK] 已备份 {label} {hooks_file.name} → {bak.name}")
    
    hooks = data.setdefault("hooks", {})
    
    def already(event, needle):
        for grp in hooks.get(event, []):
            for h in grp.get("hooks", []):
                if needle in h.get("command", ""):
                    return True
        return False
    
    changed = False
    if not already("Notification", "notify-voice"):
        hooks.setdefault("Notification", []).append(
            {"hooks": [{"type": "command", "command": notify_command("notify")}]})
        changed = True
    if not already("PreToolUse", "notify-voice"):
        hooks.setdefault("PreToolUse", []).append(
            {"matcher": "AskUserQuestion|ExitPlanMode",
             "hooks": [{"type": "command", "command": notify_command("ask")}]})
        changed = True
    
    # gate 授权检测
    if not already("PreToolUse", "notify-gate"):
        hooks.setdefault("PreToolUse", []).append(
            {"matcher": "*",
             "hooks": [{"type": "command", "command": gate_command("arm")}]})
        changed = True
    if not already("PostToolUse", "notify-gate"):
        hooks.setdefault("PostToolUse", []).append(
            {"matcher": "*",
             "hooks": [{"type": "command", "command": gate_command("clear")}]})
        changed = True
    
    if changed:
        hooks_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        log(f"[OK] {label} 已接钩子：Notification→等待/PreToolUse→让你拿主意+授权检测gate")
        log(f"  提示：{label} 可能需要重启才生效。")
    return True


def gate_command(mode):
    """生成指向已安装 gate 引擎的钩子命令字符串。"""
    if IS_WIN:
        p = str(DEST / "notify-gate.ps1").replace(chr(92), "/")
        return (f'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "{p}" '
                f'-Mode {mode} 2>/dev/null || true')
    else:
        p = str(DEST / "notify-gate.sh")
        return f'bash "{p}" {mode} 2>/dev/null || true'



def main():
    log("==== 任务语音通知工具包 · 安装 ====")
    copy_assets()
    pick_voice()
    wired = wire_claude_code()
    log("\n==== 完成 ====")
    if wired:
        log("Claude Code 用户：重启后，等待/授权/让你拿主意会语音提醒；")
        log("  任务完成播报由 AI 干完那轮主动喊 done——把『给AI的安装指令.md』给你的 AI，让它更新记忆规则。")
    else:
        log("没检测到 Claude Code。如果你用别的 AI 客户端：")
        log("  把『给AI的安装指令.md』丢给你的 AI，让它把通知命令接到对应位置；")
        log("  或让 AI 在干完长活时调用下面命令：")
        log("    " + notify_command("done"))
    log(f"\n随时换声音：运行 {DEST} 里的 pick-voice（Win 是 .ps1 / Mac 是 .sh），")
    log("或双击工具包里的『选择语音』。")


if __name__ == "__main__":
    main()
