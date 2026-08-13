#!/bin/bash
# 选择语音音色（macOS，双击运行）。按安装位置依次找引擎：
#   1) ~/.claude/      = AI 装的（给AI的安装指令.md 那条路，推荐）
#   2) ~/.task-voice/  = install.py 装的
#   3) 工具包 engine/  = 还没装，仅试听（选择结果不会生效）
cd "$(dirname "$0")"
TARGET="$HOME/.claude/pick-voice.sh"
[ -f "$TARGET" ] || TARGET="$HOME/.task-voice/pick-voice.sh"
[ -f "$TARGET" ] || TARGET="./engine/pick-voice.sh"
bash "$TARGET"
echo ""
read -n 1 -s -r -p "按任意键关闭"
