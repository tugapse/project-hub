import argparse
import getpass
import os
import sys
from datetime import datetime


def _fmt_time(ts):
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M") if ts else "-"


def cmd_serve(_args):
    import uvicorn

    from .main import app

    host = os.getenv("PROJECT_HUB_HOST", "0.0.0.0")
    port = int(os.getenv("PROJECT_HUB_PORT", 9998))
    uvicorn.run(app, host=host, port=port)


def cmd_create_user(args):
    from .services.auth import AuthStore

    store = AuthStore()
    store.load()
    username = args.username or input("Username: ").strip()
    if not username:
        sys.exit("Username cannot be empty.")
    if store.has_user():
        answer = input(f"A user ('{store.username}') already exists. Replace it? [y/N] ")
        if answer.strip().lower() != "y":
            sys.exit("Aborted.")
    password = getpass.getpass("Password: ")
    if len(password) < 8:
        sys.exit("Password must have at least 8 characters.")
    if getpass.getpass("Confirm password: ") != password:
        sys.exit("Passwords do not match.")
    store.set_user(username, password)
    print(f"✅ User '{username}' saved to {store.path}.")


def cmd_tokens_list(_args):
    from .services.auth import AuthStore

    store = AuthStore()
    store.load()
    tokens = store.list_tokens()
    if not tokens:
        print("No tokens.")
        return
    print(f"{'ID':<10}{'KIND':<9}{'CREATED':<18}{'LAST USED':<18}NAME")
    for t in tokens:
        print(f"{t.id:<10}{t.kind:<9}{_fmt_time(t.created_at):<18}{_fmt_time(t.last_used_at):<18}{t.name}")


def cmd_tokens_revoke(args):
    from .services.auth import AuthStore

    store = AuthStore()
    store.load()
    if not store.revoke(args.id):
        sys.exit(f"No token with id '{args.id}'.")
    print(f"✅ Token '{args.id}' revoked.")


def main():
    parser = argparse.ArgumentParser(prog="python -m server", description="Project Hub server")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("serve", help="run the HTTP server (default)").set_defaults(func=cmd_serve)

    p_user = sub.add_parser("create-user", help="create or replace the login user")
    p_user.add_argument("--username")
    p_user.set_defaults(func=cmd_create_user)

    p_tokens = sub.add_parser("tokens", help="manage API tokens and sessions")
    tokens_sub = p_tokens.add_subparsers(dest="tokens_command", required=True)
    tokens_sub.add_parser("list", help="list active tokens").set_defaults(func=cmd_tokens_list)
    p_revoke = tokens_sub.add_parser("revoke", help="revoke a token by id")
    p_revoke.add_argument("id")
    p_revoke.set_defaults(func=cmd_tokens_revoke)

    args = parser.parse_args()
    getattr(args, "func", cmd_serve)(args)


if __name__ == "__main__":
    main()
