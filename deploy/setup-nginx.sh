#!/usr/bin/env bash
# Publishes Project Hub through nginx under $BASE_PATH (default /hub/) without touching other proxies.
#
# The location block lives in its own snippet (/etc/nginx/snippets/project-hub.conf), which is
# included in an existing server block ($NGINX_SITE, default sites-available/proxies.conf).
# If that site does not exist yet, a minimal one listening on port 80 is created.
# Any change is validated with `nginx -t` and rolled back if it fails.
#
#   sudo ./deploy/setup-nginx.sh
#   sudo NGINX_SITE=/etc/nginx/sites-available/mysite ./deploy/setup-nginx.sh
set -euo pipefail

source "$(dirname -- "$(realpath -- "$0")")/common.sh"

NGINX_SITE=${NGINX_SITE:-/etc/nginx/sites-available/proxies.conf}

show_help() {
  echo -e "${BOLD}${COLOR_BLUE}Project Hub - nginx setup${COLOR_RESET}"
  echo -e "Publishes Project Hub under BASE_PATH without touching other proxies: writes"
  echo -e "/etc/nginx/snippets/project-hub.conf and includes it in the NGINX_SITE server block"
  echo -e "(created on port 80 if missing). Rolled back if 'nginx -t' fails."
  echo -e ""
  echo -e "Usage: ${COLOR_GREEN}sudo [VAR=value ...] $0${COLOR_RESET} [OPTIONS]"
  echo -e ""
  echo -e "${BOLD}Options:${COLOR_RESET}"
  echo -e "  ${COLOR_CYAN}-h, --help${COLOR_RESET}     Shows this help message and exits."
  echo -e ""
  help_settings NGINX_SITE BASE_PATH APP_PORT
  echo -e ""
  echo -e "Details: deploy/README.md"
}

parse_args "$@"
require_root
export DEBIAN_FRONTEND=noninteractive

SNIPPET=/etc/nginx/snippets/project-hub.conf
INCLUDE_LINE="include snippets/project-hub.conf;"
PREFIX=${BASE_PATH%/}   # "/hub"

[[ "$BASE_PATH" == /*/ ]] || die "BASE_PATH must start and end with '/' (got '$BASE_PATH')."

if ! command -v nginx &> /dev/null; then
  log_info "Installing nginx..."
  apt-get update -q
  apt-get install -y -q nginx
fi

BACKUP_DIR=$(mktemp -d)
backup() { [ -e "$1" ] && cp -a "$1" "$BACKUP_DIR/$(basename -- "$1")" || true; }
rollback() {
  log_error "nginx rejected the configuration; restoring the previous files."
  for f in "$SNIPPET" "$NGINX_SITE"; do
    if [ -e "$BACKUP_DIR/$(basename -- "$f")" ]; then
      cp -a "$BACKUP_DIR/$(basename -- "$f")" "$f"
    else
      rm -f "$f"
    fi
  done
  nginx -t || true
  exit 1
}
backup "$SNIPPET"
backup "$NGINX_SITE"

log_info "Writing $SNIPPET"
mkdir -p "$(dirname -- "$SNIPPET")"
cat > "$SNIPPET" <<CONF
# Project Hub (managed by project-hub/deploy/setup-nginx.sh)
location = $PREFIX {
    return 301 $BASE_PATH;
}

location $BASE_PATH {
    proxy_pass http://127.0.0.1:$APP_PORT/;
    proxy_http_version 1.1;
    proxy_set_header Host \$http_host;  # keeps the port, if any
    proxy_set_header X-Real-IP \$remote_addr;
    proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto \$scheme;
    # Lets the server build correct links (device login) for the sub-path.
    proxy_set_header X-Forwarded-Prefix $PREFIX;
    client_max_body_size 10m;
}
CONF

if [ ! -f "$NGINX_SITE" ]; then
  log_info "Creating $NGINX_SITE"
  cat > "$NGINX_SITE" <<CONF
server {
    listen 80;
    server_name _;

    $INCLUDE_LINE
}
CONF
  if [ -e /etc/nginx/sites-enabled/default ]; then
    # The stock site also listens on port 80 and would answer instead of this one.
    log_warn "Disabling the stock 'default' site (still available in sites-available)."
    rm -f /etc/nginx/sites-enabled/default
  fi
elif ! grep -qF "$INCLUDE_LINE" "$NGINX_SITE"; then
  # Older versions of this setup wrote the location block inline: drop it to avoid duplicates.
  if grep -qE "^\s*location\s+$BASE_PATH\s*\{" "$NGINX_SITE"; then
    log_info "Removing the inline 'location $BASE_PATH' block from $NGINX_SITE"
    awk -v loc="$BASE_PATH" '
      !skip && $1 == "location" && $2 == loc { skip = 1; depth = 0 }
      skip {
        depth += gsub(/\{/, "{") - gsub(/\}/, "}")
        if (depth <= 0 && /\}/) skip = 0
        next
      }
      { print }
    ' "$NGINX_SITE" > "$NGINX_SITE.tmp" && mv "$NGINX_SITE.tmp" "$NGINX_SITE"
  fi
  grep -qE '^\s*server_name\s' "$NGINX_SITE" \
    || die "No 'server_name' in $NGINX_SITE; add '$INCLUDE_LINE' to its server block by hand."
  log_info "Including the snippet in $NGINX_SITE"
  # Right after the first server_name line, i.e. inside the first server block.
  sed -i "0,/^\s*server_name\s.*;/s|^\(\s*\)server_name\s.*;|&\n\n\1$INCLUDE_LINE|" "$NGINX_SITE"
else
  log_success "$NGINX_SITE already includes the snippet."
fi

ln -sf "$NGINX_SITE" "/etc/nginx/sites-enabled/$(basename -- "$NGINX_SITE")"

nginx -t || rollback
systemctl enable --quiet nginx
systemctl reload nginx 2> /dev/null || systemctl restart nginx
rm -rf "$BACKUP_DIR"
log_success "Project Hub is published at http://$(hostname)$BASE_PATH"
