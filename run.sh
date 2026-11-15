#!/usr/bin/env bash
# Runs the Python server, which serves both the API and the built client (./build.sh).
set -u

ROOT=$(dirname -- "$(realpath -- "$0")")
VENV_PY="$ROOT/.venv/bin/python"
BACKEND_PORT=${PROJECT_HUB_PORT:-9998}
BACKEND_LOG="$ROOT/backend.log"

if [ ! -x "$VENV_PY" ]; then
  echo "❌ Python environment not found ($ROOT/.venv). Run ./build.sh first."
  exit 1
fi
if [ ! -f "$ROOT/dist/index.html" ]; then
  echo "⚠️  Client build not found in $ROOT/dist — only the API will be available. Run ./build.sh."
fi

PIDS=()
cleanup() {
  echo -e "\n🛑 Stopping..."
  for pid in "${PIDS[@]}"; do kill "$pid" 2>/dev/null; done
  wait 2>/dev/null
  echo "✅ System offline."
  exit 0
}
trap cleanup INT TERM

: > "$BACKEND_LOG"

echo "📡 Starting server on port $BACKEND_PORT..."
(cd "$ROOT/src" && exec "$VENV_PY" -m server) >> "$BACKEND_LOG" 2>&1 &
BACKEND_PID=$!
PIDS+=("$BACKEND_PID")

for _ in $(seq 30); do
  if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
    echo "❌ Server failed to start:"
    cat "$BACKEND_LOG"
    exit 1
  fi
  curl -s -o /dev/null "http://127.0.0.1:$BACKEND_PORT/api/projects" && break
  sleep 0.5
done

echo "🚀 Open http://localhost:$BACKEND_PORT"
echo "📖 Streaming logs (Ctrl+C to stop)"
echo "---------------------------------------"
tail -f "$BACKEND_LOG" &
PIDS+=("$!")
wait
