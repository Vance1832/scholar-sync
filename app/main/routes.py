"""
Public marketing site — landing page and login-free scholarship browsing.
Authenticated users are routed to their role dashboard from the landing page.
"""
from datetime import date
from flask import render_template, redirect, url_for, request
from flask_login import current_user
from . import main
from ..extensions import db
from ..models.scholarship import Scholarship
from ..models.student import Student
from ..models.award import Award
from ..models.donor import Donor
from ..services.scholarship import filter_open_scholarships
from ..utils.helpers import SCHOLARSHIP_CATEGORIES, format_currency, format_date


def _site_stats() -> dict:
    open_scholarships = Scholarship.query.filter_by(is_active=True).filter(
        db.or_(Scholarship.deadline == None, Scholarship.deadline >= date.today())  # noqa: E711
    ).all()
    total_available = sum(float(s.amount) * (s.slots or 1) for s in open_scholarships)
    total_awarded = db.session.query(db.func.coalesce(db.func.sum(Award.amount), 0)).scalar()
    return {
        "open_count": len(open_scholarships),
        "total_available": float(total_available),
        "total_awarded": float(total_awarded),
        "students": Student.query.count(),
        "donors": Donor.query.count(),
    }


@main.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for(f"{current_user.role}.dashboard"))

    featured = filter_open_scholarships(sort="amount")[:6]
    return render_template(
        "public/landing.html",
        stats=_site_stats(),
        featured=featured,
        categories=SCHOLARSHIP_CATEGORIES,
        today=date.today(),
        format_currency=format_currency,
        format_date=format_date,
    )


@main.route("/scholarships")
def scholarships():
    q = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    effort = request.args.get("effort", "").strip()
    sort = request.args.get("sort", "deadline")
    min_amount = request.args.get("min_amount", type=float) or 0

    items = filter_open_scholarships(
        q=q, category=category, effort=effort, min_amount=min_amount, sort=sort
    )

    return render_template(
        "public/scholarships.html",
        scholarships=items,
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


@main.route("/scholarships/<int:scholarship_id>")
def scholarship_detail(scholarship_id):
    sch = Scholarship.query.get_or_404(scholarship_id)
    if not sch.is_active:
        return redirect(url_for("main.scholarships"))

    # Logged-in students get the full in-app view with eligibility checks
    if current_user.is_authenticated and current_user.role == "student":
        return redirect(url_for("student.scholarship_detail", scholarship_id=scholarship_id))

    deadline_passed = sch.deadline and sch.deadline < date.today()
    related = [
        s for s in filter_open_scholarships(category=sch.category or "")
        if s.id != sch.id
    ][:3]

    return render_template(
        "public/scholarship_detail.html",
        scholarship=sch,
        deadline_passed=deadline_passed,
        related=related,
        today=date.today(),
        format_currency=format_currency,
        format_date=format_date,
    )
