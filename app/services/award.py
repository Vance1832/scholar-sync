from datetime import date
from ..extensions import db
from ..models.award import Award


def initiate_disbursement(
    award: Award,
    payment_method: str,
    recipient_account: str,
    notes: str = None,
) -> tuple[bool, str]:
    """Set recipient details and move award to 'processing' state."""
    if award.payment_status not in ("pending",):
        return False, f"Award is already {award.payment_status}."

    recipient_account = (recipient_account or "").strip()
    if not recipient_account:
        return False, "Recipient account / bank details are required."
    if not payment_method or not payment_method.strip():
        return False, "Payment method is required."

    award.payment_status = "processing"
    award.payment_method = payment_method.strip()
    award.recipient_account = recipient_account
    if notes:
        award.notes = (award.notes or "") + f" | {notes.strip()}"

    db.session.commit()
    return True, "Disbursement initiated. Enter the transfer reference to confirm payment."


def confirm_payment(
    award: Award,
    payment_reference: str,
    disbursement_proof: str,
) -> tuple[bool, str]:
    """Confirm transfer with reference number and proof — marks award as completed."""
    if award.payment_status not in ("processing",):
        return False, "Award must be in 'Processing' state to confirm payment."

    ref = (payment_reference or "").strip()
    proof = (disbursement_proof or "").strip()

    if not ref:
        return False, "Payment reference / transaction ID is required."
    if not proof:
        return False, "A disbursement confirmation note or receipt description is required."

    award.payment_status = "completed"
    award.payment_reference = ref
    award.disbursement_proof = proof
    award.disbursement_date = date.today()

    db.session.commit()
    return True, "Payment confirmed. Award marked as disbursed."


def cancel_award(award: Award, reason: str = None) -> tuple[bool, str]:
    if award.payment_status == "completed":
        return False, "Completed awards cannot be cancelled."
    award.payment_status = "cancelled"
    if reason:
        award.notes = (award.notes or "") + f" | Cancelled: {reason.strip()}"
    db.session.commit()
    return True, "Award cancelled."


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
