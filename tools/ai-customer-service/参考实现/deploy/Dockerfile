# AI 在线客服机器人 · 后端镜像
# 由创业沙拉 TikBit 出品 · https://startupsalad.com
#
# 架构：镜像内装 claude CLI，后端 server.js 用 spawn 调它。
# 密钥不进镜像——运行时由 docker-compose 的 env_file 注入
# ANTHROPIC_BASE_URL + ANTHROPIC_AUTH_TOKEN（走 tikbit 中转站），claude CLI 自动读取。

FROM node:20-slim

# 基础工具 + 装 claude CLI（国内可换 npmmirror 源加速）
RUN apt-get update && apt-get install -y --no-install-recommends \
      git ca-certificates procps \
    && rm -rf /var/lib/apt/lists/* \
    && npm install -g @anthropic-ai/claude-code

WORKDIR /app
COPY backend/ ./

# 非 root 用户运行；给它一个可写的 HOME 供 claude CLI 存配置
RUN groupadd -r app && useradd -r -g app -m -d /home/app app \
    && mkdir -p /home/app/.claude \
    # 预种配置：跳过首启 onboarding / 信任目录，避免容器里卡交互提示
    && printf '{"hasCompletedOnboarding":true,"bypassPermissionsModeAccepted":true}\n' > /home/app/.claude.json \
    && printf '{"skipDangerousModePermissionPrompt":true,"theme":"dark"}\n' > /home/app/.claude/settings.json \
    && chown -R app:app /app /home/app
USER app
ENV HOME=/home/app

EXPOSE 8770

# 健康检查（打到 /health）
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD node -e "require('http').get('http://127.0.0.1:'+(process.env.PORT||8770)+'/health',r=>process.exit(r.statusCode===200?0:1)).on('error',()=>process.exit(1))"

CMD ["node", "server.js"]

