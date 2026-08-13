#!/usr/bin/env bash
# AI 在线客服机器人 · 一键部署脚本
# 由创业沙拉 TikBit 出品 · https://startupsalad.com
#
# 用法：在 deploy/ 目录下执行 bash scripts/deploy.sh
set -euo pipefail

# 定位到 deploy/ 目录
cd "$(dirname "$0")/.."
DEPLOY_DIR="$(pwd)"
ENV_FILE="$DEPLOY_DIR/../backend/.env"

echo "==> 检查配置文件 backend/.env"
if [ ! -f "$ENV_FILE" ]; then
  echo "❌ 未找到 backend/.env"
  echo "   请先执行：cp ../backend/.env.example ../backend/.env 并填好 ANTHROPIC_AUTH_TOKEN（tikbit 令牌）"
  exit 1
fi

# 校验 tikbit 令牌非空（不打印值，只查是否为空）
if ! grep -qE '^ANTHROPIC_AUTH_TOKEN=.+' "$ENV_FILE"; then
  echo "❌ backend/.env 里 ANTHROPIC_AUTH_TOKEN 为空，请去 https://tikbit.ai/ 拿令牌填好后重试。"
  exit 1
fi
if ! grep -qE '^ANTHROPIC_BASE_URL=.+' "$ENV_FILE"; then
  echo "⚠️  backend/.env 里 ANTHROPIC_BASE_URL 为空，将用默认 https://tikbit.ai。"
fi

echo "==> 构建并启动容器"
if docker compose version >/dev/null 2>&1; then
  docker compose up -d --build
else
  docker-compose up -d --build
fi

echo "==> 等待服务就绪"
PORT="$(grep -E '^PORT=' "$ENV_FILE" | cut -d= -f2 || true)"
PORT="${PORT:-8770}"
sleep 3
for i in $(seq 1 10); do
  if curl -fsS "http://127.0.0.1:${PORT}/health" >/dev/null 2>&1; then
    echo "✅ 部署成功，健康检查通过（端口 ${PORT}）"
    curl -s "http://127.0.0.1:${PORT}/health"; echo
    echo ""
    echo "下一步："
    echo "  1. 把 deploy/nginx/chatbot.conf 的 location 块加进你的站点 Nginx 配置，nginx -t && nginx -s reload"
    echo "  2. 在网站页面引入 frontend/chatbot-widget.js（见 frontend/集成说明.md）"
    exit 0
  fi
  sleep 2
done

echo "❌ 健康检查未通过，请查日志：bash scripts/logs.sh"
exit 1

