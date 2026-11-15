"""Single-user authentication: password, session/API tokens and the device authorization flow."""

import hashlib
import hmac
import json
import os
import secrets
import threading
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Literal, Optional

from .storage import write_json_atomic

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_AUTH_FILE = PROJECT_ROOT / "data" / "auth.json"

TOKEN_PREFIX = "phub_"
SESSION_TTL_SECONDS = 30 * 24 * 3600
# How often `last_used_at` is persisted, so every API call does not rewrite the file.
LAST_USED_WRITE_INTERVAL = 300

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


def _hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


@dataclass
class TokenRecord:
    id: str
    kind: TokenKind
    name: str
    hash: str
    created_at: float
    expires_at: Optional[float] = None
    last_used_at: Optional[float] = None

    def is_expired(self, now: float) -> bool:
        return self.expires_at is not None and now >= self.expires_at


class AuthStore:
    """Persists the single user and the issued tokens in a JSON file (only token hashes are stored)."""

    def __init__(self, path: Optional[Path] = None):
        self.path = Path(path or os.getenv("PROJECT_HUB_AUTH_FILE", str(DEFAULT_AUTH_FILE)))
        self._user: Optional[dict] = None
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
            self._user, self._tokens = None, []
            self._mtime = self._current_mtime()
            if self._mtime is None or self.path.stat().st_size == 0:
                return
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._user = data.get("user")
            self._tokens = [TokenRecord(**t) for t in data.get("tokens", [])]

    def _reload_if_changed(self):
        """Picks up edits made by the CLI (create-user, tokens revoke) while the server runs."""
        if self._current_mtime() != self._mtime:
            self.load()

    def _save(self):
        now = time.time()
        self._tokens = [t for t in self._tokens if not t.is_expired(now)]
        data = {"user": self._user, "tokens": [asdict(t) for t in self._tokens]}
        write_json_atomic(self.path, data, mode=0o600)
        self._mtime = self._current_mtime()

    # --- user ---

    def has_user(self) -> bool:
        with self._lock:
            self._reload_if_changed()
            return self._user is not None

    @property
    def username(self) -> Optional[str]:
        return self._user["username"] if self._user else None

    def set_user(self, username: str, password: str):
        """Creates or replaces the single user. Existing sessions are revoked; API tokens are kept."""
        with self._lock:
            self._reload_if_changed()
            self._user = {"username": username, "password_hash": hash_password(password)}
            self._tokens = [t for t in self._tokens if t.kind != "session"]
            self._save()

    def verify_password(self, username: str, password: str) -> bool:
        with self._lock:
            self._reload_if_changed()
            user = self._user
        if not user:
            return False
        # Always run the hash so timing does not reveal whether the username matched.
        password_ok = check_password(password, user["password_hash"])
        return hmac.compare_digest(username.encode(), user["username"].encode()) and password_ok

    # --- tokens ---

    def issue_token(self, kind: TokenKind, name: str, ttl: Optional[float] = None) -> tuple[str, TokenRecord]:
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
        )
        with self._lock:
            self._reload_if_changed()
            self._tokens.append(record)
            self._save()
        return raw, record

    def resolve_token(self, raw: Optional[str]) -> Optional[TokenRecord]:
        if not raw or not raw.startswith(TOKEN_PREFIX):
            return None
        digest = _hash_token(raw)
        now = time.time()
        with self._lock:
            self._reload_if_changed()
            for t in self._tokens:
                if hmac.compare_digest(t.hash, digest):
                    if t.is_expired(now):
                        return None
                    if t.last_used_at is None or now - t.last_used_at > LAST_USED_WRITE_INTERVAL:
                        t.last_used_at = now
                        try:
                            self._save()
                        except OSError:
                            pass  # bookkeeping only; never fail a request because of it
                    return t
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

    def decide(self, user_code: str, approve: bool) -> DeviceRequest:
        with self._lock:
            self._purge(time.time())
            req = self._find_by_user_code(user_code)
            if not req or req.status != "pending":
                raise DeviceFlowError("invalid_user_code")
            if approve:
                raw, _ = self.store.issue_token("api", req.client_name)
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
