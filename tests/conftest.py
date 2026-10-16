"""Shared fixtures for VitalCare security regression tests."""
import os
import sys
import tempfile

import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from vitalcare import create_app  # noqa: E402


@pytest.fixture()
def app():
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    test_app = create_app({
        "TESTING": True,
        "SECRET_KEY": "pytest-only-secret-key",
        "DATABASE": db_path,
        # Set a test-only override value; never use the production value here.
        "ADMIN_OVERRIDE_CODE": "pytest-only-override",
    })
    yield test_app
    try:
        os.unlink(db_path)
    except FileNotFoundError:
        pass


@pytest.fixture()
def client(app):
    return app.test_client()


def login(client, username, password="demo-only"):
    return client.post(
        "/login",
        data={"username": username, "password": password},
        follow_redirects=False,
    )
