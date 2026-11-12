#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务语音通知工具包 · 安装器
做三件事：
  1) 把 engine/ 和 voice_clips/ 复制到本机固定位置 ~/.task-voice/（路径统一、不依赖同步盘）
  2) 让用户选音色（试听 + 存 choice.txt）
  3) 检测到 Claude Code 就备份并接好钩子（Notification/PreToolUse，不接Stop自动完成）；其它客户端打印一行手动说明
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
    existing = any((DEST / name).exists() for name in ('notify-voice.ps1', 'notify-voice.sh'))
    if existing:
        load_local('update').update(DEST)
    # 复制 engine 内容到 DEST 根（notify/pick/gate 脚本直接躺在 ~/.task-voice/）
    for f in (SRC / "engine").iterdir():
        if f.is_file() and (not existing or not (DEST / f.name).exists()):
            shutil.copy2(f, DEST / f.name)
    shutil.copy2(SRC / "VERSION", DEST / "VERSION")
    # 复制 voice_clips（整目录）
    dst_clips = DEST / "voice_clips"
    for clip in (SRC / 'voice_clips').rglob('*'):
        if not clip.is_file():
            continue
        target = dst_clips / clip.relative_to(SRC / 'voice_clips')
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(clip, target)
    # Mac 给 .sh 加执行权限
    if not IS_WIN:
        for sh in DEST.glob("*.sh"):
            os.chmod(sh, 0o755)
    log(f"[OK] 已复制语音引擎和音频到 {DEST}")


def pick_voice():
    if (DEST / 'choice.txt').is_file():
        log('保留已有音色；需要更换时单独运行选择语音。')
        return
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
    """Merge supported Claude hooks into the actual configuration homes."""
    rules = load_rules()
    roots = rules.client_homes(HOME, os.environ, 'CLAUDE_CONFIG_DIR', ['.claude', '.tikbit/claude'])
    return any([wire_settings_json(root / 'settings.json', 'Claude Code') for root in roots if root.is_dir()])


def load_rules():
    return load_local('rules')


def load_local(name):
    import importlib.util
    spec = importlib.util.spec_from_file_location('task_voice_' + name, SRC / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def wire_settings_json(settings, label):
    """Wire Claude Code settings.json."""
    if not settings.exists() and not settings.parent.is_dir():
        return False
    
    data = {}
    if settings.exists():
        try:
            data = json.loads(settings.read_text(encoding="utf-8-sig"))
            if not isinstance(data, dict) or not isinstance(data.get('hooks', {}), dict):
                raise ValueError('Invalid hook configuration')
            for groups in data.get('hooks', {}).values():
                if not isinstance(groups, list) or any(not isinstance(group, dict) or not isinstance(group.get('hooks', []), list) for group in groups):
                    raise ValueError('Invalid hook groups')
        except Exception:
            log(f"[!] {label} {settings.name} 解析失败，跳过自动接钩子（避免写坏）。")
            return False
    
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
        kept = []
        for group in stop:
            remaining = [hook for hook in group.get('hooks', []) if not (
                'notify-voice' in hook.get('command', '') and 'done-if-flagged' in hook.get('command', ''))]
            if remaining:
                kept.append({**group, 'hooks': remaining})
        if kept != stop:
            if kept:
                hooks["Stop"] = kept
            else:
                hooks.pop("Stop", None)
            log(f"[OK] {label} 已摘掉旧版 Stop→done-if-flagged 钩子")
    
    changed = kept != stop if stop else False
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
    gate_available = os.environ.get('TIKBIT_VOICE_ENABLE_GATE') == '1' and (DEST / ("notify-gate.ps1" if IS_WIN else "notify-gate.sh")).is_file()
    if gate_available and not already("PreToolUse", "notify-gate"):
        hooks.setdefault("PreToolUse", []).append(
            {"matcher": "*",
             "hooks": [{"type": "command", "command": gate_command("arm")}]})
        changed = True
    if gate_available and not already("PostToolUse", "notify-gate"):
        hooks.setdefault("PostToolUse", []).append(
            {"matcher": "*",
             "hooks": [{"type": "command", "command": gate_command("clear")}]})
        changed = True
    
    if changed:
        if settings.exists():
            bak = settings.with_suffix(f".json.bak-{time.strftime('%Y%m%d-%H%M%S')}-{time.time_ns()}")
            shutil.copy2(settings, bak)
            log(f"[OK] 已备份 {label} {settings.name} → {bak.name}")
        settings.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        log(f"[OK] {label} 已接通知/决策钩子" + ("，包含可用授权监测gate" if gate_available else "；平台无gate引擎，未写无效授权监测"))
        log("  完成播报只由主对话整轮交付时喊 done，子代理禁止播报（见安装指令第5步）。")
        log(f"  提示：需重启 {label} 才生效。")
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
    rules = load_rules()
    pending = rules.rule_writes(DEST, HOME)
    copy_assets()
    pick_voice()
    wired = wire_claude_code()
    rules.apply_rule_writes(pending, DEST)
    log("\n==== 完成 ====")
    if wired:
        log("Claude Code 通知钩子与双引擎四类提醒规则已合并；新会话再验证。")
        log("  任务完成播报只由主对话整轮交付时喊 done，子代理禁止播报——把『给AI的安装指令.md』给你的 AI，让它更新记忆规则。")
    else:
        log("没检测到 Claude Code。如果你用别的 AI 客户端：")
        log("  把『给AI的安装指令.md』丢给你的 AI，让它把通知命令接到对应位置；")
        log("  或让 AI 在干完长活时调用下面命令：")
        log("    " + notify_command("done"))
    log(f"\n随时换声音：运行 {DEST} 里的 pick-voice（Win 是 .ps1 / Mac 是 .sh），")
    log("GPT 不使用 Claude 的钩子事件；原生弹窗自动提醒需要配套工作台插件和管理安装。")
    log("或双击工具包里的『选择语音』。")


if __name__ == "__main__":
    main()
