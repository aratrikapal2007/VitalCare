"""Security regression tests for SQL injection and stored XSS."""
from conftest import login
from vitalcare.db import get_db


def test_patient_search_treats_sql_injection_payload_as_literal(client, app):
    login(client, "sana")
    payload = "' OR 1=1 --"
    response = client.post("/patient-search", data={"q": payload})
    assert response.status_code == 200

    # A SQL injection payload must not turn a search into an all-patient query.
    with app.app_context():
        db = get_db()
        expected = db.execute(
            "SELECT COUNT(*) FROM patients WHERE full_name LIKE ? OR mrn LIKE ?",
            (f"%{payload}%", f"%{payload}%"),
        ).fetchone()[0]
    if expected == 0:
        assert b"Asha Verma" not in response.data
        assert b"Imran Shaikh" not in response.data


def test_search_special_characters_are_not_executed_as_sql(client):
    login(client, "sana")
    response = client.post("/patient-search", data={"q": "'"})
    assert response.status_code == 200
    # A quote is ordinary search text, not a SQL syntax error or query control.
    assert b"We could not complete that search" not in response.data


def test_patient_cannot_open_doctor_only_patient_list(client):
    login(client, "patient")
    response = client.get("/patients")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/dashboard")


def test_patient_cannot_open_another_patient_record(client):
    login(client, "patient")
    # Patient role must not be able to use the doctor/admin detail route.
    response = client.get("/patients/2")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/dashboard")


def test_patient_record_output_escapes_stored_html(client, app):
    login(client, "patient")
    payload = '<script>alert("xss-test")</script>'
    with app.app_context():
        db = get_db()
        db.execute(
            "UPDATE patients SET notes=? WHERE mrn=?",
            (payload, "MRN-1001"),
        )
        db.commit()

    response = client.get("/my-record")
    assert response.status_code == 200
    assert payload.encode() not in response.data
    assert b"&lt;script&gt;" in response.data
