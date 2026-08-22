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
# 只用无需登录且始终存在的根页面判断服务是否就绪。
# 往期日报接口需要登录，不能作为启动探针，否则会因 401 被误判为启动失败。
BACKEND_STATUS_URL="http://127.0.0.1:8000/"

mkdir -p "$LOG_DIR"

pause_on_error() {
  echo
  echo "启动未完成，请把上面的提示发给 Codex 排查。"
  if [[ -t 0 ]]; then
    read -r "?按回车关闭窗口…"
  fi
  exit 1
}

listener_pid() {
  local port="$1"
  /usr/sbin/lsof -nP -tiTCP:"$port" -sTCP:LISTEN 2>/dev/null | /usr/bin/head -n 1
}

process_cwd() {
  local pid="$1"
  /usr/sbin/lsof -a -p "$pid" -d cwd -Fn 2>/dev/null \
    | /usr/bin/sed -n 's/^n//p' \
    | /usr/bin/head -n 1
}

stop_project_listener() {
  local port="$1"
  local expected_dir="$2"
  local label="$3"
  local pid
  local cwd
  local elapsed=0

  pid="$(listener_pid "$port")"
  if [[ -z "$pid" ]]; then
    return 0
  fi

  cwd="$(process_cwd "$pid")"
  if [[ "$cwd" != "$expected_dir" ]]; then
    echo "❌ 端口 $port 已被其他程序占用，未对它做任何操作。"
    echo "   占用进程：$pid"
    echo "   所在目录：${cwd:-无法识别}"
    return 1
  fi

  echo "• 正在刷新${label}（旧进程 $pid）…"
  /bin/kill -TERM "$pid" 2>/dev/null || true
  while (( elapsed < 15 )); do
    if [[ -z "$(listener_pid "$port")" ]]; then
      return 0
    fi
    /bin/sleep 1
    (( elapsed += 1 ))
  done

  echo "❌ ${label}旧进程未能正常退出，请重启电脑后再试。"
  return 1
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

if [[ -t 1 ]]; then
  clear
fi
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

stop_project_listener 3000 "$FRONTEND_DIR" "前端" || pause_on_error
stop_project_listener 8000 "$BACKEND_DIR" "后端" || pause_on_error

echo "• 正在启动后端…"
(
  cd "$BACKEND_DIR" || exit 1
  /usr/bin/env OPERATOR_PASSWORD="" /usr/bin/nohup "$BACKEND_PYTHON" -m uvicorn app.main:app \
    --host 127.0.0.1 --port 8000 >"$BACKEND_LOG" 2>&1 </dev/null &!
)

if wait_for_url "$BACKEND_STATUS_URL" 45; then
  echo "✓ 后端启动成功"
else
  echo "❌ 后端启动超时，日志位置：$BACKEND_LOG"
  /usr/bin/tail -n 20 "$BACKEND_LOG" 2>/dev/null
  pause_on_error
fi

echo "• 正在启动前端…"
(
  cd "$FRONTEND_DIR" || exit 1
  /usr/bin/env NEXT_TELEMETRY_DISABLED=1 /usr/bin/nohup "$NPM_BIN" run dev -- \
    --hostname localhost --port 3000 >"$FRONTEND_LOG" 2>&1 </dev/null &!
)

if wait_for_url "$FRONTEND_URL" 90; then
  echo "✓ 前端启动成功"
else
  echo "❌ 前端启动超时，日志位置：$FRONTEND_LOG"
  /usr/bin/tail -n 20 "$FRONTEND_LOG" 2>/dev/null
  pause_on_error
fi

echo
echo "✓ 服务已就绪，正在打开：$FRONTEND_URL"
if [[ "${WEILAN_SKIP_OPEN:-0}" != "1" ]]; then
  /usr/bin/open "$FRONTEND_URL"
fi
/bin/sleep 2
