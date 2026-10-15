# VitalCare Hospital Management System

A local Flask/SQLite sample application with Patient, Doctor, and Admin roles. All included patient data is fictional.

## Run locally

1. Install Python 3.10+.
2. Open a terminal in this folder.
3. Run `python -m venv .venv` (recommended) and activate it.
4. Run `pip install -r requirements.txt`.
5. Run `python run.py`.
6. Visit `http://127.0.0.1:5000`.

## Local credentials

- Patient: `patient` / `demo-only`
- Doctor: `sana` / `demo-only`
- Admin account: `admin` / `demo-only`
- Admin Portal access code: `override-2024`

## Important

This is a local educational sample, not a production medical application. It intentionally retains a hardcoded admin override and a vulnerable SQL search path so these weaknesses can be observed against fictional records. Keep it on localhost, never connect it to real patient data, and do not deploy it publicly. For production, remove the override, use properly hashed passwords and robust authorization, and use parameterized SQL for every query.
