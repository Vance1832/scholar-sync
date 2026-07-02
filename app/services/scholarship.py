"""
Scholarship CRUD — ported from save_scholarship_with_criteria() and related functions.
"""
from datetime import date
from typing import Optional
from ..extensions import db
from ..models.scholarship import Scholarship, EligibilityCriteria
from ..models.donor import Donor
from ..utils.validators import validate_amount, validate_gpa, validate_deadline


def get_active_scholarships():
    return (
        Scholarship.query
        .filter_by(is_active=True)
        .order_by(Scholarship.deadline.asc().nullslast(), Scholarship.created_at.desc())
        .all()
    )


def filter_open_scholarships(
    q: str = "",
    category: str = "",
    effort: str = "",
    min_amount: float = 0,
    sort: str = "deadline",
):
    """Active, non-expired scholarships filtered by search/category/effort/amount and sorted."""
    query = Scholarship.query.filter_by(is_active=True).filter(
        db.or_(Scholarship.deadline == None, Scholarship.deadline >= date.today())  # noqa: E711
    )
    if q:
        query = query.filter(
            db.or_(
                Scholarship.title.ilike(f"%{q}%"),
                Scholarship.description.ilike(f"%{q}%"),
            )
        )
    if category:
        query = query.filter(Scholarship.category == category)
    if effort in ("easy", "essay", "detailed"):
        query = query.filter(Scholarship.effort_level == effort)
    if min_amount:
        query = query.filter(Scholarship.amount >= min_amount)

    if sort == "amount":
        query = query.order_by(Scholarship.amount.desc())
    elif sort == "newest":
        query = query.order_by(Scholarship.created_at.desc())
    else:  # deadline (soonest first, no-deadline last)
        query = query.order_by(Scholarship.deadline.asc().nullslast(), Scholarship.created_at.desc())

    return query.all()


def get_donor_scholarships(donor_id: int):
    return (
        Scholarship.query
        .filter_by(donor_id=donor_id)
        .order_by(Scholarship.created_at.desc())
        .all()
    )


def create_scholarship(
    donor: Donor,
    title: str,
    description: str,
    amount_str: str,
    deadline_str: str,
    is_active: bool,
    min_gpa_str: str,
    required_major: str,
    need_based: bool,
    criterion_text: str,
    category: str = "",
    effort_level: str = "essay",
) -> tuple[bool, Optional[Scholarship], str]:

    ok, amount, msg = validate_amount(amount_str)
    if not ok:
        return False, None, msg

    ok, gpa, msg = validate_gpa(min_gpa_str)
    if not ok:
        return False, None, msg

    ok, deadline, msg = validate_deadline(deadline_str)
    if not ok:
        return False, None, msg

    scholarship = Scholarship(
        donor_id=donor.id,
        title=title.strip(),
        description=description.strip(),
        amount=amount,
        deadline=deadline,
        is_active=is_active,
        category=category.strip() or None,
        effort_level=effort_level if effort_level in ("easy", "essay", "detailed") else "essay",
    )
    db.session.add(scholarship)
    db.session.flush()

    _upsert_criteria(scholarship.id, gpa, required_major, need_based, criterion_text)

    db.session.commit()
    return True, scholarship, "Scholarship created successfully"


def update_scholarship(
    scholarship: Scholarship,
    title: str,
    description: str,
    amount_str: str,
    deadline_str: str,
    is_active: bool,
    min_gpa_str: str,
    required_major: str,
    need_based: bool,
    criterion_text: str,
    category: str = "",
    effort_level: str = "essay",
) -> tuple[bool, str]:

    ok, amount, msg = validate_amount(amount_str)
    if not ok:
        return False, msg

    ok, gpa, msg = validate_gpa(min_gpa_str)
    if not ok:
        return False, msg

    ok, deadline, msg = validate_deadline(deadline_str)
    if not ok:
        return False, msg

    scholarship.title = title.strip()
    scholarship.description = description.strip()
    scholarship.amount = amount
    scholarship.deadline = deadline
    scholarship.is_active = is_active
    scholarship.category = category.strip() or None
    scholarship.effort_level = effort_level if effort_level in ("easy", "essay", "detailed") else "essay"

    _upsert_criteria(scholarship.id, gpa, required_major, need_based, criterion_text)

    db.session.commit()
    return True, "Scholarship updated successfully"


def delete_scholarship(scholarship: Scholarship) -> tuple[bool, str]:
    if scholarship.applications.filter(
        Scholarship.applications.property.mapper.class_.status.in_(["pending", "approved"])
    ).count():
        return False, "Cannot delete a scholarship with active or approved applications"
    db.session.delete(scholarship)
    db.session.commit()
    return True, "Scholarship deleted"


def _upsert_criteria(
    scholarship_id: int,
    min_gpa,
    required_major: str,
    need_based: bool,
    criterion_text: str,
) -> None:
    criteria = EligibilityCriteria.query.filter_by(scholarship_id=scholarship_id).first()
    if not criteria:
        criteria = EligibilityCriteria(scholarship_id=scholarship_id)
        db.session.add(criteria)

    criteria.min_gpa = min_gpa
    criteria.required_major = required_major.strip() if required_major else None
    criteria.need_based = need_based
    criteria.criterion_text = criterion_text.strip() if criterion_text else None
