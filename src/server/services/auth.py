"""Multi-user authentication: passwords, session/API tokens and the device authorization flow."""

import hashlib
import hmac
import json
import os
import re
import secrets
import threading
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Literal, Optional

from .storage import DATA_DIR, write_json_atomic

DEFAULT_AUTH_FILE = DATA_DIR / "auth.json"

TOKEN_PREFIX = "phub_"
SESSION_TTL_SECONDS = 30 * 24 * 3600
# How often `last_used_at` is persisted, so every API call does not rewrite the file.
LAST_USED_WRITE_INTERVAL = 300

USERNAME_RE = re.compile(r"^[A-Za-z0-9._-]{1,32}$")
MIN_PASSWORD_LENGTH = 8

TokenKind = Literal["session", "api"]

# scrypt parameters (~16 MB memory, well under a typical 32 MB OpenSSL limit).
_SCRYPT_N, _SCRYPT_R, _SCRYPT_P = 2**14, 8, 1


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=_SCRYPT_N, r=_SCRYPT_R, p=_SCRYPT_P)
    return f"scrypt${_SCRYPT_N}${_SCRYPT_R}${_SCRYPT_P}${salt.hex()}${digest.hex()}"


def check_password(password: str, encoded: str) -> bool:
    try:
        algo, n, r, p, salt_hex, digest_hex = encoded.split("$")
        if algo != "scrypt":
            return False
        digest = hashlib.scrypt(
            password.encode(), salt=bytes.fromhex(salt_hex), n=int(n), r=int(r), p=int(p)
        )
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(digest.hex(), digest_hex)


# Checked against when the username does not exist, so timing does not reveal valid usernames.
_DUMMY_PASSWORD_HASH = hash_password(secrets.token_hex(16))


def _hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


class UserError(Exception):
    """Invalid user operation (duplicate or unknown username, invalid name...)."""


@dataclass
class UserRecord:
    id: str
    username: str
    password_hash: str = field(repr=False)
    created_at: float


@dataclass
class TokenRecord:
    id: str
    kind: TokenKind
    name: str
    hash: str
    created_at: float
    expires_at: Optional[float] = None
    last_used_at: Optional[float] = None
    user_id: str = ""

    def is_expired(self, now: float) -> bool:
        return self.expires_at is not None and now >= self.expires_at


def _new_user_id() -> str:
    return secrets.token_hex(8)


class AuthStore:
    """Persists the users and the issued tokens in a JSON file (only hashes are stored).

    Each token belongs to one user; removing a user revokes all of their tokens.
    """

    def __init__(self, path: Optional[Path] = None):
        self.path = Path(path or os.getenv("PROJECT_HUB_AUTH_FILE", str(DEFAULT_AUTH_FILE)))
        self._users: list[UserRecord] = []
        self._tokens: list[TokenRecord] = []
        self._mtime: Optional[float] = None
        self._lock = threading.RLock()

    # --- persistence ---

    def _current_mtime(self) -> Optional[float]:
        try:
            return self.path.stat().st_mtime
        except FileNotFoundError:
            return None

    def load(self):
        with self._lock:
            self._users, self._tokens = [], []
            self._mtime = self._current_mtime()
            if self._mtime is None or self.path.stat().st_size == 0:
                return
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._users = [UserRecord(**u) for u in data.get("users", [])]
            self._tokens = [TokenRecord(**t) for t in data.get("tokens", [])]
            if "user" in data and "users" not in data:
                self._migrate_single_user(data["user"])

    def _migrate_single_user(self, legacy: Optional[dict]):
        """Converts the old single-user format; existing tokens are kept and given to that user."""
        if legacy:
            user = UserRecord(
                id=_new_user_id(),
                username=legacy["username"],
                password_hash=legacy["password_hash"],
                created_at=time.time(),
            )
            self._users = [user]
            for t in self._tokens:
                t.user_id = user.id
        self._save()

    def _reload_if_changed(self):
        """Picks up edits made by the CLI (users, tokens revoke) while the server runs."""
        if self._current_mtime() != self._mtime:
            self.load()

    def _save(self):
        now = time.time()
        user_ids = {u.id for u in self._users}
        self._tokens = [t for t in self._tokens if not t.is_expired(now) and t.user_id in user_ids]
        data = {
            "users": [asdict(u) for u in self._users],
            "tokens": [asdict(t) for t in self._tokens],
        }
        write_json_atomic(self.path, data, mode=0o600)
        self._mtime = self._current_mtime()

    # --- users ---

    def _find(self, username: str) -> Optional[UserRecord]:
        wanted = username.casefold()
        return next((u for u in self._users if u.username.casefold() == wanted), None)

    def has_users(self) -> bool:
        with self._lock:
            self._reload_if_changed()
            return bool(self._users)

    def list_users(self) -> list[UserRecord]:
        with self._lock:
            self._reload_if_changed()
            return sorted(self._users, key=lambda u: u.created_at)

    def get_user(self, user_id: str) -> Optional[UserRecord]:
        with self._lock:
            self._reload_if_changed()
            return next((u for u in self._users if u.id == user_id), None)

    def find_user(self, username: str) -> Optional[UserRecord]:
        with self._lock:
            self._reload_if_changed()
            return self._find(username)

    @staticmethod
    def validate_username(username: str):
        if not USERNAME_RE.match(username):
            raise UserError("Username must be 1-32 characters: letters, digits, '.', '_' or '-'.")

    @staticmethod
    def validate_password(password: str):
        if len(password) < MIN_PASSWORD_LENGTH:
            raise UserError(f"Password must have at least {MIN_PASSWORD_LENGTH} characters.")

    def add_user(self, username: str, password: str) -> UserRecord:
        self.validate_username(username)
        self.validate_password(password)
        password_hash = hash_password(password)
        with self._lock:
            self._reload_if_changed()
            if self._find(username):
                raise UserError(f"User '{username}' already exists.")
            user = UserRecord(
                id=_new_user_id(), username=username, password_hash=password_hash, created_at=time.time()
            )
            self._users.append(user)
            self._save()
            return user

    def set_password(self, username: str, password: str) -> UserRecord:
        """Changes a user's password and revokes their browser sessions (API tokens are kept)."""
        self.validate_password(password)
        password_hash = hash_password(password)
        with self._lock:
            self._reload_if_changed()
            user = self._find(username)
            if not user:
                raise UserError(f"No user named '{username}'.")
            user.password_hash = password_hash
            self._tokens = [t for t in self._tokens if not (t.user_id == user.id and t.kind == "session")]
            self._save()
            return user

    def remove_user(self, username: str) -> UserRecord:
        """Removes a user and revokes all of their tokens. Their data is handled by the caller."""
        with self._lock:
            self._reload_if_changed()
            user = self._find(username)
            if not user:
                raise UserError(f"No user named '{username}'.")
            self._users.remove(user)
            self._save()  # also drops the user's tokens
            return user

    def authenticate(self, username: str, password: str) -> Optional[UserRecord]:
        with self._lock:
            self._reload_if_changed()
            user = self._find(username)
        # Always run the hash so timing does not reveal whether the username exists.
        password_ok = check_password(password, user.password_hash if user else _DUMMY_PASSWORD_HASH)
        return user if user and password_ok else None

    # --- tokens ---

    def issue_token(
        self, user_id: str, kind: TokenKind, name: str, ttl: Optional[float] = None
    ) -> tuple[str, TokenRecord]:
        """Returns (raw_token, record). The raw token is only available here."""
        raw = TOKEN_PREFIX + secrets.token_urlsafe(32)
        now = time.time()
        record = TokenRecord(
            id=secrets.token_hex(4),
            kind=kind,
            name=name,
            hash=_hash_token(raw),
            created_at=now,
            expires_at=now + ttl if ttl else None,
            user_id=user_id,
        )
        with self._lock:
            self._reload_if_changed()
            if not any(u.id == user_id for u in self._users):
                raise UserError("Unknown user.")
            self._tokens.append(record)
            self._save()
        return raw, record

    def resolve_token(self, raw: Optional[str]) -> Optional[tuple[UserRecord, TokenRecord]]:
        """Returns the owner and the record of a valid token, or None."""
        if not raw or not raw.startswith(TOKEN_PREFIX):
            return None
        digest = _hash_token(raw)
        now = time.time()
        with self._lock:
            self._reload_if_changed()
            for t in self._tokens:
                if hmac.compare_digest(t.hash, digest):
                    user = next((u for u in self._users if u.id == t.user_id), None)
                    if user is None or t.is_expired(now):
                        return None
                    if t.last_used_at is None or now - t.last_used_at > LAST_USED_WRITE_INTERVAL:
                        t.last_used_at = now
                        try:
                            self._save()
                        except OSError:
                            pass  # bookkeeping only; never fail a request because of it
                    return user, t
        return None

    def revoke(self, token_id: str) -> bool:
        with self._lock:
            self._reload_if_changed()
            before = len(self._tokens)
            self._tokens = [t for t in self._tokens if t.id != token_id]
            if len(self._tokens) == before:
                return False
            self._save()
            return True

    def list_tokens(self) -> list[TokenRecord]:
        with self._lock:
            self._reload_if_changed()
            now = time.time()
            return [t for t in self._tokens if not t.is_expired(now)]


# --- Device authorization flow (RFC 8628 style) ---

DEVICE_CODE_TTL = 600
DEVICE_POLL_INTERVAL = 5
# Unambiguous characters (no 0/O, 1/I/L...) for the code the user compares in the browser.
_USER_CODE_ALPHABET = "BCDFGHJKMNPQRSTVWXZ23456789"


class DeviceFlowError(Exception):
    """`code` is one of the RFC 8628 error codes (authorization_pending, slow_down, ...)."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


@dataclass
class DeviceRequest:
    device_code: str
    user_code: str
    client_name: str
    expires_at: float
    status: Literal["pending", "approved", "denied"] = "pending"
    last_poll_at: float = 0.0
    interval: int = DEVICE_POLL_INTERVAL
    access_token: Optional[str] = field(default=None, repr=False)


def normalize_user_code(code: str) -> str:
    return "".join(c for c in code.upper() if c.isalnum())


class DeviceFlow:
    """Pending device requests live in memory only; losing them on restart just means retrying."""

    def __init__(self, store: AuthStore):
        self.store = store
        self._requests: dict[str, DeviceRequest] = {}  # by device_code
        self._lock = threading.Lock()

    def _purge(self, now: float):
        for code in [c for c, r in self._requests.items() if now >= r.expires_at]:
            del self._requests[code]

    def _find_by_user_code(self, user_code: str) -> Optional[DeviceRequest]:
        wanted = normalize_user_code(user_code)
        for r in self._requests.values():
            if hmac.compare_digest(normalize_user_code(r.user_code), wanted):
                return r
        return None

    def start(self, client_name: str) -> DeviceRequest:
        now = time.time()
        with self._lock:
            self._purge(now)
            while True:
                chars = "".join(secrets.choice(_USER_CODE_ALPHABET) for _ in range(8))
                user_code = f"{chars[:4]}-{chars[4:]}"
                if not self._find_by_user_code(user_code):
                    break
            req = DeviceRequest(
                device_code=secrets.token_urlsafe(32),
                user_code=user_code,
                client_name=client_name,
                expires_at=now + DEVICE_CODE_TTL,
            )
            self._requests[req.device_code] = req
            return req

    def lookup(self, user_code: str) -> Optional[DeviceRequest]:
        """Returns the pending request for a user code, if any."""
        with self._lock:
            self._purge(time.time())
            req = self._find_by_user_code(user_code)
            return req if req and req.status == "pending" else None

    def decide(self, user_code: str, approve: bool, user_id: str) -> DeviceRequest:
        """Approving issues an API token owned by `user_id` (the user who approved in the browser)."""
        with self._lock:
            self._purge(time.time())
            req = self._find_by_user_code(user_code)
            if not req or req.status != "pending":
                raise DeviceFlowError("invalid_user_code")
            if approve:
                raw, _ = self.store.issue_token(user_id, "api", req.client_name)
                req.access_token = raw
                req.status = "approved"
            else:
                req.status = "denied"
            return req

    def poll(self, device_code: str) -> str:
        """Returns the access token once approved; raises DeviceFlowError otherwise."""
        now = time.time()
        with self._lock:
            req = self._requests.get(device_code)
            if not req:
                raise DeviceFlowError("expired_token")
            if now >= req.expires_at:
                del self._requests[device_code]
                raise DeviceFlowError("expired_token")
            if req.status == "denied":
                del self._requests[device_code]
                raise DeviceFlowError("access_denied")
            if req.status == "approved":
                del self._requests[device_code]  # the token is handed out exactly once
                return req.access_token  # type: ignore[return-value]
            too_fast = now - req.last_poll_at < req.interval
            req.last_poll_at = now
            if too_fast:
                req.interval += 5
                raise DeviceFlowError("slow_down")
            raise DeviceFlowError("authorization_pending")


# --- Login rate limiting ---

class LoginThrottle:
    """Per client: after MAX_FAILURES consecutive failures, logins are refused for LOCKOUT_SECONDS."""

    MAX_FAILURES = 5
    LOCKOUT_SECONDS = 60

    def __init__(self):
        self._failures: dict[str, int] = {}
        self._locked_until: dict[str, float] = {}
        self._lock = threading.Lock()

    def retry_after(self, client: str) -> int:
        remaining = self._locked_until.get(client, 0.0) - time.time()
        return max(0, int(remaining + 0.999))

    def record_failure(self, client: str):
        with self._lock:
            self._failures[client] = self._failures.get(client, 0) + 1
            if self._failures[client] >= self.MAX_FAILURES:
                del self._failures[client]
                self._locked_until[client] = time.time() + self.LOCKOUT_SECONDS

    def record_success(self, client: str):
        with self._lock:
            self._failures.pop(client, None)
            self._locked_until.pop(client, None)
