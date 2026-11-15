import os
import shutil
import tempfile
from pathlib import Path

import pytest

# Must be set before the server modules are imported (paths are read at import time).
_DATA_DIR = Path(tempfile.mkdtemp(prefix="project-hub-tests-"))
os.environ["PROJECT_HUB_DATA_DIR"] = str(_DATA_DIR)
os.environ.pop("PROJECT_HUB_AUTH_FILE", None)
os.environ.pop("PROJECT_HUB_PUBLIC_URL", None)

from fastapi.testclient import TestClient  # noqa: E402

from server import main, security  # noqa: E402
from server.services.auth import DeviceFlow, LoginThrottle  # noqa: E402
from server.services.database import DatabaseRegistry  # noqa: E402

USERNAME = "admin"
PASSWORD = "correct horse battery"
OTHER_USERNAME = "bob"
OTHER_PASSWORD = "another long password"


@pytest.fixture
def data_dir():
    return _DATA_DIR


@pytest.fixture
def client(data_dir):
    for child in data_dir.iterdir():
        shutil.rmtree(child) if child.is_dir() else child.unlink()
    main.auth_store.load()
    main.auth_store.add_user(USERNAME, PASSWORD)
    registry = DatabaseRegistry(data_dir)
    security.databases = main.databases = registry
    main.device_flow = DeviceFlow(main.auth_store)
    main.login_throttle = LoginThrottle()
    with TestClient(main.app) as c:
        yield c


def login(c: TestClient, username: str = USERNAME, password: str = PASSWORD) -> TestClient:
    r = c.post("/api/auth/login", json={"username": username, "password": password})
    assert r.status_code == 200, r.text
    return c


@pytest.fixture
def logged_in(client):
    return login(client)


@pytest.fixture
def other_user(client):
    """A second user, logged in on a separate client."""
    main.auth_store.add_user(OTHER_USERNAME, OTHER_PASSWORD)
    with TestClient(main.app) as c:
        yield login(c, OTHER_USERNAME, OTHER_PASSWORD)
