#!/usr/bin/env bash
# Runs the Python server, which serves both the API and the built client (./build.sh).
set -u

# --- Color Definitions ---
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
BACKEND_LOG="$ROOT/backend.log"

# --- Help Menu ---
show_help() {
  echo -e "${BOLD}${BLUE}Project Hub - Server Runner${RESET}"
  echo -e "Usage: ${GREEN}./run.sh${RESET} [OPTIONS]"
  echo -e ""
  echo -e "${BOLD}Options:${RESET}"
  echo -e "  ${CYAN}-c, --create-user${RESET} [name]   Creates a login user and exits."
  echo -e "  ${CYAN}-h, --help${RESET}                 Shows this help message and exits."
  echo -e ""
  echo -e "${BOLD}Environment Variables:${RESET}"
  echo -e "  ${YELLOW}PROJECT_HUB_HOST${RESET}       Address the server listens on (default: 0.0.0.0)"
  echo -e "  ${YELLOW}PROJECT_HUB_PORT${RESET}       Backend server port (default: 9998)"
  echo -e "  ${YELLOW}PROJECT_HUB_DATA_DIR${RESET}   Users and projects (default: $ROOT/data)"
  echo -e ""
  echo -e "Other user management: ${GREEN}cd src && ../.venv/bin/python -m server users --help${RESET}"
  exit 0
}

# --- Argument Parsing ---
ACTION="serve"
ARGS=()

while [[ "$#" -gt 0 ]]; do
  case $1 in
    -h|--help)
      show_help
      ;;
    -c|--create-user)
      ACTION="create-user"
      shift
      # Optional username, passed on to `server create-user --username`
      [ "$#" -gt 0 ] && ARGS=(--username "$1")
      break
      ;;
    *)
      echo -e "${RED}❌ Unknown parameter: $1${RESET}"
      echo -e "Use ${CYAN}./run.sh --help${RESET} to see available options."
      exit 1
      ;;
  esac
done

if [ ! -x "$VENV_PY" ]; then
  echo -e "${RED}❌ Python environment not found ($ROOT/.venv). Run ./build.sh first.${RESET}"
  exit 1
fi

# --- Execute Special Action: Create User ---
if [ "$ACTION" = "create-user" ]; then
  echo -e "${BLUE}👤 Starting create-user routine...${RESET}"
  cd "$ROOT/src" || exit 1
  # Exec replaces the current bash process with the python process (exits when done)
  exec "$VENV_PY" -m server create-user "${ARGS[@]}"
fi

# --- Execute Normal Server ---
if [ ! -f "$ROOT/dist/index.html" ]; then
  echo -e "${YELLOW}⚠️  Client build not found in $ROOT/dist — only the API will be available. Run ./build.sh.${RESET}"
fi

PIDS=()
cleanup() {
  echo -e "\n${YELLOW}🛑 Stopping...${RESET}"
  for pid in "${PIDS[@]}"; do kill "$pid" 2>/dev/null; done
  wait 2>/dev/null
  echo -e "${GREEN}✅ System offline.${RESET}"
  exit 0
}
trap cleanup INT TERM

: > "$BACKEND_LOG"

echo -e "${BLUE}📡 Starting server on port $BACKEND_PORT...${RESET}"
(cd "$ROOT/src" && exec "$VENV_PY" -m server) >> "$BACKEND_LOG" 2>&1 &
BACKEND_PID=$!
PIDS+=("$BACKEND_PID")

for _ in $(seq 30); do
  if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
    echo -e "${RED}❌ Server failed to start:${RESET}"
    cat "$BACKEND_LOG"
    exit 1
  fi
  curl -s -o /dev/null "http://127.0.0.1:$BACKEND_PORT/api/health" && break
  sleep 0.5
done

echo -e "${GREEN}🚀 Open http://localhost:$BACKEND_PORT${RESET}"
echo -e "${BOLD}📖 Streaming logs (Ctrl+C to stop)${RESET}"
echo "---------------------------------------"
tail -f "$BACKEND_LOG" &
PIDS+=("$!")
wait