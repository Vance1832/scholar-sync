from flask import current_app
from flask_mail import Message
from ..extensions import mail


def _send(subject: str, recipient: str, body: str, html: str = None):
    if not recipient:
        return
    try:
        msg = Message(subject=subject, recipients=[recipient], body=body, html=html)
        mail.send(msg)
    except Exception as e:
        current_app.logger.warning(f"Email failed to {recipient}: {e}")


def send_application_received(application):
    student = application.student
    sch = application.scholarship
    if not student.email:
        return
    _send(
        subject=f"Application Received – {sch.title}",
        recipient=student.email,
        body=(
            f"Hi {student.first_name},\n\n"
            f"Your application for {sch.title} has been received and is now under review.\n\n"
            f"Award amount: {sch.amount}\n"
            f"Donor: {sch.donor.display_name}\n\n"
            f"You will be notified when a decision is made.\n\n"
            f"— ScholarSync"
        ),
    )


def send_shortlisted(application):
    student = application.student
    sch = application.scholarship
    if not student.email:
        return
    _send(
        subject=f"You've Been Shortlisted – {sch.title}",
        recipient=student.email,
        body=(
            f"Hi {student.first_name},\n\n"
            f"Great news! Your application for {sch.title} has been shortlisted.\n\n"
            f"The donor is now making their final selection. "
            f"We will notify you once a decision has been made.\n\n"
            f"— ScholarSync"
        ),
    )


def send_awarded(application):
    student = application.student
    sch = application.scholarship
    if not student.email:
        return
    _send(
        subject=f"Congratulations! You've Been Awarded – {sch.title}",
        recipient=student.email,
        body=(
            f"Hi {student.first_name},\n\n"
            f"Congratulations! You have been selected to receive the {sch.title} scholarship "
            f"worth {sch.amount}.\n\n"
            f"Please log in to ScholarSync to accept your award and provide your payment details. "
            f"You must accept within 7 days or the award may be reallocated.\n\n"
            f"— ScholarSync"
        ),
    )


def send_rejected(application):
    student = application.student
    sch = application.scholarship
    if not student.email:
        return
    _send(
        subject=f"Application Update – {sch.title}",
        recipient=student.email,
        body=(
            f"Hi {student.first_name},\n\n"
            f"Thank you for applying for {sch.title}. After careful consideration, "
            f"your application was not selected this time.\n\n"
            f"We encourage you to continue applying for other scholarships on ScholarSync.\n\n"
            f"— ScholarSync"
        ),
    )


def send_disbursement_confirmed(award):
    student = award.student
    sch = award.scholarship
    if not student.email:
        return
    _send(
        subject=f"Payment Confirmed – {sch.title}",
        recipient=student.email,
        body=(
            f"Hi {student.first_name},\n\n"
            f"Your scholarship payment of {award.amount} for {sch.title} has been confirmed.\n\n"
            f"Reference: {award.payment_reference or 'N/A'}\n\n"
            f"Thank you for being part of ScholarSync.\n\n"
            f"— ScholarSync"
        ),
    )


def send_award_accepted_to_donor(award):
    donor = award.scholarship.donor
    student = award.student
    sch = award.scholarship
    if not donor.contact_email:
        return
    _send(
        subject=f"Award Accepted – {sch.title}",
        recipient=donor.contact_email,
        body=(
            f"Hi {donor.display_name},\n\n"
            f"{student.full_name} has accepted the {sch.title} award.\n\n"
            f"Please log in to ScholarSync to initiate the disbursement.\n\n"
            f"— ScholarSync"
        ),
    )
