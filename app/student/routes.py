from datetime import date
from flask import render_template, redirect, url_for, request, flash, abort
from flask_login import login_required, current_user
from functools import wraps
from . import student
from ..models.application import Application
from ..models.scholarship import Scholarship
from ..services.application import submit_application, withdraw_application
from ..services.award import accept_award
from ..models.award import Award
from ..services.eligibility import eligibility_summary
from ..services.scholarship import filter_open_scholarships
from ..models.saved import SavedScholarship
from ..utils.helpers import MAJORS, ACADEMIC_YEARS, SCHOLARSHIP_CATEGORIES, format_currency, format_date


def student_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "student":
            abort(403)
        return f(*args, **kwargs)
    return decorated


def profile_required(f):
    """Redirect to profile page if student hasn't completed their profile."""
    @wraps(f)
    def decorated(*args, **kwargs):
        profile = current_user.student_profile
        if not profile or not profile.profile_completed:
            flash("Please complete your profile before continuing.", "warning")
            return redirect(url_for("student.profile"))
        return f(*args, **kwargs)
    return decorated


@student.route("/dashboard")
@login_required
@student_required
def dashboard():
    profile = current_user.student_profile

    my_apps = (
        Application.query
        .filter_by(student_id=profile.id)
        .order_by(Application.date_applied.desc())
        .limit(5)
        .all()
    )

    from ..models.scholarship import Scholarship
    from ..extensions import db as _db
    from datetime import date as _date

    # Sum of active open scholarships not yet applied to
    applied_ids = [a.scholarship_id for a in Application.query.filter_by(student_id=profile.id).all()]
    open_qs = Scholarship.query.filter_by(is_active=True).filter(
        _db.or_(Scholarship.deadline == None, Scholarship.deadline >= _date.today())
    )
    total_eligible = sum(
        float(s.amount) for s in open_qs.all() if s.id not in applied_ids
    )

    stats = {
        "total": Application.query.filter_by(student_id=profile.id).count(),
        "pending": Application.query.filter_by(student_id=profile.id, status="pending").count(),
        "shortlisted": Application.query.filter_by(student_id=profile.id, status="shortlisted").count(),
        "approved": Application.query.filter_by(student_id=profile.id, status="approved").count(),
        "rejected": Application.query.filter_by(student_id=profile.id, status="rejected").count(),
        "total_eligible": total_eligible,
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
                flash("Invalid date of birth format.", "danger")
                return render_template("student/profile.html", profile=p, majors=MAJORS, academic_years=ACADEMIC_YEARS)

        p.profile_completed = bool(p.first_name and p.last_name and p.major and p.gpa)
        db.session.commit()
        flash("Profile updated successfully.", "success")
        return redirect(url_for("student.profile"))

    return render_template("student/profile.html", profile=p, majors=MAJORS, academic_years=ACADEMIC_YEARS)


@student.route("/scholarships")
@login_required
@student_required
@profile_required
def scholarships():
    profile = current_user.student_profile
    q = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    effort = request.args.get("effort", "").strip()
    sort = request.args.get("sort", "deadline")
    min_amount = request.args.get("min_amount", type=float) or 0

    all_scholarships = filter_open_scholarships(
        q=q, category=category, effort=effort, min_amount=min_amount, sort=sort
    )

    saved_ids = {s.scholarship_id for s in profile.saved_scholarships}

    enriched = []
    for sch in all_scholarships:
        existing = Application.query.filter_by(
            student_id=profile.id, scholarship_id=sch.id
        ).first()
        eligibility = eligibility_summary(profile, sch)
        enriched.append({
            "scholarship": sch,
            "eligibility": eligibility,
            "already_applied": existing is not None,
            "application_status": existing.status if existing else None,
            "saved": sch.id in saved_ids,
        })

    # Best matches first when sorting by match
    if sort == "match":
        enriched.sort(key=lambda e: e["eligibility"]["match_pct"] or 0, reverse=True)

    return render_template(
        "student/scholarships.html",
        scholarships=enriched,
        q=q,
        category=category,
        effort=effort,
        sort=sort,
        min_amount=min_amount,
        categories=SCHOLARSHIP_CATEGORIES,
        today=date.today(),
        format_currency=format_currency,
        format_date=format_date,
    )


@student.route("/scholarships/<int:scholarship_id>")
@login_required
@student_required
def scholarship_detail(scholarship_id):
    sch = Scholarship.query.get_or_404(scholarship_id)

    # Students can only view active scholarships
    if not sch.is_active:
        flash("This scholarship is no longer available.", "warning")
        return redirect(url_for("student.scholarships"))

    profile = current_user.student_profile
    eligibility = eligibility_summary(profile, sch)

    existing = Application.query.filter_by(
        student_id=profile.id, scholarship_id=sch.id
    ).first()

    # Check if deadline has passed
    deadline_passed = sch.deadline and sch.deadline < date.today()

    return render_template(
        "student/scholarship_detail.html",
        scholarship=sch,
        eligibility=eligibility,
        existing_application=existing,
        deadline_passed=deadline_passed,
        format_currency=format_currency,
        format_date=format_date,
    )


@student.route("/scholarships/<int:scholarship_id>/apply", methods=["GET", "POST"])
@login_required
@student_required
@profile_required
def apply(scholarship_id):
    sch = Scholarship.query.get_or_404(scholarship_id)
    profile = current_user.student_profile

    # Guard: scholarship must be active
    if not sch.is_active:
        flash("This scholarship is no longer accepting applications.", "danger")
        return redirect(url_for("student.scholarships"))

    # Guard: deadline must not have passed
    if sch.deadline and sch.deadline < date.today():
        flash("The deadline for this scholarship has passed.", "danger")
        return redirect(url_for("student.scholarships"))

    # Guard: no duplicate application
    existing = Application.query.filter_by(
        student_id=profile.id, scholarship_id=sch.id
    ).first()
    if existing:
        flash("You have already applied for this scholarship.", "warning")
        return redirect(url_for("student.applications"))

    if request.method == "POST":
        ok, msg = submit_application(
            student=profile,
            scholarship=sch,
            personal_statement=request.form.get("personal_statement", ""),
            financial_need=request.form.get("financial_need", ""),
            intended_use=request.form.get("intended_use", ""),
        )
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


@student.route("/scholarships/<int:scholarship_id>/save", methods=["POST"])
@login_required
@student_required
def toggle_save(scholarship_id):
    Scholarship.query.get_or_404(scholarship_id)
    profile = current_user.student_profile

    existing = SavedScholarship.query.filter_by(
        student_id=profile.id, scholarship_id=scholarship_id
    ).first()

    if existing:
        db.session.delete(existing)
        db.session.commit()
        flash("Removed from saved scholarships.", "info")
    else:
        db.session.add(SavedScholarship(student_id=profile.id, scholarship_id=scholarship_id))
        db.session.commit()
        flash("Scholarship saved.", "success")

    return redirect(request.referrer or url_for("student.scholarships"))


@student.route("/saved")
@login_required
@student_required
def saved():
    profile = current_user.student_profile
    saved_rows = (
        profile.saved_scholarships
        .order_by(SavedScholarship.created_at.desc())
        .all()
    )

    enriched = []
    for row in saved_rows:
        sch = row.scholarship
        existing = Application.query.filter_by(
            student_id=profile.id, scholarship_id=sch.id
        ).first()
        enriched.append({
            "scholarship": sch,
            "eligibility": eligibility_summary(profile, sch),
            "already_applied": existing is not None,
            "application_status": existing.status if existing else None,
            "saved": True,
            "expired": sch.deadline and sch.deadline < date.today(),
            "inactive": not sch.is_active,
        })

    return render_template(
        "student/saved.html",
        scholarships=enriched,
        today=date.today(),
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

    # Ownership check — students can only withdraw their own applications
    if application.student_id != profile.id:
        abort(403)

    ok, msg = withdraw_application(application, profile)
    flash(msg, "success" if ok else "danger")
    return redirect(url_for("student.applications"))


@student.route("/awards/<int:award_id>/accept", methods=["GET", "POST"])
@login_required
@student_required
def award_accept(award_id):
    award = Award.query.get_or_404(award_id)
    profile = current_user.student_profile
    if award.application.student_id != profile.id:
        abort(403)

    if request.method == "POST":
        ok, msg = accept_award(
            award=award,
            student_payment_info=request.form.get("student_payment_info", ""),
        )
        flash(msg, "success" if ok else "danger")
        if ok:
            return redirect(url_for("student.applications"))

    return render_template(
        "student/award_accept.html",
        award=award,
        format_currency=format_currency,
    )


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


# Import db for query filters
from ..extensions import db
