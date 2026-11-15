#!/usr/bin/env python3
"""Minimal Project Hub API client (stdlib only).

    python examples/project_hub_client.py login      # browser-based device login, saves the token
    python examples/project_hub_client.py projects   # list projects using the saved token
    python examples/project_hub_client.py logout     # delete the saved token

The server URL comes from --url or PROJECT_HUB_URL (default http://localhost:9998/).
The token can also be passed via PROJECT_HUB_TOKEN instead of the saved file.
"""

import argparse
import json
import os
import socket
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path

TOKEN_FILE = Path(os.getenv("XDG_CONFIG_HOME", Path.home() / ".config")) / "project-hub" / "token"


class ApiError(Exception):
    def __init__(self, status: int, body: dict):
        super().__init__(f"HTTP {status}: {body}")
        self.status = status
        self.body = body


def request(base_url: str, method: str, path: str, body=None, token: str | None = None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(base_url.rstrip("/") + path, data=data, method=method)
    req.add_header("Accept", "application/json")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read()
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        try:
            payload = json.loads(e.read() or b"{}")
        except ValueError:
            payload = {}
        raise ApiError(e.code, payload) from None


def device_login(base_url: str) -> str:
    """Runs the device authorization flow and returns the access token."""
    client_name = f"project_hub_client.py on {socket.gethostname()}"
    start = request(base_url, "POST", "/api/auth/device/code", {"client_name": client_name})

    print(f"\nOpen this URL in your browser and approve the request:\n\n  {start['verification_uri_complete']}\n", flush=True)
    print(f"Confirm the code shown matches: {start['user_code']}\n", flush=True)
    try:
        webbrowser.open(start["verification_uri_complete"])
    except Exception:
        pass

    interval = start["interval"]
    deadline = time.time() + start["expires_in"]
    while time.time() < deadline:
        time.sleep(interval)
        try:
            return request(base_url, "POST", "/api/auth/device/token", {"device_code": start["device_code"]})["access_token"]
        except ApiError as e:
            error = e.body.get("error")
            if error == "authorization_pending":
                continue
            if error == "slow_down":
                interval += 5
                continue
            if error == "access_denied":
                sys.exit("❌ Access denied in the browser.")
            if error == "expired_token":
                break
            raise
    sys.exit("❌ The code expired. Run login again.")


def save_token(token: str):
    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(TOKEN_FILE, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        f.write(token)


def load_token() -> str:
    token = os.getenv("PROJECT_HUB_TOKEN")
    if token:
        return token
    if TOKEN_FILE.exists():
        return TOKEN_FILE.read_text().strip()
    sys.exit("Not logged in. Run: python examples/project_hub_client.py login")


def get_projects(base_url: str, token: str) -> list[dict]:
    return request(base_url, "GET", "/api/projects", token=token)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--url", default=os.getenv("PROJECT_HUB_URL", "http://localhost:9998/"))
    parser.add_argument("command", choices=["login", "projects", "logout"])
    args = parser.parse_args()

    if args.command == "login":
        token = device_login(args.url)
        save_token(token)
        print(f"✅ Logged in. Token saved to {TOKEN_FILE}")
    elif args.command == "logout":
        TOKEN_FILE.unlink(missing_ok=True)
        print("Token removed locally. Revoke it on the server with: python -m server tokens revoke <id>")
    else:
        try:
            projects = get_projects(args.url, load_token())
        except ApiError as e:
            if e.status == 401:
                sys.exit("❌ Token invalid or revoked. Run login again.")
            raise
        for p in projects:
            tasks = sum(len(c["tasks"]) for c in p["columns"])
            print(f"- {p['name']} [{p['status']}] ({tasks} tasks)")


if __name__ == "__main__":
    main()
