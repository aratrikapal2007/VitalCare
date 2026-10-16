"""Checks that deployment secrets are not hardcoded in application source."""
import os
from pathlib import Path

from vitalcare import create_app


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = PROJECT_ROOT / "vitalcare"


def test_secret_key_can_be_supplied_through_environment(monkeypatch, tmp_path):
    monkeypatch.setenv("VITALCARE_SECRET_KEY", "environment-test-secret")
    app = create_app({
        "TESTING": True,
        "DATABASE": str(tmp_path / "env-secret.db"),
        "ADMIN_OVERRIDE_CODE": "pytest-only-override",
    })
    assert app.config["SECRET_KEY"] == "environment-test-secret"


def test_secret_key_has_no_insecure_hardcoded_fallback():
    source = (PACKAGE_ROOT / "__init__.py").read_text(encoding="utf-8")
    assert "local-development-secret-change-before-deployment" not in source


def test_admin_override_code_is_not_hardcoded_in_app_factory():
    source = (PACKAGE_ROOT / "__init__.py").read_text(encoding="utf-8")
    assert 'ADMIN_OVERRIDE_CODE="override-2024"' not in source
    assert "ADMIN_OVERRIDE_CODE='override-2024'" not in source
