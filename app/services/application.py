"""
Application submission, approval, rejection — ported from submit_application_with_checks()
and approve_application_and_create_award() in the original monolith.
"""
from datetime import datetime
from ..extensions import db
from ..models.application import Application
from ..models.scholarship import Scholarship
from ..models.student import Student
from ..models.award import Award
from ..utils.validators import validate_application_message


def submit_application(
    student: Student, scholarship: Scholarship, message: str
) -> tuple[bool, str]:
    ok, msg = validate_application_message(message)
    if not ok:
        return False, msg

    if not scholarship.is_active:
        return False, "This scholarship is no longer accepting applications"

    existing = Application.query.filter_by(
        student_id=student.id, scholarship_id=scholarship.id
    ).first()
    if existing:
        return False, "You have already applied for this scholarship"

    application = Application(
        student_id=student.id,
        scholarship_id=scholarship.id,
        application_message=message.strip(),
        status="pending",
    )
    db.session.add(application)
    db.session.commit()
    return True, "Application submitted successfully"


def withdraw_application(application: Application, student: Student) -> tuple[bool, str]:
    if application.student_id != student.id:
        return False, "Not authorised"
    if application.status != "pending":
        return False, "Only pending applications can be withdrawn"
    application.status = "withdrawn"
    application.date_reviewed = datetime.utcnow()
    db.session.commit()
    return True, "Application withdrawn"


def approve_application(application: Application) -> tuple[bool, str]:
    if application.status != "pending":
        return False, f"Application is already {application.status}"

    application.status = "approved"
    application.date_reviewed = datetime.utcnow()

    Application.query.filter(
        Application.scholarship_id == application.scholarship_id,
        Application.id != application.id,
        Application.status == "pending",
    ).update({"status": "rejected", "date_reviewed": datetime.utcnow()})

    db.session.flush()

    if not application.award:
        award = Award(
            application_id=application.id,
            amount=application.scholarship.amount,
            payment_status="pending",
            notes=(
                f"Award created for {application.student.full_name} — "
                f"{application.scholarship.title}"
            ),
        )
        db.session.add(award)

    db.session.commit()
    return True, "Application approved and award record created"


def reject_application(application: Application) -> tuple[bool, str]:
    if application.status == "approved":
        return False, "Approved applications cannot be rejected"
    if application.status == "rejected":
        return False, "Application is already rejected"

    application.status = "rejected"
    application.date_reviewed = datetime.utcnow()
    db.session.commit()
    return True, "Application rejected"
