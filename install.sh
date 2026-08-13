#!/usr/bin/env bash
set -euo pipefail
TOOL="${1:-}"
DESTINATION="${TIKBIT_HOME:-$HOME/.tikbit/TikBit}"
REPO="https://github.com/startupsalad/TikBit.git"
command -v git >/dev/null || { echo "需要先安装 Git" >&2; exit 1; }
mkdir -p "$(dirname "$DESTINATION")"
if [[ -d "$DESTINATION/.git" ]]; then
  git -C "$DESTINATION" pull --ff-only
else
  git clone "$REPO" "$DESTINATION"
fi
if [[ -n "$TOOL" ]]; then
  [[ -d "$DESTINATION/tools/$TOOL" ]] || { echo "未找到工具：$TOOL" >&2; exit 1; }
  echo "已安装/更新 $TOOL 到 $DESTINATION/tools/$TOOL"
  echo "下一步请读取 $DESTINATION/tools/$TOOL/INSTALL.md"
else
  echo "TikBit 工具库已安装/更新到 $DESTINATION"
  echo "请读取 $DESTINATION/catalog.json 选择工具。"
fi
echo "需要 API Key 的工具必须由用户在本机自行配置。"
