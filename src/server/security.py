"""FastAPI dependencies that authenticate requests via Bearer token or session cookie."""

import os
from typing import Optional

from fastapi import Depends, HTTPException, Request, status

from .services.auth import AuthStore, TokenRecord

SESSION_COOKIE = "ph_session"
COOKIE_SECURE = os.getenv("PROJECT_HUB_COOKIE_SECURE", "0").lower() in ("1", "true", "yes")

auth_store = AuthStore()


def extract_token(request: Request) -> Optional[str]:
    header = request.headers.get("Authorization", "")
    scheme, _, value = header.partition(" ")
    if scheme.lower() == "bearer" and value:
        return value.strip()
    return request.cookies.get(SESSION_COOKIE)


def require_auth(request: Request) -> TokenRecord:
    record = auth_store.resolve_token(extract_token(request))
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return record


def require_session(record: TokenRecord = Depends(require_auth)) -> TokenRecord:
    """Only a logged-in browser session (not an API token) may approve new devices."""
    if record.kind != "session":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Browser session required")
    return record
