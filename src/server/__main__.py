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


def _store():
    from .services.auth import AuthStore

    store = AuthStore()
    store.load()
    return store


def _ask_password() -> str:
    password = getpass.getpass("Password: ")
    if getpass.getpass("Confirm password: ") != password:
        sys.exit("Passwords do not match.")
    return password


def cmd_users_add(args):
    from .services.auth import UserError
    from .services.database import DatabaseRegistry

    store = _store()
    username = args.username or input("Username: ").strip()
    try:
        store.validate_username(username)
        if store.find_user(username):
            raise UserError(f"User '{username}' already exists.")
        first_user = not store.has_users()
        user = store.add_user(username, _ask_password())
    except UserError as e:
        sys.exit(str(e))
    print(f"✅ User '{user.username}' created.")
    if first_user and DatabaseRegistry().adopt_legacy_data(user.id):
        print("   Existing projects were moved into this user's data folder.")


def cmd_users_list(_args):
    from .services.database import DatabaseRegistry

    store = _store()
    users = store.list_users()
    if not users:
        print("No users.")
        return
    registry = DatabaseRegistry()
    print(f"{'USERNAME':<20}{'ID':<18}{'CREATED':<18}DATA")
    for u in users:
        print(f"{u.username:<20}{u.id:<18}{_fmt_time(u.created_at):<18}{registry.user_dir(u.id)}")


def cmd_users_passwd(args):
    from .services.auth import UserError

    store = _store()
    if not store.find_user(args.username):
        sys.exit(f"No user named '{args.username}'.")
    try:
        user = store.set_password(args.username, _ask_password())
    except UserError as e:
        sys.exit(str(e))
    print(f"✅ Password of '{user.username}' changed; their browser sessions were signed out.")


def cmd_users_remove(args):
    from .services.auth import UserError
    from .services.database import DatabaseRegistry

    store = _store()
    user = store.find_user(args.username)
    if not user:
        sys.exit(f"No user named '{args.username}'.")
    if not args.yes:
        answer = input(f"Remove user '{user.username}' and revoke all their tokens? [y/N] ")
        if answer.strip().lower() != "y":
            sys.exit("Aborted.")
    try:
        store.remove_user(user.username)
    except UserError as e:
        sys.exit(str(e))
    trashed = DatabaseRegistry().trash(user.id)
    print(f"✅ User '{user.username}' removed.")
    if trashed:
        print(f"   Their data was moved to {trashed}")


def cmd_tokens_list(_args):
    store = _store()
    tokens = store.list_tokens()
    if not tokens:
        print("No tokens.")
        return
    usernames = {u.id: u.username for u in store.list_users()}
    print(f"{'ID':<10}{'USER':<20}{'KIND':<9}{'CREATED':<18}{'LAST USED':<18}NAME")
    for t in tokens:
        user = usernames.get(t.user_id, "?")
        print(
            f"{t.id:<10}{user:<20}{t.kind:<9}{_fmt_time(t.created_at):<18}"
            f"{_fmt_time(t.last_used_at):<18}{t.name}"
        )


def cmd_tokens_revoke(args):
    store = _store()
    if not store.revoke(args.id):
        sys.exit(f"No token with id '{args.id}'.")
    print(f"✅ Token '{args.id}' revoked.")


def main():
    parser = argparse.ArgumentParser(prog="python -m server", description="Project Hub server")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("serve", help="run the HTTP server (default)").set_defaults(func=cmd_serve)

    p_users = sub.add_parser("users", help="manage users")
    users_sub = p_users.add_subparsers(dest="users_command", required=True)
    p_add = users_sub.add_parser("add", help="create a user")
    p_add.add_argument("username", nargs="?")
    p_add.set_defaults(func=cmd_users_add)
    users_sub.add_parser("list", help="list users").set_defaults(func=cmd_users_list)
    p_passwd = users_sub.add_parser("passwd", help="change a user's password")
    p_passwd.add_argument("username")
    p_passwd.set_defaults(func=cmd_users_passwd)
    p_remove = users_sub.add_parser("remove", help="remove a user (their data goes to data/deleted/)")
    p_remove.add_argument("username")
    p_remove.add_argument("-y", "--yes", action="store_true", help="do not ask for confirmation")
    p_remove.set_defaults(func=cmd_users_remove)

    # Kept for compatibility with the single-user setup instructions.
    p_create = sub.add_parser("create-user", help="alias of `users add`")
    p_create.add_argument("--username")
    p_create.set_defaults(func=cmd_users_add)

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
