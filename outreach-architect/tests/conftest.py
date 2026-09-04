"""Shared fixtures. Configuration is explicit so results never depend on a
developer's local .env."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

os.environ.setdefault("ENVIRONMENT", "testing")
os.environ.setdefault("API_KEY", "test-api-key-not-a-real-one")
os.environ.setdefault("LOG_LEVEL", "WARNING")
os.environ.setdefault("EMAIL_SENDING_ENABLED", "false")

_DB = Path(tempfile.gettempdir()) / "outreach_test.db"
os.environ.setdefault("DATABASE_URL", f"sqlite:///{_DB.as_posix()}")

import pytest  # noqa: E402

TEST_API_KEY = os.environ["API_KEY"]


@pytest.fixture(scope="session")
def api_key() -> str:
    return TEST_API_KEY


@pytest.fixture(scope="session")
def auth_headers(api_key) -> dict[str, str]:
    return {"X-API-Key": api_key}


@pytest.fixture
def client():
    from fastapi.testclient import TestClient

    from main import app

    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True, scope="session")
def _cleanup_db():
    yield
    if _DB.exists():
        try:
            _DB.unlink()
        except OSError:
            pass
