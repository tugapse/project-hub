import os
import tempfile
from pathlib import Path

import pytest

# Must be set before the server modules are imported (paths are read at import time).
_DATA_DIR = Path(tempfile.mkdtemp(prefix="project-hub-tests-"))
os.environ["PROJECT_HUB_JSON_FILE"] = str(_DATA_DIR / "projects.json")
os.environ["PROJECT_HUB_AUTH_FILE"] = str(_DATA_DIR / "auth.json")
os.environ.pop("PROJECT_HUB_PUBLIC_URL", None)

from fastapi.testclient import TestClient  # noqa: E402

from server import main  # noqa: E402
from server.services.auth import DeviceFlow, LoginThrottle  # noqa: E402

USERNAME = "admin"
PASSWORD = "correct horse battery"


@pytest.fixture
def client():
    auth_file = Path(os.environ["PROJECT_HUB_AUTH_FILE"])
    auth_file.unlink(missing_ok=True)
    main.auth_store.load()
    main.auth_store.set_user(USERNAME, PASSWORD)
    main.device_flow = DeviceFlow(main.auth_store)
    main.login_throttle = LoginThrottle()
    with TestClient(main.app) as c:
        yield c


@pytest.fixture
def logged_in(client):
    r = client.post("/api/auth/login", json={"username": USERNAME, "password": PASSWORD})
    assert r.status_code == 200
    return client
