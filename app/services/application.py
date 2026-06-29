from datetime import datetime
from ..extensions import db
from ..models.application import Application
from ..models.scholarship import Scholarship
from ..models.student import Student
from ..models.award import Award


def submit_application(
    student: Student,
    scholarship: Scholarship,
    personal_statement: str,
    financial_need: str,
    intended_use: str,
) -> tuple[bool, str]:
    if not scholarship.is_active:
        return False, "This scholarship is no longer accepting applications."

    existing = Application.query.filter_by(
        student_id=student.id, scholarship_id=scholarship.id
    ).first()
    if existing:
        return False, "You have already applied for this scholarship."

    ps = (personal_statement or "").strip()
    fn = (financial_need or "").strip()
    iu = (intended_use or "").strip()

    if len(ps) < 150:
        return False, "Personal statement must be at least 150 characters."
    if len(fn) < 50:
        return False, "Financial need statement must be at least 50 characters."
    if len(iu) < 50:
        return False, "Intended use must be at least 50 characters."

    application = Application(
        student_id=student.id,
        scholarship_id=scholarship.id,
        personal_statement=ps,
        financial_need=fn,
        intended_use=iu,
        status="pending",
    )
    db.session.add(application)
    db.session.commit()

    try:
        from .email import send_application_received
        from .audit import log
        send_application_received(application)
        log("application_submitted", "application", application.id,
            f"{student.full_name} applied for {scholarship.title}")
    except Exception:
        pass

    return True, "Application submitted successfully."


def withdraw_application(application: Application, student: Student) -> tuple[bool, str]:
    if application.student_id != student.id:
        return False, "Not authorised."
    if application.status != "pending":
        return False, "Only pending applications can be withdrawn."
    application.status = "withdrawn"
    application.date_reviewed = datetime.utcnow()
    db.session.commit()

    try:
        from .audit import log
        log("application_withdrawn", "application", application.id,
            f"{student.full_name} withdrew from {application.scholarship.title}")
    except Exception:
        pass

    return True, "Application withdrawn."


def shortlist_application(application: Application, star_rating: int = None, reviewer_notes: str = None) -> tuple[bool, str]:
    if application.status not in ("pending", "shortlisted"):
        return False, f"Cannot shortlist an application with status '{application.status}'."
    application.status = "shortlisted"
    if star_rating and 1 <= star_rating <= 5:
        application.star_rating = star_rating
    if reviewer_notes and reviewer_notes.strip():
        application.reviewer_notes = reviewer_notes.strip()
    db.session.commit()

    try:
        from .email import send_shortlisted
        from .audit import log
        send_shortlisted(application)
        log("application_shortlisted", "application", application.id,
            f"{application.student.full_name} shortlisted for {application.scholarship.title}")
    except Exception:
        pass

    return True, "Applicant shortlisted."


def rate_application(application: Application, star_rating: int) -> tuple[bool, str]:
    if not (1 <= star_rating <= 5):
        return False, "Rating must be between 1 and 5."
    application.star_rating = star_rating
    db.session.commit()
    return True, "Rating saved."


def approve_application(application: Application, reviewer_notes: str = None) -> tuple[bool, str]:
    if application.status not in ("pending", "shortlisted"):
        return False, f"Application is already {application.status}."

    application.status = "approved"
    application.date_reviewed = datetime.utcnow()
    if reviewer_notes and reviewer_notes.strip():
        application.reviewer_notes = reviewer_notes.strip()

    Application.query.filter(
        Application.scholarship_id == application.scholarship_id,
        Application.id != application.id,
        Application.status.in_(["pending", "shortlisted"]),
    ).update({
        "status": "rejected",
        "date_reviewed": datetime.utcnow(),
        "rejection_reason": "Another applicant was selected for this scholarship.",
    })

    db.session.flush()

    if not application.award:
        award = Award(
            application_id=application.id,
            amount=application.scholarship.amount,
            payment_status="pending_acceptance",
            notes=f"Approved for {application.student.full_name} — {application.scholarship.title}",
        )
        db.session.add(award)

    db.session.commit()

    try:
        from .email import send_awarded
        from .audit import log
        send_awarded(application)
        log("application_approved", "application", application.id,
            f"{application.student.full_name} awarded {application.scholarship.title}")
    except Exception:
        pass

    return True, "Application approved. Student has been notified to accept the award."


def reject_application(application: Application, reason: str) -> tuple[bool, str]:
    if application.status == "approved":
        return False, "Approved applications cannot be rejected."
    if application.status == "rejected":
        return False, "Application is already rejected."

    reason = (reason or "").strip()
    if not reason:
        return False, "A rejection reason is required."

    application.status = "rejected"
    application.rejection_reason = reason
    application.date_reviewed = datetime.utcnow()
    db.session.commit()

    try:
        from .email import send_rejected
        from .audit import log
        send_rejected(application)
        log("application_rejected", "application", application.id,
            f"{application.student.full_name} rejected from {application.scholarship.title}: {reason}")
    except Exception:
        pass

    return True, "Application rejected."
