#!/usr/bin/env bash
# 同时启动后端 (FastAPI) 与前端 (Vite)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
UVICORN="$ROOT/server/venv/bin/uvicorn"

if [[ ! -x "$UVICORN" ]]; then
  echo "❌ 未找到后端虚拟环境，请先执行："
  echo "   cd server && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
  exit 1
fi

if [[ ! -d "$ROOT/web/node_modules" ]]; then
  echo "❌ 未找到前端依赖，请先执行："
  echo "   cd web && pnpm install"
  exit 1
fi

if command -v pnpm &>/dev/null; then
  WEB_CMD="pnpm dev"
else
  WEB_CMD="npm run dev"
fi

cleanup() {
  echo ""
  echo "正在停止服务…"
  kill 0 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "🚀 启动 OmniChat"
echo "   后端  http://localhost:8000/docs"
echo "   前端  http://localhost:5173"
echo "   按 Ctrl+C 同时停止"
echo ""

cd "$ROOT/server"
"$UVICORN" main:app --reload --host 0.0.0.0 --port 8000 &
SERVER_PID=$!

echo "⏳ 等待后端就绪…"
READY=0
for _ in $(seq 1 60); do
  if curl -sf "http://127.0.0.1:8000/health" >/dev/null 2>&1; then
    READY=1
    break
  fi
  sleep 0.5
done

if [[ "$READY" -ne 1 ]]; then
  echo "❌ 后端在 30 秒内未启动，请检查 server/.env 与终端报错"
  kill "$SERVER_PID" 2>/dev/null || true
  exit 1
fi

echo "✅ 后端已就绪，启动前端…"
echo ""

cd "$ROOT/web"
$WEB_CMD &
WEB_PID=$!

wait "$SERVER_PID" "$WEB_PID"
