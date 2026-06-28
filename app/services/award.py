"""
Award payment tracking — ported from update_award_payment_status() in the original monolith.
"""
from datetime import date
from ..extensions import db
from ..models.award import Award


def mark_paid(
    award: Award,
    payment_method: str,
    payment_reference: str,
    notes: str = None,
) -> tuple[bool, str]:
    if not payment_reference or not payment_reference.strip():
        return False, "Payment reference is required"

    award.payment_status = "completed"
    award.payment_method = payment_method
    award.payment_reference = payment_reference.strip()
    award.disbursement_date = date.today()

    if notes:
        existing = award.notes or ""
        award.notes = existing + f" | {notes.strip()}"

    db.session.commit()
    return True, "Payment recorded successfully"


def update_payment_status(
    award: Award,
    status: str,
    payment_method: str = None,
    payment_reference: str = None,
    notes: str = None,
) -> tuple[bool, str]:
    valid_statuses = {"pending", "processing", "completed", "failed", "cancelled"}
    if status not in valid_statuses:
        return False, f"Invalid status: {status}"

    award.payment_status = status
    if status == "completed":
        award.disbursement_date = date.today()
    if payment_method:
        award.payment_method = payment_method
    if payment_reference:
        award.payment_reference = payment_reference
    if notes:
        existing = award.notes or ""
        award.notes = existing + f" | {notes}"

    db.session.commit()
    return True, "Payment status updated"


def get_donor_awards(donor_id: int):
    from ..models.scholarship import Scholarship
    from ..models.application import Application

    return (
        Award.query
        .join(Application, Award.application_id == Application.id)
        .join(Scholarship, Application.scholarship_id == Scholarship.id)
        .filter(Scholarship.donor_id == donor_id)
        .order_by(Award.award_date.desc())
        .all()
    )
