#!/bin/zsh

set -u

PROJECT_DIR="$(cd -- "$(dirname -- "$0")" && pwd)"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"
BACKEND_PYTHON="$BACKEND_DIR/.venv/bin/python"
LOG_DIR="/tmp/weilan-daily-launcher"
BACKEND_LOG="$LOG_DIR/backend.log"
FRONTEND_LOG="$LOG_DIR/frontend.log"
FRONTEND_URL="http://localhost:3000"
BACKEND_STATUS_URL="http://127.0.0.1:8000/api/v1/status"

mkdir -p "$LOG_DIR"

pause_on_error() {
  echo
  echo "启动未完成，请把上面的提示发给 Codex 排查。"
  read -r "?按回车关闭窗口…"
  exit 1
}

wait_for_url() {
  local url="$1"
  local max_seconds="$2"
  local elapsed=0

  while (( elapsed < max_seconds )); do
    if /usr/bin/curl -fsS --max-time 2 "$url" >/dev/null 2>&1; then
      return 0
    fi
    /bin/sleep 1
    (( elapsed += 1 ))
  done

  return 1
}

clear
echo "========================================"
echo "       微蓝日报 · 一键启动"
echo "========================================"
echo

if [[ ! -x "$BACKEND_PYTHON" ]]; then
  echo "❌ 未找到后端运行环境：$BACKEND_PYTHON"
  pause_on_error
fi

NPM_BIN="$(command -v npm 2>/dev/null || true)"
if [[ -z "$NPM_BIN" ]]; then
  echo "❌ 未找到 npm，请先安装 Node.js。"
  pause_on_error
fi

if [[ ! -d "$FRONTEND_DIR/node_modules" ]]; then
  echo "❌ 前端依赖尚未安装：$FRONTEND_DIR/node_modules"
  pause_on_error
fi

if /usr/bin/curl -fsS --max-time 2 "$BACKEND_STATUS_URL" >/dev/null 2>&1; then
  echo "✓ 后端已在运行"
else
  echo "• 正在启动后端…"
  (
    cd "$BACKEND_DIR" || exit 1
    /usr/bin/env OPERATOR_PASSWORD="" /usr/bin/nohup "$BACKEND_PYTHON" -m uvicorn app.main:app \
      --host 127.0.0.1 --port 8000 >"$BACKEND_LOG" 2>&1 &
  )

  if wait_for_url "$BACKEND_STATUS_URL" 45; then
    echo "✓ 后端启动成功"
  else
    echo "❌ 后端启动超时，日志位置：$BACKEND_LOG"
    /usr/bin/tail -n 20 "$BACKEND_LOG" 2>/dev/null
    pause_on_error
  fi
fi

if /usr/bin/curl -fsS --max-time 2 "$FRONTEND_URL" >/dev/null 2>&1; then
  echo "✓ 前端已在运行"
else
  echo "• 正在启动前端…"
  (
    cd "$FRONTEND_DIR" || exit 1
    /usr/bin/env NEXT_TELEMETRY_DISABLED=1 /usr/bin/nohup "$NPM_BIN" run dev -- \
      --hostname localhost --port 3000 >"$FRONTEND_LOG" 2>&1 &
  )

  if wait_for_url "$FRONTEND_URL" 90; then
    echo "✓ 前端启动成功"
  else
    echo "❌ 前端启动超时，日志位置：$FRONTEND_LOG"
    /usr/bin/tail -n 20 "$FRONTEND_LOG" 2>/dev/null
    pause_on_error
  fi
fi

echo
echo "✓ 服务已就绪，正在打开：$FRONTEND_URL"
/usr/bin/open "$FRONTEND_URL"
/bin/sleep 2
