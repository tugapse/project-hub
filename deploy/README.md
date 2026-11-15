# Deploy (Debian / Raspberry Pi OS)

Runs Project Hub as a systemd service behind nginx, at `http://<host>/hub/`.

```bash
git clone https://github.com/tugapse/project-hub && cd project-hub
sudo DES_FOLDER=/mnt/hdd ./deploy/install.sh   # code + data on the external disk
sudo ./deploy/setup-nginx.sh                   # publish under /hub/ (once)
sudo project-hub users add <username>          # first login account
```

To update later, run `install.sh` again with the same settings. It pulls the latest code, rebuilds and restarts the service.

## What `install.sh` does

1. Installs `git`, `curl`, `python3`, `python3-venv` and, if the installed Node is older than Angular 20 needs (≥ 20.19), Node 22 from NodeSource.
2. Creates the `project-hub` system user (no shell, no home).
3. Clones or fast-forwards the repo into `$TARGET_DIR`. It stops if there are local changes instead of merging them.
4. Runs `build.sh` with base href `/hub/`.
5. Creates the data folder next to the checkout, owned by `project-hub` with mode 700. Data from an older install in `<checkout>/data` is moved there.
6. Writes `/etc/systemd/system/project-hub.service`, `/etc/default/project-hub` (only if missing) and the `/usr/local/bin/project-hub` admin command.
7. Restarts the service and waits for `/api/health`.

The service listens on `127.0.0.1` only, so nginx is the only way in. It can write only to the data folder.

## What `setup-nginx.sh` does

It writes the `location /hub/` block to `/etc/nginx/snippets/project-hub.conf` and adds `include snippets/project-hub.conf;` to an existing server block. Other proxies in that file are left alone.

- If the site file doesn't exist, it creates a minimal server on port 80 and disables the stock `default` site.
- An inline `location /hub/` block written by older versions of this script is replaced by the include.
- Every change is checked with `nginx -t` and rolled back if nginx rejects it. nginx is then reloaded, not restarted.

## Settings (environment variables)

| Variable | Default | Used by |
| --- | --- | --- |
| `DES_FOLDER` | `/opt` | Parent folder of the checkout |
| `TARGET_DIR` | `$DES_FOLDER/project-hub` | Checkout |
| `DATA_DIR` | `<parent of TARGET_DIR>/project-hub-data` | `auth.json` + one folder per user |
| `BRANCH` | `master` | Branch that is deployed |
| `REPO_URL` | GitHub repo | |
| `APP_PORT` | `9998` | Local port of the service |
| `BASE_PATH` | `/hub/` | Path under nginx (build + proxy) |
| `NGINX_SITE` | `/etc/nginx/sites-available/proxies.conf` | Server block that gets the include |
| `SERVICE_USER` | `project-hub` | |

Use the same values every time you run the scripts. Extra server settings, such as `PROJECT_HUB_COOKIE_SECURE=1` behind HTTPS, go in `/etc/default/project-hub`.

## Day-to-day

```bash
sudo project-hub users add|list|passwd|remove <username>
sudo project-hub tokens list | tokens revoke <id>
systemctl status project-hub
journalctl -u project-hub -f
```

`project-hub` runs the server CLI as the service user, so the files it writes keep the right owner. Changes take effect without a restart.

**Backups:** copy `DATA_DIR`. It holds everything, including users removed with `users remove` (in `deleted/`).
