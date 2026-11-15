#!/usr/bin/env bash
# Development mode: Python API (port 9998) + Angular dev server with hot reload (port 4200).
# The Angular dev server proxies /api to the Python server (src/client/proxy.conf.json).
set -u

# --- Colors (para manter a consistência com o teu script de run) ---
RESET='\033[0m'
BOLD='\033[1m'
RED='\033[31m'
GREEN='\033[32m'
YELLOW='\033[33m'
BLUE='\033[34m'
CYAN='\033[36m'

ROOT=$(dirname -- "$(realpath -- "$0")")
VENV_PY="$ROOT/.venv/bin/python"
BACKEND_PORT=${PROJECT_HUB_PORT:-9998}
FRONTEND_PORT=4200
BACKEND_LOG="$ROOT/backend.log"
FRONTEND_LOG="$ROOT/frontend.log"

show_help() {
  echo -e "${BOLD}${BLUE}Project Hub - Development Mode${RESET}"
  echo -e "Runs the Python API (port 9998) and the Angular dev server with hot reload (port $FRONTEND_PORT)."
  echo -e "Logs go to backend.log / frontend.log and are streamed to the terminal."
  echo -e ""
  echo -e "Usage: ${GREEN}./run-dev.sh${RESET} [OPTIONS]"
  echo -e ""
  echo -e "${BOLD}Options:${RESET}"
  echo -e "  ${CYAN}-h, --help${RESET}               Shows this help message and exits."
  echo -e ""
  echo -e "${BOLD}Environment Variables:${RESET}"
  echo -e "  ${YELLOW}PROJECT_HUB_PORT${RESET}         Backend port (default: 9998; the dev proxy expects 9998)"
  echo -e "  ${YELLOW}PROJECT_HUB_DATA_DIR${RESET}     Users and projects (default: $ROOT/data)"
  echo -e ""
  echo -e "Run ${GREEN}./build.sh${RESET} once first to install the dependencies."
}

while [[ "$#" -gt 0 ]]; do
  case $1 in
    -h|--help) show_help; exit 0 ;;
    *)
      echo -e "${RED}❌ Unknown parameter: $1${RESET}" >&2
      echo -e "Use ${CYAN}./run-dev.sh --help${RESET} to see available options." >&2
      exit 1
      ;;
  esac
done

# --- PRE-FLIGHT ---
if [ ! -x "$VENV_PY" ]; then
  echo -e "${RED}❌ Python environment not found ($ROOT/.venv). Run ./build.sh first.${RESET}"
  exit 1
fi
if [ ! -d "$ROOT/src/client/node_modules" ]; then
  echo -e "${RED}❌ Client dependencies not installed. Run ./build.sh first.${RESET}"
  exit 1
fi
if [ "$BACKEND_PORT" != 9998 ]; then
  echo -e "${YELLOW}⚠️  PROJECT_HUB_PORT=$BACKEND_PORT, but the dev proxy targets 9998 (src/client/proxy.conf.json).${RESET}"
fi

PIDS=()
cleanup() {
  # Remove traps para evitar loops recursivos no exit
  trap - EXIT INT TERM
  echo -e "\n${YELLOW}🛑 Stopping processes...${RESET}"
  for pid in "${PIDS[@]}"; do
    pkill -P "$pid" 2>/dev/null # Mata child processes (npx/node)
    kill "$pid" 2>/dev/null     # Mata parent process
  done
  wait 2>/dev/null
  echo -e "${GREEN}✅ System offline.${RESET}"
  exit 0
}
# O EXIT garante que o cleanup corre independentemente do motivo pela qual o script morre
trap cleanup EXIT INT TERM

: > "$BACKEND_LOG"
: > "$FRONTEND_LOG"

# --- BACKEND ---
echo -e "${BLUE}📡 Starting backend on port $BACKEND_PORT...${RESET}"
(cd "$ROOT/src" && exec "$VENV_PY" -m server) >> "$BACKEND_LOG" 2>&1 &
BACKEND_PID=$!
PIDS+=("$BACKEND_PID")

for _ in $(seq 30); do
  if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
    echo -e "${RED}❌ Backend failed to start:${RESET}"
    cat "$BACKEND_LOG"
    exit 1
  fi
  curl -s -o /dev/null "http://127.0.0.1:$BACKEND_PORT/api/health" && break
  sleep 0.5
done

# --- FRONTEND ---
echo -e "${CYAN}💻 Starting frontend on port $FRONTEND_PORT...${RESET}"
(cd "$ROOT/src/client" && exec npx ng serve --host 0.0.0.0 --port "$FRONTEND_PORT") >> "$FRONTEND_LOG" 2>&1 &
FRONTEND_PID=$!
PIDS+=("$FRONTEND_PID")

# Verificação básica se o frontend morre logo ao arrancar (ex: porta ocupada)
for _ in $(seq 6); do
  if ! kill -0 "$FRONTEND_PID" 2>/dev/null; then
    echo -e "${RED}❌ Frontend failed to start (check logs):${RESET}"
    cat "$FRONTEND_LOG"
    exit 1
  fi
  sleep 0.5
done

echo "---------------------------------------"
echo -e "${GREEN}🚀 Open http://localhost:$FRONTEND_PORT${RESET}"
echo -e "${BOLD}📖 Streaming logs (Ctrl+C to stop everything)${RESET}"
echo "---------------------------------------"
tail -f "$BACKEND_LOG" "$FRONTEND_LOG" &
PIDS+=("$!")

# 'wait -n' é a chave de estabilidade: se UM background process cair, destranca e faz shutdown seguro a tudo.
wait -n