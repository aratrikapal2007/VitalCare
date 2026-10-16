"""Basic functional tests for VitalCare."""
from vitalcare.db import get_db
from conftest import login


def test_home_redirects_to_login_when_signed_out(client):
    response = client.get("/")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")


def test_doctor_can_sign_in_and_open_dashboard(client):
    response = login(client, "sana")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/dashboard")
    dashboard = client.get("/dashboard")
    assert dashboard.status_code == 200


def test_bad_password_does_not_sign_in(client):
    response = login(client, "sana", "not-the-password")
    assert response.status_code == 200
    assert client.get("/dashboard").status_code == 302


def test_logout_clears_session(client):
    login(client, "sana")
    assert client.get("/dashboard").status_code == 200
    response = client.post("/logout")
    assert response.status_code == 302
    assert client.get("/dashboard").status_code == 302


def test_signed_in_pages_are_not_cached(client):
    login(client, "sana")
    response = client.get("/dashboard")
    assert "no-store" in response.headers.get("Cache-Control", "")
    assert response.headers.get("Pragma") == "no-cache"


def test_patient_search_page_requires_login(client):
    response = client.post("/patient-search", data={"q": "Asha"})
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")
