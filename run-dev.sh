#!/usr/bin/env bash
# Development mode: Python API (port 9998) + Angular dev server with hot reload (port 4200).
# The Angular dev server proxies /api to the Python server (src/client/proxy.conf.json).
set -u

ROOT=$(dirname -- "$(realpath -- "$0")")
VENV_PY="$ROOT/.venv/bin/python"
BACKEND_PORT=${PROJECT_HUB_PORT:-9998}
FRONTEND_PORT=4200
BACKEND_LOG="$ROOT/backend.log"
FRONTEND_LOG="$ROOT/frontend.log"

# --- PRE-FLIGHT ---
if [ ! -x "$VENV_PY" ]; then
  echo "❌ Python environment not found ($ROOT/.venv). Run ./build.sh first."
  exit 1
fi
if [ ! -d "$ROOT/src/client/node_modules" ]; then
  echo "❌ Client dependencies not installed. Run ./build.sh first."
  exit 1
fi
if [ "$BACKEND_PORT" != 9998 ]; then
  echo "⚠️  PROJECT_HUB_PORT=$BACKEND_PORT, but the dev proxy targets 9998 (src/client/proxy.conf.json)."
fi

PIDS=()
cleanup() {
  echo -e "\n🛑 Stopping..."
  for pid in "${PIDS[@]}"; do
    pkill -P "$pid" 2>/dev/null
    kill "$pid" 2>/dev/null
  done
  wait 2>/dev/null
  echo "✅ System offline."
  exit 0
}
trap cleanup INT TERM

: > "$BACKEND_LOG"
: > "$FRONTEND_LOG"

# --- BACKEND ---
echo "📡 Starting backend on port $BACKEND_PORT..."
(cd "$ROOT/src" && exec "$VENV_PY" -m server) >> "$BACKEND_LOG" 2>&1 &
BACKEND_PID=$!
PIDS+=("$BACKEND_PID")

for _ in $(seq 30); do
  if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
    echo "❌ Backend failed to start:"
    cat "$BACKEND_LOG"
    exit 1
  fi
  curl -s -o /dev/null "http://127.0.0.1:$BACKEND_PORT/api/health" && break
  sleep 0.5
done

# --- FRONTEND ---
echo "💻 Starting frontend on port $FRONTEND_PORT..."
(cd "$ROOT/src/client" && exec npx ng serve --host 0.0.0.0 --port "$FRONTEND_PORT") >> "$FRONTEND_LOG" 2>&1 &
PIDS+=("$!")

echo "---------------------------------------"
echo "🚀 Open http://localhost:$FRONTEND_PORT"
echo "📖 Streaming logs (Ctrl+C to stop everything)"
echo "---------------------------------------"
tail -f "$BACKEND_LOG" "$FRONTEND_LOG" &
PIDS+=("$!")
wait
