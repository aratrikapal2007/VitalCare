import sqlite3
from flask import current_app, g


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(current_app.config["DATABASE"])
    db.row_factory = sqlite3.Row
    try:
        db.executescript('''
        CREATE TABLE IF NOT EXISTS users (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          username TEXT NOT NULL UNIQUE,
          display_name TEXT NOT NULL,
          role TEXT NOT NULL CHECK(role IN ('Patient','Doctor','Admin')),
          password_demo TEXT NOT NULL,
          patient_id INTEGER
        );
        CREATE TABLE IF NOT EXISTS patients (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          full_name TEXT NOT NULL,
          mrn TEXT NOT NULL UNIQUE,
          dob TEXT NOT NULL,
          diagnosis TEXT NOT NULL,
          department TEXT NOT NULL,
          notes TEXT NOT NULL DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS audit_events (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          event_type TEXT NOT NULL,
          details TEXT NOT NULL,
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        ''')
        user_cols = {r[1] for r in db.execute("PRAGMA table_info(users)").fetchall()}
        if "patient_id" not in user_cols:
            db.execute("ALTER TABLE users ADD COLUMN patient_id INTEGER")
        patient_cols = {r[1] for r in db.execute("PRAGMA table_info(patients)").fetchall()}
        if "notes" not in patient_cols:
            db.execute("ALTER TABLE patients ADD COLUMN notes TEXT NOT NULL DEFAULT ''")
        if db.execute("SELECT COUNT(*) FROM patients").fetchone()[0] == 0:
            db.executemany('''INSERT INTO patients
                (full_name,mrn,dob,diagnosis,department,notes) VALUES (?,?,?,?,?,?)''', [
                ("Asha Verma", "MRN-1001", "1988-04-12", "Seasonal allergy", "General", "Follow-up as needed."),
                ("Imran Shaikh", "MRN-1002", "1975-11-02", "Type 2 diabetes", "Endocrinology", "Routine monitoring."),
                ("Leela Nair", "MRN-1003", "1992-07-23", "Fractured wrist", "Orthopedics", "Recovery review scheduled."),
                ("Tom Baker", "MRN-1004", "1960-01-30", "Hypertension", "Cardiology", "Blood pressure review."),
                ("Nina Kapoor", "MRN-1005", "2001-03-18", "Migraine", "Neurology", "Discuss symptom frequency at review."),
                ("Kabir Das", "MRN-1006", "1983-09-09", "Asthma", "Pulmonology", "Routine respiratory review."),
            ])
        db.execute("DELETE FROM users WHERE role NOT IN ('Patient','Doctor','Admin')")
        for account in [
            ("sana", "Sana Iyer", "Doctor", "demo-only"),
            ("patient", "Asha Verma", "Patient", "demo-only"),
            ("admin", "VitalCare Administrator", "Admin", "demo-only"),
        ]:
            db.execute("INSERT OR IGNORE INTO users (username,display_name,role,password_demo) VALUES (?,?,?,?)", account)
        patient = db.execute("SELECT id FROM patients WHERE mrn=?", ("MRN-1001",)).fetchone()
        if patient:
            db.execute("UPDATE users SET display_name=?, role=?, patient_id=? WHERE username=?",
                        ("Asha Verma", "Patient", patient[0], "patient"))
        db.execute('''INSERT INTO audit_events(event_type,details)
          SELECT 'system','Database initialized' WHERE NOT EXISTS
          (SELECT 1 FROM audit_events WHERE event_type='system' AND details='Database initialized')''')
        db.commit()
    finally:
        db.close()
