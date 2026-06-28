from flask import render_template, redirect, url_for, request, flash, abort
from flask_login import login_required, current_user
from functools import wraps
from . import admin
from ..models.user import User
from ..models.student import Student
from ..models.donor import Donor
from ..models.scholarship import Scholarship
from ..models.application import Application
from ..models.award import Award
from ..extensions import db
from ..utils.helpers import format_currency, format_date


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "admin":
            abort(403)
        return f(*args, **kwargs)
    return decorated


@admin.route("/dashboard")
@login_required
@admin_required
def dashboard():
    stats = {
        "students": Student.query.count(),
        "donors": Donor.query.count(),
        "scholarships": Scholarship.query.count(),
        "active_scholarships": Scholarship.query.filter_by(is_active=True).count(),
        "applications": Application.query.count(),
        "pending_applications": Application.query.filter_by(status="pending").count(),
        "approved_applications": Application.query.filter_by(status="approved").count(),
        "total_awarded": db.session.query(db.func.sum(Award.amount)).scalar() or 0,
    }

    recent_apps = (
        Application.query
        .order_by(Application.date_applied.desc())
        .limit(8)
        .all()
    )

    return render_template(
        "admin/dashboard.html",
        stats=stats,
        recent_applications=recent_apps,
        format_currency=format_currency,
        format_date=format_date,
    )


@admin.route("/students")
@login_required
@admin_required
def students():
    q = request.args.get("q", "").strip()
    query = Student.query
    if q:
        query = query.filter(
            db.or_(
                Student.first_name.ilike(f"%{q}%"),
                Student.last_name.ilike(f"%{q}%"),
                Student.email.ilike(f"%{q}%"),
                Student.student_code.ilike(f"%{q}%"),
            )
        )
    all_students = query.order_by(Student.id.desc()).all()
    return render_template("admin/students.html", students=all_students, q=q, format_date=format_date)


@admin.route("/students/<int:student_id>")
@login_required
@admin_required
def student_detail(student_id):
    s = Student.query.get_or_404(student_id)
    apps = Application.query.filter_by(student_id=s.id).order_by(Application.date_applied.desc()).all()
    return render_template(
        "admin/student_detail.html",
        student=s,
        applications=apps,
        format_currency=format_currency,
        format_date=format_date,
    )


@admin.route("/donors")
@login_required
@admin_required
def donors():
    q = request.args.get("q", "").strip()
    query = Donor.query
    if q:
        query = query.filter(
            db.or_(
                Donor.name.ilike(f"%{q}%"),
                Donor.contact_email.ilike(f"%{q}%"),
                Donor.donor_code.ilike(f"%{q}%"),
            )
        )
    all_donors = query.order_by(Donor.id.desc()).all()
    return render_template("admin/donors.html", donors=all_donors, q=q, format_currency=format_currency)


@admin.route("/scholarships")
@login_required
@admin_required
def scholarships():
    q = request.args.get("q", "").strip()
    query = Scholarship.query
    if q:
        query = query.filter(Scholarship.title.ilike(f"%{q}%"))
    all_scholarships = query.order_by(Scholarship.created_at.desc()).all()
    return render_template(
        "admin/scholarships.html",
        scholarships=all_scholarships,
        q=q,
        format_currency=format_currency,
        format_date=format_date,
    )


@admin.route("/scholarships/<int:scholarship_id>/toggle", methods=["POST"])
@login_required
@admin_required
def toggle_scholarship(scholarship_id):
    sch = Scholarship.query.get_or_404(scholarship_id)
    sch.is_active = not sch.is_active
    db.session.commit()
    status = "activated" if sch.is_active else "deactivated"
    flash(f'Scholarship "{sch.title}" {status}.', "success")
    return redirect(url_for("admin.scholarships"))


@admin.route("/applications")
@login_required
@admin_required
def applications():
    status_filter = request.args.get("status", "")
    q = request.args.get("q", "").strip()

    query = Application.query
    if status_filter:
        query = query.filter_by(status=status_filter)

    apps = query.order_by(Application.date_applied.desc()).all()

    if q:
        apps = [
            a for a in apps
            if q.lower() in (a.student.full_name or "").lower()
            or q.lower() in (a.scholarship.title or "").lower()
        ]

    return render_template(
        "admin/applications.html",
        applications=apps,
        status_filter=status_filter,
        q=q,
        format_currency=format_currency,
        format_date=format_date,
    )


@admin.route("/applications/<int:app_id>")
@login_required
@admin_required
def application_detail(app_id):
    application = Application.query.get_or_404(app_id)
    from ..services.eligibility import check_eligibility
    eligible, reasons = check_eligibility(application.student, application.scholarship)
    return render_template(
        "admin/application_detail.html",
        application=application,
        eligible=eligible,
        reasons=reasons,
        format_currency=format_currency,
        format_date=format_date,
    )


@admin.route("/applications/<int:app_id>/approve", methods=["POST"])
@login_required
@admin_required
def approve_application(app_id):
    from ..services.application import approve_application as svc_approve
    application = Application.query.get_or_404(app_id)
    ok, msg = svc_approve(application, reviewer_notes=request.form.get("reviewer_notes", ""))
    flash(msg, "success" if ok else "danger")
    return redirect(url_for("admin.application_detail", app_id=app_id))


@admin.route("/applications/<int:app_id>/reject", methods=["POST"])
@login_required
@admin_required
def reject_application(app_id):
    from ..services.application import reject_application as svc_reject
    application = Application.query.get_or_404(app_id)
    ok, msg = svc_reject(application, reason=request.form.get("rejection_reason", ""))
    flash(msg, "success" if ok else "danger")
    return redirect(url_for("admin.application_detail", app_id=app_id))


@admin.route("/users/<int:user_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_user(user_id):
    if current_user.id == user_id:
        flash("You cannot delete your own account.", "danger")
        return redirect(url_for("admin.students"))
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash("User deleted.", "info")
    return redirect(url_for("admin.students"))
