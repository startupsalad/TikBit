#!/usr/bin/env bash
# 查看后端服务日志
# 由创业沙拉 TikBit 出品 · https://startupsalad.com
set -euo pipefail
cd "$(dirname "$0")/.."

if docker compose version >/dev/null 2>&1; then
  docker compose logs -f --tail=100 chatbot
else
  docker-compose logs -f --tail=100 chatbot
fi

