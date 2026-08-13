#!/usr/bin/env bash
# ai-radar 一键安装到 Claude Code / 兼容 agent 的 skills 目录
# 用法: ./install.sh [目标目录]   默认 ~/.claude/skills/ai-radar
set -euo pipefail
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST="${1:-$HOME/.claude/skills/ai-radar}"
mkdir -p "$(dirname "$DEST")"
cp -r "$SRC" "$DEST"
# 不随 skill 分发开发文件
rm -rf "$DEST/.git" 2>/dev/null || true
find "$DEST" -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null || true
echo "✓ ai-radar 已安装到 $DEST"
echo "  重开会话后说「给我今天的 AI 日报」即可触发。"
