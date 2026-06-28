from datetime import date
from typing import Optional


def validate_gpa(value: str) -> tuple[bool, Optional[float], str]:
    """Return (is_valid, float_value, error_message)."""
    if not value or not value.strip():
        return True, None, ""
    try:
        gpa = float(value.strip())
    except ValueError:
        return False, None, "GPA must be a number (e.g. 3.50)"
    if not (0.0 <= gpa <= 4.0):
        return False, None, "GPA must be between 0.0 and 4.0"
    return True, gpa, ""


def validate_amount(value: str) -> tuple[bool, Optional[float], str]:
    if not value or not value.strip():
        return False, None, "Amount is required"
    try:
        amount = float(value.strip())
    except ValueError:
        return False, None, "Amount must be a number"
    if amount <= 0:
        return False, None, "Amount must be greater than 0"
    return True, amount, ""


def validate_deadline(value: str) -> tuple[bool, Optional[date], str]:
    if not value or not value.strip():
        return True, None, ""
    try:
        from datetime import datetime
        deadline = datetime.strptime(value.strip(), "%Y-%m-%d").date()
    except ValueError:
        return False, None, "Deadline must be in YYYY-MM-DD format"
    if deadline < date.today():
        return False, None, "Deadline cannot be in the past"
    return True, deadline, ""


def validate_password(password: str, confirm: str = None) -> tuple[bool, str]:
    if len(password) < 6:
        return False, "Password must be at least 6 characters"
    if confirm is not None and password != confirm:
        return False, "Passwords do not match"
    return True, ""


def validate_username(username: str) -> tuple[bool, str]:
    if len(username) < 3:
        return False, "Username must be at least 3 characters"
    if len(username) > 64:
        return False, "Username must be under 64 characters"
    return True, ""


def validate_application_message(message: str) -> tuple[bool, str]:
    if not message or len(message.strip()) < 50:
        return False, "Application statement must be at least 50 characters"
    return True, ""
