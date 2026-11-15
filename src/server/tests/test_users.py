import json
import time

import pytest
from fastapi.testclient import TestClient

from server import main
from server.services import auth as auth_module
from server.services.auth import UserError, hash_password
from server.services.database import DatabaseRegistry

from .conftest import OTHER_PASSWORD, OTHER_USERNAME, PASSWORD, USERNAME, login


def project(pid: str, name: str = "P", status: str = "active"):
    return {"id": pid, "name": name, "status": status, "columns": [{"id": "c", "title": "To Do", "tasks": []}]}


def test_each_user_sees_only_their_projects(logged_in, other_user, data_dir):
    assert logged_in.post("/api/projects", json=[project("a1"), project("a2", status="archived")]).status_code == 200
    assert other_user.post("/api/projects", json=[project("b1")]).status_code == 200

    assert {p["id"] for p in logged_in.get("/api/projects").json()} == {"a1", "a2"}
    assert [p["id"] for p in other_user.get("/api/projects").json()] == ["b1"]

    admin = main.auth_store.find_user(USERNAME)
    files = sorted(f.name for f in (data_dir / "users" / admin.id).iterdir())
    assert files == ["projects.json", "projects_archived.json"]


def test_me_reports_the_logged_in_user(logged_in, other_user):
    assert logged_in.get("/api/auth/me").json()["username"] == USERNAME
    assert other_user.get("/api/auth/me").json()["username"] == OTHER_USERNAME


def test_login_is_case_insensitive_on_username(client):
    login(client, USERNAME.upper(), PASSWORD)
    assert client.get("/api/auth/me").json()["username"] == USERNAME


def test_wrong_password_of_another_user_is_rejected(client, other_user):
    r = client.post("/api/auth/login", json={"username": OTHER_USERNAME, "password": PASSWORD})
    assert r.status_code == 401


def test_device_token_belongs_to_the_approving_user(other_user):
    script = TestClient(main.app)
    dev = script.post("/api/auth/device/code", json={"client_name": "bob-script"}).json()
    other_user.post("/api/auth/device/approve", json={"user_code": dev["user_code"], "approve": True})
    token = script.post("/api/auth/device/token", json={"device_code": dev["device_code"]}).json()["access_token"]

    other_user.post("/api/projects", json=[project("b1")])
    headers = {"Authorization": f"Bearer {token}"}
    assert script.get("/api/auth/me", headers=headers).json()["username"] == OTHER_USERNAME
    assert [p["id"] for p in script.get("/api/projects", headers=headers).json()] == ["b1"]


def test_duplicate_and_invalid_usernames_are_rejected(client):
    with pytest.raises(UserError):
        main.auth_store.add_user(USERNAME.upper(), PASSWORD)
    with pytest.raises(UserError):
        main.auth_store.add_user("../evil", PASSWORD)
    with pytest.raises(UserError):
        main.auth_store.add_user("short-pass", "1234567")


def test_removed_user_loses_access_and_data_goes_to_trash(logged_in, other_user, data_dir):
    other_user.post("/api/projects", json=[project("b1")])
    bob = main.auth_store.find_user(OTHER_USERNAME)

    # Simulate `python -m server users remove bob` in another process.
    cli_store = auth_module.AuthStore(main.auth_store.path)
    cli_store.load()
    time.sleep(0.01)
    cli_store.remove_user(OTHER_USERNAME)
    trashed = DatabaseRegistry(data_dir).trash(bob.id)

    assert other_user.get("/api/projects").status_code == 401
    assert not (data_dir / "users" / bob.id).exists()
    assert trashed is not None and (trashed / "projects.json").exists()
    assert logged_in.get("/api/projects").status_code == 200
    assert all(t.user_id != bob.id for t in main.auth_store.list_tokens())


def test_password_change_revokes_only_that_users_sessions(logged_in, other_user):
    bob = main.auth_store.find_user(OTHER_USERNAME)
    raw, _ = main.auth_store.issue_token(bob.id, "api", "bob-script")
    main.auth_store.set_password(OTHER_USERNAME, "a brand new password")

    assert other_user.get("/api/projects").status_code == 401
    assert logged_in.get("/api/projects").status_code == 200
    assert TestClient(main.app).get("/api/projects", headers={"Authorization": f"Bearer {raw}"}).status_code == 200


def test_legacy_single_user_auth_is_migrated(client, data_dir):
    path = main.auth_store.path
    legacy_token = {
        "id": "abcd1234",
        "kind": "api",
        "name": "old-script",
        "hash": auth_module._hash_token("phub_legacy"),
        "created_at": time.time(),
        "expires_at": None,
        "last_used_at": None,
    }
    path.write_text(json.dumps({
        "user": {"username": "legacy", "password_hash": hash_password(PASSWORD)},
        "tokens": [legacy_token],
    }))

    store = auth_module.AuthStore(path)
    store.load()
    users = store.list_users()
    assert [u.username for u in users] == ["legacy"]
    assert store.resolve_token("phub_legacy")[0].id == users[0].id
    assert store.authenticate("legacy", PASSWORD) is not None
    saved = json.loads(path.read_text())
    assert "user" not in saved and saved["users"][0]["username"] == "legacy"


def test_legacy_projects_are_adopted_without_overwriting(data_dir):
    registry = DatabaseRegistry(data_dir)
    (data_dir / "projects.json").write_text(json.dumps([project("old")]))
    (data_dir / "projects_archived.json").write_text("[]")

    assert registry.adopt_legacy_data("u1")
    assert [p.id for p in registry.get("u1").get_projects()] == ["old"]
    assert not (data_dir / "projects.json").exists()

    # A second legacy file never replaces data the user already has.
    (data_dir / "projects.json").write_text(json.dumps([project("other")]))
    assert not registry.adopt_legacy_data("u1")
    assert [p.id for p in registry.get("u1").get_projects()] == ["old"]


def test_user_dir_rejects_unsafe_ids(data_dir):
    with pytest.raises(ValueError):
        DatabaseRegistry(data_dir).user_dir("../x")
