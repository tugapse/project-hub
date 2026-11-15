import time

from fastapi.testclient import TestClient

from server import main
from server.security import SESSION_COOKIE
from server.services import auth as auth_module

from .conftest import PASSWORD, USERNAME


def start_device(client, name="test-script"):
    r = client.post("/api/auth/device/code", json={"client_name": name})
    assert r.status_code == 200
    return r.json()


def anonymous():
    return TestClient(main.app)


def test_health_is_public(client):
    assert client.get("/api/health").status_code == 200


def test_projects_require_auth(client):
    assert client.get("/api/projects").status_code == 401
    assert client.post("/api/projects", json=[]).status_code == 401


def test_wrong_password_is_rejected(client):
    r = client.post("/api/auth/login", json={"username": USERNAME, "password": "nope"})
    assert r.status_code == 401
    assert SESSION_COOKIE not in client.cookies


def test_login_sets_cookie_and_grants_access(logged_in):
    assert SESSION_COOKIE in logged_in.cookies
    assert logged_in.get("/api/projects").status_code == 200
    me = logged_in.get("/api/auth/me").json()
    assert me == {"username": USERNAME, "token_kind": "session"}


def test_logout_revokes_session(logged_in):
    cookie = logged_in.cookies[SESSION_COOKIE]
    assert logged_in.post("/api/auth/logout").status_code == 204
    other = anonymous()
    other.cookies.set(SESSION_COOKIE, cookie)
    assert other.get("/api/projects").status_code == 401


def test_login_lockout_after_repeated_failures(client):
    for _ in range(auth_module.LoginThrottle.MAX_FAILURES):
        client.post("/api/auth/login", json={"username": USERNAME, "password": "bad"})
    r = client.post("/api/auth/login", json={"username": USERNAME, "password": PASSWORD})
    assert r.status_code == 429
    assert "Retry-After" in r.headers


def test_login_without_user_returns_503(client):
    main.auth_store.path.unlink()
    r = client.post("/api/auth/login", json={"username": USERNAME, "password": PASSWORD})
    assert r.status_code == 503


def test_device_flow_end_to_end(logged_in):
    script = anonymous()
    dev = start_device(script)
    assert dev["verification_uri_complete"].endswith(f"?user_code={dev['user_code']}")

    r = script.post("/api/auth/device/token", json={"device_code": dev["device_code"]})
    assert r.status_code == 400 and r.json()["error"] == "authorization_pending"

    info = logged_in.get(f"/api/auth/device/{dev['user_code']}")
    assert info.status_code == 200 and info.json()["client_name"] == "test-script"

    # The code is accepted regardless of case or dash.
    code = dev["user_code"].replace("-", "").lower()
    r = logged_in.post("/api/auth/device/approve", json={"user_code": code, "approve": True})
    assert r.status_code == 204

    r = script.post("/api/auth/device/token", json={"device_code": dev["device_code"]})
    assert r.status_code == 200
    token = r.json()["access_token"]
    assert token.startswith("phub_")

    headers = {"Authorization": f"Bearer {token}"}
    assert script.get("/api/projects", headers=headers).status_code == 200
    assert script.get("/api/auth/me", headers=headers).json()["token_kind"] == "api"

    # Handed out only once.
    r = script.post("/api/auth/device/token", json={"device_code": dev["device_code"]})
    assert r.status_code == 400 and r.json()["error"] == "expired_token"


def test_device_flow_denied(logged_in):
    script = anonymous()
    dev = start_device(script)
    logged_in.post("/api/auth/device/approve", json={"user_code": dev["user_code"], "approve": False})
    r = script.post("/api/auth/device/token", json={"device_code": dev["device_code"]})
    assert r.json()["error"] == "access_denied"


def test_device_flow_slow_down(client):
    dev = start_device(client)
    client.post("/api/auth/device/token", json={"device_code": dev["device_code"]})
    r = client.post("/api/auth/device/token", json={"device_code": dev["device_code"]})
    assert r.json()["error"] == "slow_down"


def test_device_code_expires(logged_in, monkeypatch):
    dev = start_device(anonymous())
    real_time = time.time
    monkeypatch.setattr(auth_module.time, "time", lambda: real_time() + auth_module.DEVICE_CODE_TTL + 1)
    r = logged_in.post("/api/auth/device/approve", json={"user_code": dev["user_code"], "approve": True})
    assert r.status_code == 404
    r = logged_in.post("/api/auth/device/token", json={"device_code": dev["device_code"]})
    assert r.json()["error"] == "expired_token"


def test_approve_requires_session(logged_in):
    dev = start_device(anonymous())
    assert anonymous().post(
        "/api/auth/device/approve", json={"user_code": dev["user_code"], "approve": True}
    ).status_code == 401

    raw, _ = main.auth_store.issue_token("api", "other-script")
    r = anonymous().post(
        "/api/auth/device/approve",
        json={"user_code": dev["user_code"], "approve": True},
        headers={"Authorization": f"Bearer {raw}"},
    )
    assert r.status_code == 403


def test_revoked_token_is_rejected(client):
    raw, record = main.auth_store.issue_token("api", "script")
    headers = {"Authorization": f"Bearer {raw}"}
    assert client.get("/api/projects", headers=headers).status_code == 200
    main.auth_store.revoke(record.id)
    assert client.get("/api/projects", headers=headers).status_code == 401


def test_cli_revocation_is_picked_up_without_restart(client):
    raw, record = main.auth_store.issue_token("api", "script")
    headers = {"Authorization": f"Bearer {raw}"}
    # Simulate `python -m server tokens revoke` running in another process.
    cli_store = auth_module.AuthStore(main.auth_store.path)
    cli_store.load()
    time.sleep(0.01)
    assert cli_store.revoke(record.id)
    assert client.get("/api/projects", headers=headers).status_code == 401


def test_auth_file_stores_only_hashes(client):
    raw, _ = main.auth_store.issue_token("api", "script")
    content = main.auth_store.path.read_text()
    assert raw not in content
    assert PASSWORD not in content
    assert (main.auth_store.path.stat().st_mode & 0o777) == 0o600
