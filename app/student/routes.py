from flask import render_template, redirect, url_for, request, flash, abort
from flask_login import login_required, current_user
from functools import wraps
from . import student
from ..models.application import Application
from ..models.scholarship import Scholarship
from ..services.scholarship import get_active_scholarships
from ..services.application import submit_application, withdraw_application
from ..services.eligibility import eligibility_summary
from ..utils.helpers import MAJORS, ACADEMIC_YEARS, format_currency, format_date


def student_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "student":
            abort(403)
        return f(*args, **kwargs)
    return decorated


@student.route("/dashboard")
@login_required
@student_required
def dashboard():
    profile = current_user.student_profile
    if not profile:
        abort(500)

    my_apps = (
        Application.query
        .filter_by(student_id=profile.id)
        .order_by(Application.date_applied.desc())
        .limit(5)
        .all()
    )

    stats = {
        "total": Application.query.filter_by(student_id=profile.id).count(),
        "pending": Application.query.filter_by(student_id=profile.id, status="pending").count(),
        "approved": Application.query.filter_by(student_id=profile.id, status="approved").count(),
        "rejected": Application.query.filter_by(student_id=profile.id, status="rejected").count(),
    }

    return render_template(
        "student/dashboard.html",
        profile=profile,
        recent_applications=my_apps,
        stats=stats,
        format_currency=format_currency,
        format_date=format_date,
    )


@student.route("/profile", methods=["GET", "POST"])
@login_required
@student_required
def profile():
    p = current_user.student_profile
    if request.method == "POST":
        from ..extensions import db
        from datetime import datetime

        p.first_name = request.form.get("first_name", "").strip()
        p.last_name = request.form.get("last_name", "").strip()
        p.email = request.form.get("email", "").strip()
        p.phone = request.form.get("phone", "").strip()
        p.address = request.form.get("address", "").strip()
        p.major = request.form.get("major", "").strip()
        p.academic_year = request.form.get("academic_year", "").strip()
        p.department = request.form.get("department", "").strip()

        gpa_str = request.form.get("gpa", "").strip()
        from ..utils.validators import validate_gpa
        ok, gpa_val, msg = validate_gpa(gpa_str)
        if not ok:
            flash(msg, "danger")
            return render_template("student/profile.html", profile=p, majors=MAJORS, academic_years=ACADEMIC_YEARS)

        p.gpa = gpa_val

        dob_str = request.form.get("date_of_birth", "").strip()
        if dob_str:
            try:
                p.date_of_birth = datetime.strptime(dob_str, "%Y-%m-%d").date()
            except ValueError:
                flash("Invalid date of birth format", "danger")
                return render_template("student/profile.html", profile=p, majors=MAJORS, academic_years=ACADEMIC_YEARS)

        p.profile_completed = bool(p.first_name and p.last_name and p.major)
        db.session.commit()
        flash("Profile updated successfully.", "success")
        return redirect(url_for("student.profile"))

    return render_template("student/profile.html", profile=p, majors=MAJORS, academic_years=ACADEMIC_YEARS)


@student.route("/scholarships")
@login_required
@student_required
def scholarships():
    profile = current_user.student_profile
    q = request.args.get("q", "").strip()
    major_filter = request.args.get("major", "").strip()

    query = Scholarship.query.filter_by(is_active=True)
    if q:
        query = query.filter(Scholarship.title.ilike(f"%{q}%"))

    all_scholarships = query.order_by(Scholarship.deadline.asc().nullslast()).all()

    enriched = []
    for sch in all_scholarships:
        eligibility = eligibility_summary(profile, sch)
        enriched.append({"scholarship": sch, "eligibility": eligibility})

    return render_template(
        "student/scholarships.html",
        scholarships=enriched,
        q=q,
        format_currency=format_currency,
        format_date=format_date,
    )


@student.route("/scholarships/<int:scholarship_id>")
@login_required
@student_required
def scholarship_detail(scholarship_id):
    sch = Scholarship.query.get_or_404(scholarship_id)
    profile = current_user.student_profile

    eligibility = eligibility_summary(profile, sch)

    existing = None
    if profile:
        existing = Application.query.filter_by(
            student_id=profile.id, scholarship_id=sch.id
        ).first()

    return render_template(
        "student/scholarship_detail.html",
        scholarship=sch,
        eligibility=eligibility,
        existing_application=existing,
        format_currency=format_currency,
        format_date=format_date,
    )


@student.route("/scholarships/<int:scholarship_id>/apply", methods=["GET", "POST"])
@login_required
@student_required
def apply(scholarship_id):
    sch = Scholarship.query.get_or_404(scholarship_id)
    profile = current_user.student_profile

    if request.method == "POST":
        message = request.form.get("application_message", "")
        ok, msg = submit_application(profile, sch, message)
        if ok:
            flash(msg, "success")
            return redirect(url_for("student.applications"))
        flash(msg, "danger")

    eligibility = eligibility_summary(profile, sch)
    return render_template(
        "student/apply.html",
        scholarship=sch,
        eligibility=eligibility,
        format_currency=format_currency,
        format_date=format_date,
    )


@student.route("/applications")
@login_required
@student_required
def applications():
    profile = current_user.student_profile
    status_filter = request.args.get("status", "")

    query = Application.query.filter_by(student_id=profile.id)
    if status_filter:
        query = query.filter_by(status=status_filter)

    apps = query.order_by(Application.date_applied.desc()).all()

    return render_template(
        "student/applications.html",
        applications=apps,
        status_filter=status_filter,
        format_currency=format_currency,
        format_date=format_date,
    )


@student.route("/applications/<int:app_id>/withdraw", methods=["POST"])
@login_required
@student_required
def withdraw(app_id):
    application = Application.query.get_or_404(app_id)
    profile = current_user.student_profile
    ok, msg = withdraw_application(application, profile)
    flash(msg, "success" if ok else "danger")
    return redirect(url_for("student.applications"))


@student.route("/settings", methods=["GET", "POST"])
@login_required
@student_required
def settings():
    if request.method == "POST":
        action = request.form.get("action")
        from ..services.auth import change_password, change_username

        if action == "change_password":
            ok, msg = change_password(
                current_user,
                request.form.get("current_password", ""),
                request.form.get("new_password", ""),
                request.form.get("confirm_password", ""),
            )
            flash(msg, "success" if ok else "danger")

        elif action == "change_username":
            ok, msg = change_username(current_user, request.form.get("new_username", ""))
            flash(msg, "success" if ok else "danger")

    return render_template("student/settings.html")
