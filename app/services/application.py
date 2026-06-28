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
    return True, "Application submitted successfully."


def withdraw_application(application: Application, student: Student) -> tuple[bool, str]:
    if application.student_id != student.id:
        return False, "Not authorised."
    if application.status != "pending":
        return False, "Only pending applications can be withdrawn."
    application.status = "withdrawn"
    application.date_reviewed = datetime.utcnow()
    db.session.commit()
    return True, "Application withdrawn."


def approve_application(application: Application, reviewer_notes: str = None) -> tuple[bool, str]:
    if application.status != "pending":
        return False, f"Application is already {application.status}."

    application.status = "approved"
    application.date_reviewed = datetime.utcnow()
    if reviewer_notes and reviewer_notes.strip():
        application.reviewer_notes = reviewer_notes.strip()

    # Auto-reject other pending applications for the same scholarship
    Application.query.filter(
        Application.scholarship_id == application.scholarship_id,
        Application.id != application.id,
        Application.status == "pending",
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
            payment_status="pending",
            notes=f"Approved for {application.student.full_name} — {application.scholarship.title}",
        )
        db.session.add(award)

    db.session.commit()
    return True, "Application approved. Awaiting disbursement setup."


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
    return True, "Application rejected."
