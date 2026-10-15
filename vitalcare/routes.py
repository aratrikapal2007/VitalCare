from functools import wraps
from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for
from .db import get_db

bp = Blueprint("main", __name__)


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please sign in to continue.", "warning")
            return redirect(url_for("main.login"))
        return view(*args, **kwargs)
    return wrapped


def role_required(*roles):
    def decorate(view):
        @wraps(view)
        @login_required
        def wrapped(*args, **kwargs):
            if session.get("role") not in roles:
                flash("You do not have permission to access that page.", "error")
                return redirect(url_for("main.dashboard"))
            return view(*args, **kwargs)
        return wrapped
    return decorate


@bp.after_request
def no_store_for_signed_in_pages(response):
    if session.get("user_id"):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
    return response


@bp.route("/")
def index():
    return redirect(url_for("main.dashboard" if session.get("user_id") else "main.login"))


@bp.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("main.dashboard"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = get_db().execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        if user and user["password_demo"] == password:
            session.clear()
            session.update(user_id=user["id"], username=user["username"],
                           display_name=user["display_name"], role=user["role"],
                           patient_id=user["patient_id"])
            get_db().execute("INSERT INTO audit_events(event_type,details) VALUES (?,?)",
                             ("login", f"{user['role']} signed in"))
            get_db().commit()
            flash(f"Welcome back, {user['display_name']}.", "success")
            return redirect(url_for("main.dashboard"))
        flash("The username or password was not recognised.", "error")
    return render_template("login.html")


@bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("main.login"))


@bp.route("/dashboard")
@login_required
def dashboard():
    db = get_db()
    role = session.get("role")
    if role == "Patient":
        patient = db.execute("SELECT * FROM patients WHERE id=?", (session.get("patient_id"),)).fetchone()
        return render_template("patient_dashboard.html", patient=patient)
    if role == "Doctor":
        count = db.execute("SELECT COUNT(*) FROM patients").fetchone()[0]
        return render_template("doctor_dashboard.html", patient_count=count)
    if role == "Admin":
        patient_count = db.execute("SELECT COUNT(*) FROM patients").fetchone()[0]
        user_count = db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        events = db.execute("SELECT * FROM audit_events ORDER BY id DESC LIMIT 6").fetchall()
        return render_template("admin_dashboard.html", patient_count=patient_count,
                               user_count=user_count, recent_events=events)
    session.clear()
    return redirect(url_for("main.login"))


@bp.route("/patients")
@role_required("Doctor", "Admin")
def patients_list():
    query = request.args.get("q", "").strip()
    db = get_db()
    if query:
        rows = db.execute("SELECT * FROM patients WHERE full_name LIKE ? OR mrn LIKE ? ORDER BY full_name",
                          (f"%{query}%", f"%{query}%")).fetchall()
    else:
        rows = db.execute("SELECT * FROM patients ORDER BY full_name").fetchall()
    return render_template("patients.html", patients=rows, query=query)


@bp.route("/my-record")
@role_required("Patient")
def my_record():
    patient = get_db().execute("SELECT * FROM patients WHERE id=?", (session.get("patient_id"),)).fetchone()
    return render_template("patient_record.html", patient=patient, own_record=True)


@bp.route("/patients/<int:patient_id>")
@role_required("Doctor", "Admin")
def patient_detail(patient_id):
    patient = get_db().execute("SELECT * FROM patients WHERE id=?", (patient_id,)).fetchone()
    if not patient:
        flash("That patient record could not be found.", "error")
        return redirect(url_for("main.patients_list"))
    return render_template("patient_record.html", patient=patient, own_record=False)


@bp.route("/admin-access", methods=["GET", "POST"])
def admin_access():
    if session.get("user_id") and session.get("role") == "Admin":
        return redirect(url_for("main.dashboard"))
    if request.method == "POST":
        if request.form.get("code", "") == current_app.config["ADMIN_OVERRIDE_CODE"]:
            admin = get_db().execute("SELECT * FROM users WHERE role='Admin' ORDER BY id LIMIT 1").fetchone()
            if admin:
                session.clear()
                session.update(user_id=admin["id"], username=admin["username"],
                               display_name=admin["display_name"], role=admin["role"], patient_id=None)
                get_db().execute("INSERT INTO audit_events(event_type,details) VALUES (?,?)",
                                 ("admin_access", "Administrator portal accessed"))
                get_db().commit()
                flash("Welcome to the Admin Portal.", "success")
                return redirect(url_for("main.dashboard"))
        flash("The access code was not recognised.", "error")
    return render_template("admin_access.html")


@bp.route("/patient-search", methods=["GET", "POST"])
@login_required
def patient_search():
    query = ""
    rows = []
    if request.method == "POST":
        query = request.form.get("q", "").strip()
        if query:
            sql = ("SELECT id,full_name,mrn,dob,diagnosis,department FROM patients WHERE full_name LIKE '%"
                   + query + "%' OR mrn LIKE '%" + query + "%' ORDER BY full_name")
            try:
                rows = get_db().execute(sql).fetchall()
                get_db().execute("INSERT INTO audit_events(event_type,details) VALUES (?,?)",
                                 ("search", f"Patient search by {session.get('username')}"))
                get_db().commit()
            except Exception:
                flash("We could not complete that search. Please try again.", "error")
    return render_template("patient_search.html", results=rows, query=query)
