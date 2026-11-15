"""FastAPI dependencies that authenticate requests via Bearer token or session cookie."""

import os
from dataclasses import dataclass
from typing import Optional

from fastapi import Depends, HTTPException, Request, status

from .services.auth import AuthStore, TokenRecord, UserRecord
from .services.database import DatabaseRegistry, ProjectsDatabase

SESSION_COOKIE = "ph_session"
COOKIE_SECURE = os.getenv("PROJECT_HUB_COOKIE_SECURE", "0").lower() in ("1", "true", "yes")

auth_store = AuthStore()
databases = DatabaseRegistry()


@dataclass(frozen=True)
class Principal:
    """The authenticated user and the token used for the request."""

    user: UserRecord
    token: TokenRecord


def extract_token(request: Request) -> Optional[str]:
    header = request.headers.get("Authorization", "")
    scheme, _, value = header.partition(" ")
    if scheme.lower() == "bearer" and value:
        return value.strip()
    return request.cookies.get(SESSION_COOKIE)


def require_auth(request: Request) -> Principal:
    resolved = auth_store.resolve_token(extract_token(request))
    if resolved is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return Principal(*resolved)


def require_session(principal: Principal = Depends(require_auth)) -> Principal:
    """Only a logged-in browser session (not an API token) may approve new devices."""
    if principal.token.kind != "session":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Browser session required")
    return principal


def user_database(principal: Principal = Depends(require_auth)) -> ProjectsDatabase:
    """The projects database of the authenticated user."""
    return databases.get(principal.user.id)
