from datetime import date, datetime
from ..extensions import db
from ..models.award import Award


def accept_award(award: Award, student_payment_info: str) -> tuple[bool, str]:
    if award.payment_status != "pending_acceptance":
        return False, "This award is not awaiting acceptance."
    info = (student_payment_info or "").strip()
    if not info:
        return False, "Please provide your payment details (bank account or school ID)."

    award.student_accepted = True
    award.student_payment_info = info
    award.accepted_at = datetime.utcnow()
    award.payment_status = "pending"
    db.session.commit()

    try:
        from .email import send_award_accepted_to_donor
        from .audit import log
        send_award_accepted_to_donor(award)
        log("award_accepted", "award", award.id,
            f"{award.student.full_name} accepted award for {award.scholarship.title}")
    except Exception:
        pass

    return True, "Award accepted. The donor will now arrange the transfer."


def initiate_disbursement(
    award: Award,
    payment_method: str,
    recipient_account: str,
    notes: str = None,
) -> tuple[bool, str]:
    if award.payment_status == "pending_acceptance":
        return False, "The student has not yet accepted this award."
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

    try:
        from .audit import log
        log("disbursement_initiated", "award", award.id,
            f"Disbursement initiated for {award.student.full_name}")
    except Exception:
        pass

    return True, "Disbursement initiated. Enter the transfer reference to confirm payment."


def confirm_payment(
    award: Award,
    payment_reference: str,
    disbursement_proof: str,
) -> tuple[bool, str]:
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

    try:
        from .email import send_disbursement_confirmed
        from .audit import log
        send_disbursement_confirmed(award)
        log("payment_confirmed", "award", award.id,
            f"Payment confirmed for {award.student.full_name}, ref {ref}")
    except Exception:
        pass

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
