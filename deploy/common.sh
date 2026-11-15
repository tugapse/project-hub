# Shared helpers for the deploy scripts (sourced, not executed).

COLOR_RESET='\033[0m'
COLOR_RED='\033[0;31m'
COLOR_GREEN='\033[0;32m'
COLOR_YELLOW='\033[0;33m'
COLOR_BLUE='\033[0;34m'

log_info()    { echo -e "${COLOR_BLUE}==>${COLOR_RESET} $*"; }
log_success() { echo -e "${COLOR_GREEN}✅ $*${COLOR_RESET}"; }
log_warn()    { echo -e "${COLOR_YELLOW}⚠️  $*${COLOR_RESET}"; }
log_error()   { echo -e "${COLOR_RED}❌ $*${COLOR_RESET}" >&2; }
die()         { log_error "$*"; exit 1; }

BOLD='\033[1m'
COLOR_CYAN='\033[0;36m'

# Handles -h/--help (calls the script's show_help) and rejects anything else.
parse_args() {
  while [[ "$#" -gt 0 ]]; do
    case $1 in
      -h|--help) show_help; exit 0 ;;
      *) die "Unknown parameter: $1 (see $0 --help)" ;;
    esac
  done
}

# Prints the settings table shared by the deploy scripts.
help_settings() {
  echo -e "${BOLD}Settings (environment variables, current value):${COLOR_RESET}"
  local var
  for var in "$@"; do
    printf "  ${COLOR_YELLOW}%-14s${COLOR_RESET} %s\n" "$var" "${!var}"
  done
}

require_root() {
  [ "$EUID" -eq 0 ] || die "Please run as root (sudo $0)."
}

# --- Settings shared by install.sh and setup-nginx.sh (override via environment) ---

# Parent folder of the checkout; the data lives next to it (same disk, e.g. an external HDD).
DES_FOLDER=${DES_FOLDER:-/opt}
TARGET_DIR=${TARGET_DIR:-$DES_FOLDER/project-hub}
DATA_DIR=${DATA_DIR:-$(dirname -- "$TARGET_DIR")/project-hub-data}

REPO_URL=${REPO_URL:-https://github.com/tugapse/project-hub}
BRANCH=${BRANCH:-master}

SERVICE_NAME=project-hub
SERVICE_USER=${SERVICE_USER:-project-hub}
APP_PORT=${APP_PORT:-9998}
# Path nginx serves the app under (must start and end with "/").
BASE_PATH=${BASE_PATH:-/hub/}

ENV_FILE=/etc/default/project-hub
