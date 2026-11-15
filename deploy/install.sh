#!/usr/bin/env bash
# Installs or updates Project Hub as a systemd service (Debian / Raspberry Pi OS).
# Safe to run again: it pulls the latest code, rebuilds and restarts the service.
#
#   sudo ./deploy/install.sh
#   sudo DES_FOLDER=/mnt/hdd ./deploy/install.sh   # checkout + data on another disk
#
# See deploy/README.md for all settings.
set -euo pipefail

source "$(dirname -- "$(realpath -- "$0")")/common.sh"

show_help() {
  echo -e "${BOLD}${COLOR_BLUE}Project Hub - Install / Update${COLOR_RESET}"
  echo -e "Installs or updates Project Hub as a systemd service (Debian / Raspberry Pi OS)."
  echo -e "Run it again to update: pulls the code, rebuilds and restarts the service."
  echo -e ""
  echo -e "Usage: ${COLOR_GREEN}sudo [VAR=value ...] $0${COLOR_RESET} [OPTIONS]"
  echo -e "  e.g. ${COLOR_GREEN}sudo DES_FOLDER=/mnt/hdd $0${COLOR_RESET}"
  echo -e ""
  echo -e "${BOLD}Options:${COLOR_RESET}"
  echo -e "  ${COLOR_CYAN}-h, --help${COLOR_RESET}     Shows this help message and exits."
  echo -e ""
  help_settings DES_FOLDER TARGET_DIR DATA_DIR BRANCH REPO_URL APP_PORT BASE_PATH SERVICE_USER
  echo -e ""
  echo -e "Afterwards: ${COLOR_GREEN}sudo ./deploy/setup-nginx.sh${COLOR_RESET} (once) and ${COLOR_GREEN}sudo project-hub users add <name>${COLOR_RESET}"
  echo -e "Details: deploy/README.md"
}

parse_args "$@"
require_root
export DEBIAN_FRONTEND=noninteractive

# Node versions supported by Angular 20.
node_is_supported() {
  command -v node &> /dev/null || return 1
  node -e '
    const [maj, min] = process.versions.node.split(".").map(Number);
    const ok = (maj === 20 && min >= 19) || (maj === 22 && min >= 12) || maj >= 24;
    process.exit(ok ? 0 : 1);'
}

log_info "1. System dependencies"
apt-get update -q
PACKAGES=(git curl ca-certificates python3 python3-pip python3-venv)
MISSING=()
for pkg in "${PACKAGES[@]}"; do
  dpkg -s "$pkg" &> /dev/null || MISSING+=("$pkg")
done
if [ ${#MISSING[@]} -gt 0 ]; then
  log_info "Installing: ${MISSING[*]}"
  apt-get install -y -q "${MISSING[@]}"
fi

if ! node_is_supported; then
  log_info "Node $(node --version 2>/dev/null || echo 'not installed') is too old for Angular 20; installing Node 22 (NodeSource)..."
  # NodeSource's nodejs ships npm; Debian's separate npm package conflicts with it.
  apt-get remove -y -q npm &> /dev/null || true
  curl -fsSL https://deb.nodesource.com/setup_22.x | bash -
  apt-get install -y -q nodejs
  node_is_supported || die "Node $(node --version) is still not supported."
fi
log_success "python3 $(python3 --version | cut -d' ' -f2), node $(node --version)"

log_info "2. Service user"
if ! id "$SERVICE_USER" &> /dev/null; then
  useradd --system --no-create-home --shell /usr/sbin/nologin "$SERVICE_USER"
  log_success "Created system user $SERVICE_USER"
fi

log_info "3. Code ($TARGET_DIR, branch $BRANCH)"
if [ ! -d "$TARGET_DIR/.git" ]; then
  mkdir -p "$(dirname -- "$TARGET_DIR")"
  git clone --branch "$BRANCH" "$REPO_URL" "$TARGET_DIR"
else
  git -C "$TARGET_DIR" fetch --quiet origin "$BRANCH"
  git -C "$TARGET_DIR" checkout --quiet "$BRANCH"
  # Refuses to overwrite local edits instead of silently merging them.
  git -C "$TARGET_DIR" merge --ff-only "origin/$BRANCH" \
    || die "Local changes in $TARGET_DIR block the update; check 'git -C $TARGET_DIR status'."
fi
log_success "At $(git -C "$TARGET_DIR" log -1 --format='%h %s')"

log_info "4. Build (base href $BASE_PATH)"
PROJECT_HUB_BASE_HREF="$BASE_PATH" "$TARGET_DIR/build.sh"

log_info "5. Data ($DATA_DIR)"
# Older installs kept the data inside the checkout.
if [ -d "$TARGET_DIR/data" ] && [ ! -e "$DATA_DIR" ]; then
  log_info "Moving existing data from $TARGET_DIR/data"
  mv "$TARGET_DIR/data" "$DATA_DIR"
elif [ -d "$TARGET_DIR/data" ]; then
  log_warn "$TARGET_DIR/data exists but is no longer used (data is in $DATA_DIR)."
fi
mkdir -p "$DATA_DIR"
chown -R "$SERVICE_USER:$SERVICE_USER" "$DATA_DIR"
chmod 700 "$DATA_DIR"

log_info "6. systemd service"
if [ ! -f "$ENV_FILE" ]; then
  cat > "$ENV_FILE" <<CONF
# Extra settings for the project-hub service (read by systemd and the project-hub command).
# Public client URL used in device-login links; normally derived from the request.
#PROJECT_HUB_PUBLIC_URL=https://example.com/hub/
# Set to 1 when the site is served over HTTPS.
#PROJECT_HUB_COOKIE_SECURE=1
CONF
fi

cat > "/etc/systemd/system/$SERVICE_NAME.service" <<UNIT
[Unit]
Description=Project Hub server
After=network-online.target local-fs.target
Wants=network-online.target
# The data may be on an external disk: wait for it to be mounted.
RequiresMountsFor=$TARGET_DIR $DATA_DIR

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$TARGET_DIR/src
Environment=PROJECT_HUB_HOST=127.0.0.1
Environment=PROJECT_HUB_PORT=$APP_PORT
Environment=PROJECT_HUB_DATA_DIR=$DATA_DIR
Environment=PYTHONUNBUFFERED=1
Environment=PYTHONDONTWRITEBYTECODE=1
EnvironmentFile=-$ENV_FILE
ExecStart=$TARGET_DIR/.venv/bin/python -m server serve
Restart=on-failure
RestartSec=3

# Hardening: the code is read-only for the service; only the data folder is writable.
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=full
ReadWritePaths=$DATA_DIR

[Install]
WantedBy=multi-user.target
UNIT

# Admin command that runs the server CLI as the service user (so files keep the right owner).
cat > /usr/local/bin/project-hub <<CLI
#!/usr/bin/env bash
# Project Hub admin CLI, e.g.: sudo project-hub users add <name> | users list | tokens list
set -euo pipefail
[ "\$EUID" -eq 0 ] || { echo "Run with sudo." >&2; exit 1; }
[ \$# -gt 0 ] || set -- --help
set -a
[ -f "$ENV_FILE" ] && source "$ENV_FILE"
PROJECT_HUB_DATA_DIR="$DATA_DIR"
PYTHONDONTWRITEBYTECODE=1
set +a
cd "$TARGET_DIR/src"
# runuser keeps the environment (it is not a login shell).
exec runuser -u "$SERVICE_USER" -- "$TARGET_DIR/.venv/bin/python" -m server "\$@"
CLI
chmod 755 /usr/local/bin/project-hub

systemctl daemon-reload
systemctl enable --quiet "$SERVICE_NAME"
systemctl restart "$SERVICE_NAME"

log_info "7. Health check"
for _ in $(seq 30); do
  if curl -fs -o /dev/null "http://127.0.0.1:$APP_PORT/api/health"; then
    log_success "$SERVICE_NAME is running on 127.0.0.1:$APP_PORT"
    if [ ! -s "$DATA_DIR/auth.json" ]; then
      log_warn "No users yet. Create one with: sudo project-hub users add <username>"
    fi
    log_info "Logs: journalctl -u $SERVICE_NAME -f"
    exit 0
  fi
  sleep 1
done

log_error "$SERVICE_NAME did not become healthy. Recent logs:"
journalctl -u "$SERVICE_NAME" --no-pager -n 20
exit 1
