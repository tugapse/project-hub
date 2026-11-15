#!/usr/bin/env bash
# Creates .venv, installs the server dependencies and builds the client into dist/.
#
#   PROJECT_HUB_BASE_HREF  base path the client is served from (default "/"; e.g. "/hub/" behind nginx)
set -euo pipefail

RESET='\033[0m'
BOLD='\033[1m'
RED='\033[31m'
GREEN='\033[32m'
YELLOW='\033[33m'
BLUE='\033[34m'
CYAN='\033[36m'

show_help() {
  echo -e "${BOLD}${BLUE}Project Hub - Build${RESET}"
  echo -e "Creates .venv, installs the server dependencies and builds the client into dist/."
  echo -e ""
  echo -e "Usage: ${GREEN}./build.sh${RESET} [OPTIONS]"
  echo -e ""
  echo -e "${BOLD}Options:${RESET}"
  echo -e "  ${CYAN}-h, --help${RESET}               Shows this help message and exits."
  echo -e ""
  echo -e "${BOLD}Environment Variables:${RESET}"
  echo -e "  ${YELLOW}PROJECT_HUB_BASE_HREF${RESET}    Path the client is served from (default: /; e.g. /hub/ behind nginx)"
  echo -e ""
  echo -e "Requires python3 (with venv) and Node ${BOLD}>= 20.19${RESET} with npm."
}

while [[ "$#" -gt 0 ]]; do
  case $1 in
    -h|--help) show_help; exit 0 ;;
    *)
      echo -e "${RED}❌ Unknown parameter: $1${RESET}" >&2
      echo -e "Use ${CYAN}./build.sh --help${RESET} to see available options." >&2
      exit 1
      ;;
  esac
done

SCRIPT_DIR=$(dirname -- "$(realpath -- "$0")")
BASE_HREF=${PROJECT_HUB_BASE_HREF:-/}
cd "$SCRIPT_DIR"

echo "Checking system dependencies..."
if ! command -v python3 &> /dev/null; then
  echo "Error: python3 is not installed." >&2
  exit 1
fi
if ! python3 -m venv -h &> /dev/null; then
  echo "Error: python3-venv is not installed." >&2
  exit 1
fi
if ! command -v npm &> /dev/null; then
  echo "Error: node/npm is not installed." >&2
  exit 1
fi

if [ ! -d ".venv" ]; then
  echo "Creating Python virtual environment..."
  python3 -m venv .venv
fi

echo "Installing server dependencies..."
.venv/bin/pip install --quiet --upgrade pip
.venv/bin/pip install --quiet -r src/server/requirements.txt

(
  cd src/client
  echo "Installing Node dependencies..."
  # `ci` installs exactly what package-lock.json says and never rewrites it.
  npm ci --no-audit --no-fund
  echo "Building Angular client (base href: $BASE_HREF)..."
  npm run build-to-server -- --base-href "$BASE_HREF"
)

echo ""
echo "======================================================"
echo "Build completed successfully!"
echo "Environment variables read by the server:"
echo " * PROJECT_HUB_HOST defaults to 0.0.0.0"
echo " * PROJECT_HUB_PORT defaults to 9998"
echo " * PROJECT_HUB_DATA_DIR defaults to $SCRIPT_DIR/data"
echo "To start the application, run ./run.sh"
echo "======================================================"
