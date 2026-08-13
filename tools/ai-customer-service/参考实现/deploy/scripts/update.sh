#!/usr/bin/env bash
# 更新知识库/代码后重建重启
# 由创业沙拉 TikBit 出品 · https://startupsalad.com
set -euo pipefail
cd "$(dirname "$0")/.."

echo "==> 重建并重启容器"
if docker compose version >/dev/null 2>&1; then
  docker compose up -d --build
else
  docker-compose up -d --build
fi
echo "✅ 已重启。若只改了 knowledge-base/ 内容，也可只重启：docker compose restart chatbot"

