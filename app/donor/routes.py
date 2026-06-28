from flask import render_template, redirect, url_for, request, flash, abort
from flask_login import login_required, current_user
from functools import wraps
from . import donor
from ..models.application import Application
from ..models.scholarship import Scholarship
from ..models.award import Award
from ..services.scholarship import (
    get_donor_scholarships, create_scholarship, update_scholarship
)
from ..services.application import approve_application, reject_application
from ..services.award import mark_paid, get_donor_awards
from ..utils.helpers import MAJORS, DONOR_TYPES, PAYMENT_METHODS, format_currency, format_date


def donor_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "donor":
            abort(403)
        return f(*args, **kwargs)
    return decorated


@donor.route("/dashboard")
@login_required
@donor_required
def dashboard():
    profile = current_user.donor_profile
    scholarships = get_donor_scholarships(profile.id)

    from ..models.application import Application
    sch_ids = [s.id for s in scholarships]

    stats = {
        "scholarships": len(scholarships),
        "active": sum(1 for s in scholarships if s.is_active),
        "total_applications": Application.query.filter(
            Application.scholarship_id.in_(sch_ids)
        ).count() if sch_ids else 0,
        "pending_applications": Application.query.filter(
            Application.scholarship_id.in_(sch_ids),
            Application.status == "pending",
        ).count() if sch_ids else 0,
    }

    recent_apps = (
        Application.query
        .filter(Application.scholarship_id.in_(sch_ids))
        .order_by(Application.date_applied.desc())
        .limit(5)
        .all()
    ) if sch_ids else []

    return render_template(
        "donor/dashboard.html",
        profile=profile,
        stats=stats,
        recent_applications=recent_apps,
        format_currency=format_currency,
        format_date=format_date,
    )


@donor.route("/profile", methods=["GET", "POST"])
@login_required
@donor_required
def profile():
    p = current_user.donor_profile
    if request.method == "POST":
        from ..extensions import db
        p.name = request.form.get("name", "").strip()
        p.donor_type = request.form.get("donor_type", "").strip()
        p.contact_email = request.form.get("contact_email", "").strip()
        p.contact_phone = request.form.get("contact_phone", "").strip()
        p.address = request.form.get("address", "").strip()
        p.profile_completed = bool(p.name)
        db.session.commit()
        flash("Profile updated successfully.", "success")
        return redirect(url_for("donor.profile"))

    return render_template("donor/profile.html", profile=p, donor_types=DONOR_TYPES)


@donor.route("/scholarships")
@login_required
@donor_required
def scholarships():
    profile = current_user.donor_profile
    items = get_donor_scholarships(profile.id)
    return render_template(
        "donor/scholarships.html",
        scholarships=items,
        format_currency=format_currency,
        format_date=format_date,
    )


@donor.route("/scholarships/new", methods=["GET", "POST"])
@login_required
@donor_required
def scholarship_new():
    profile = current_user.donor_profile
    if request.method == "POST":
        ok, sch, msg = create_scholarship(
            donor=profile,
            title=request.form.get("title", ""),
            description=request.form.get("description", ""),
            amount_str=request.form.get("amount", ""),
            deadline_str=request.form.get("deadline", ""),
            is_active=request.form.get("is_active") == "1",
            min_gpa_str=request.form.get("min_gpa", ""),
            required_major=request.form.get("required_major", ""),
            need_based=request.form.get("need_based") == "1",
            criterion_text=request.form.get("criterion_text", ""),
        )
        if ok:
            flash(msg, "success")
            return redirect(url_for("donor.scholarships"))
        flash(msg, "danger")

    return render_template("donor/scholarship_form.html", scholarship=None, majors=MAJORS)


@donor.route("/scholarships/<int:scholarship_id>/edit", methods=["GET", "POST"])
@login_required
@donor_required
def scholarship_edit(scholarship_id):
    sch = Scholarship.query.get_or_404(scholarship_id)
    if sch.donor_id != current_user.donor_profile.id:
        abort(403)

    if request.method == "POST":
        ok, msg = update_scholarship(
            scholarship=sch,
            title=request.form.get("title", ""),
            description=request.form.get("description", ""),
            amount_str=request.form.get("amount", ""),
            deadline_str=request.form.get("deadline", ""),
            is_active=request.form.get("is_active") == "1",
            min_gpa_str=request.form.get("min_gpa", ""),
            required_major=request.form.get("required_major", ""),
            need_based=request.form.get("need_based") == "1",
            criterion_text=request.form.get("criterion_text", ""),
        )
        if ok:
            flash(msg, "success")
            return redirect(url_for("donor.scholarships"))
        flash(msg, "danger")

    return render_template("donor/scholarship_form.html", scholarship=sch, majors=MAJORS)


@donor.route("/applicants")
@login_required
@donor_required
def applicants():
    profile = current_user.donor_profile
    sch_ids = [s.id for s in get_donor_scholarships(profile.id)]

    scholarship_id = request.args.get("scholarship_id", type=int)
    status_filter = request.args.get("status", "")

    query = Application.query.filter(Application.scholarship_id.in_(sch_ids)) if sch_ids else Application.query.filter_by(id=-1)

    if scholarship_id:
        query = query.filter_by(scholarship_id=scholarship_id)
    if status_filter:
        query = query.filter_by(status=status_filter)

    apps = query.order_by(Application.date_applied.desc()).all()
    my_scholarships = get_donor_scholarships(profile.id)

    return render_template(
        "donor/applicants.html",
        applications=apps,
        my_scholarships=my_scholarships,
        scholarship_id=scholarship_id,
        status_filter=status_filter,
        format_currency=format_currency,
        format_date=format_date,
    )


@donor.route("/applicants/<int:app_id>")
@login_required
@donor_required
def applicant_detail(app_id):
    application = Application.query.get_or_404(app_id)
    if application.scholarship.donor_id != current_user.donor_profile.id:
        abort(403)

    from ..services.eligibility import check_eligibility
    eligible, reasons = check_eligibility(application.student, application.scholarship)

    return render_template(
        "donor/applicant_detail.html",
        application=application,
        eligible=eligible,
        reasons=reasons,
        format_currency=format_currency,
        format_date=format_date,
    )


@donor.route("/applicants/<int:app_id>/approve", methods=["POST"])
@login_required
@donor_required
def approve(app_id):
    application = Application.query.get_or_404(app_id)
    if application.scholarship.donor_id != current_user.donor_profile.id:
        abort(403)
    ok, msg = approve_application(application)
    flash(msg, "success" if ok else "danger")
    return redirect(url_for("donor.applicants"))


@donor.route("/applicants/<int:app_id>/reject", methods=["POST"])
@login_required
@donor_required
def reject(app_id):
    application = Application.query.get_or_404(app_id)
    if application.scholarship.donor_id != current_user.donor_profile.id:
        abort(403)
    ok, msg = reject_application(application)
    flash(msg, "success" if ok else "danger")
    return redirect(url_for("donor.applicants"))


@donor.route("/awards")
@login_required
@donor_required
def awards():
    profile = current_user.donor_profile
    all_awards = get_donor_awards(profile.id)

    total_amount = sum(a.amount_float for a in all_awards)
    paid_amount = sum(a.amount_float for a in all_awards if a.payment_status == "completed")

    return render_template(
        "donor/awards.html",
        awards=all_awards,
        total_amount=total_amount,
        paid_amount=paid_amount,
        payment_methods=PAYMENT_METHODS,
        format_currency=format_currency,
        format_date=format_date,
    )


@donor.route("/awards/<int:award_id>/pay", methods=["POST"])
@login_required
@donor_required
def award_pay(award_id):
    award = Award.query.get_or_404(award_id)
    if award.scholarship.donor_id != current_user.donor_profile.id:
        abort(403)

    ok, msg = mark_paid(
        award=award,
        payment_method=request.form.get("payment_method", ""),
        payment_reference=request.form.get("payment_reference", ""),
    )
    flash(msg, "success" if ok else "danger")
    return redirect(url_for("donor.awards"))


@donor.route("/settings", methods=["GET", "POST"])
@login_required
@donor_required
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

    return render_template("donor/settings.html")
