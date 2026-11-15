import logging
import mimetypes
import os
import time
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from .entities.dto import (
    DeviceApproveRequest,
    DeviceCodeRequest,
    DeviceCodeResponse,
    DeviceInfoResponse,
    DeviceTokenRequest,
    DeviceTokenResponse,
    LoginRequest,
    MeResponse,
    Project,
)
from .security import (
    COOKIE_SECURE,
    SESSION_COOKIE,
    auth_store,
    extract_token,
    require_auth,
    require_session,
)
from .services.auth import (
    DEVICE_CODE_TTL,
    SESSION_TTL_SECONDS,
    DeviceFlow,
    DeviceFlowError,
    LoginThrottle,
    TokenRecord,
)
from .services.database import DatabaseError, ProjectsDatabase

logger = logging.getLogger("project_hub")

# Some systems (e.g. Windows registry, minimal containers) map these wrongly,
# which breaks loading the Angular bundle as ES modules.
mimetypes.add_type("text/javascript", ".js")
mimetypes.add_type("text/css", ".css")
mimetypes.add_type("image/svg+xml", ".svg")

FRONTEND_BUILD_DIR = Path(__file__).resolve().parents[2] / "dist"
# Public base URL of the client (e.g. "https://example.com/hub/"); used in device-flow links.
PUBLIC_URL = os.getenv("PROJECT_HUB_PUBLIC_URL")

app = FastAPI(title="Project Hub")

database = ProjectsDatabase()
database.load_from_disk()

auth_store.load()
if not auth_store.has_user():
    logger.warning("No user configured: run `python -m server create-user` to enable login.")
device_flow = DeviceFlow(auth_store)
login_throttle = LoginThrottle()


# --- Public ---

public = APIRouter(prefix="/api")


@public.get("/health")
def health():
    return {"status": "ok"}


# --- Auth ---

auth = APIRouter(prefix="/api/auth")


@auth.post("/login", response_model=MeResponse)
def login(body: LoginRequest, request: Request, response: Response):
    client = request.client.host if request.client else "unknown"
    retry_after = login_throttle.retry_after(client)
    if retry_after:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many failed attempts. Try again in {retry_after}s.",
            headers={"Retry-After": str(retry_after)},
        )
    if not auth_store.has_user():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No user configured. Run `python -m server create-user` on the server.",
        )
    if not auth_store.verify_password(body.username, body.password):
        login_throttle.record_failure(client)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")

    login_throttle.record_success(client)
    user_agent = request.headers.get("User-Agent", "browser")[:100]
    raw, _ = auth_store.issue_token("session", user_agent, ttl=SESSION_TTL_SECONDS)
    response.set_cookie(
        SESSION_COOKIE,
        raw,
        max_age=SESSION_TTL_SECONDS,
        httponly=True,
        samesite="lax",
        secure=COOKIE_SECURE,
        path="/",
    )
    return MeResponse(username=auth_store.username or body.username, token_kind="session")


@auth.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request: Request, response: Response):
    record = auth_store.resolve_token(extract_token(request))
    if record and record.kind == "session":
        auth_store.revoke(record.id)
    response.delete_cookie(SESSION_COOKIE, path="/", httponly=True, samesite="lax", secure=COOKIE_SECURE)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@auth.get("/me", response_model=MeResponse)
def me(record: TokenRecord = Depends(require_auth)):
    return MeResponse(username=auth_store.username or "", token_kind=record.kind)


def _client_base_url(request: Request) -> str:
    base = PUBLIC_URL or str(request.base_url)
    return base if base.endswith("/") else base + "/"


@auth.post("/device/code", response_model=DeviceCodeResponse)
def device_code(body: DeviceCodeRequest, request: Request):
    req = device_flow.start(body.client_name.strip() or "API client")
    base = _client_base_url(request)
    return DeviceCodeResponse(
        device_code=req.device_code,
        user_code=req.user_code,
        verification_uri=base,
        verification_uri_complete=f"{base}?user_code={req.user_code}",
        expires_in=DEVICE_CODE_TTL,
        interval=req.interval,
    )


@auth.post("/device/token", response_model=DeviceTokenResponse)
def device_token(body: DeviceTokenRequest):
    try:
        token = device_flow.poll(body.device_code)
    except DeviceFlowError as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"error": e.code})
    return DeviceTokenResponse(access_token=token)


@auth.get("/device/{user_code}", response_model=DeviceInfoResponse)
def device_info(user_code: str, _: TokenRecord = Depends(require_session)):
    req = device_flow.lookup(user_code)
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown or expired code")
    return DeviceInfoResponse(
        user_code=req.user_code,
        client_name=req.client_name,
        expires_in=max(0, int(req.expires_at - time.time())),
    )


@auth.post("/device/approve", status_code=status.HTTP_204_NO_CONTENT)
def device_approve(body: DeviceApproveRequest, _: TokenRecord = Depends(require_session)):
    try:
        device_flow.decide(body.user_code, body.approve)
    except DeviceFlowError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown or expired code")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --- Protected API ---

api = APIRouter(prefix="/api", dependencies=[Depends(require_auth)])


@api.get("/projects", response_model=List[Project])
def get_projects():
    return database.get_projects()


@api.post("/projects")
def update_projects(incoming_projects: List[Project]):
    try:
        database.save_to_disk(incoming_projects)
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    return {"status": "success", "count": len(database.get_projects())}


app.include_router(public)
app.include_router(auth)
app.include_router(api)

if FRONTEND_BUILD_DIR.is_dir():
    app.mount("/", StaticFiles(directory=FRONTEND_BUILD_DIR, html=True), name="static_app")
