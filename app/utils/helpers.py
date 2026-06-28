from datetime import date
from typing import Optional


def format_currency(value) -> str:
    try:
        return f"${float(value):,.2f}"
    except (TypeError, ValueError):
        return "$0.00"


def format_date(value, fmt: str = "%b %d, %Y") -> str:
    if value is None:
        return "—"
    if hasattr(value, "strftime"):
        return value.strftime(fmt)
    return str(value)


def days_until(deadline: Optional[date]) -> Optional[int]:
    if deadline is None:
        return None
    return (deadline - date.today()).days


def is_expired(deadline: Optional[date]) -> bool:
    if deadline is None:
        return False
    return deadline < date.today()


MAJORS = [
    "Computer Science",
    "Engineering",
    "Business Administration",
    "Nursing",
    "Education",
    "Biology",
    "Mathematics",
    "Psychology",
    "Communications",
    "Arts",
    "Physics",
    "Chemistry",
    "Economics",
    "Political Science",
    "History",
    "English Literature",
    "Medicine",
    "Law",
    "Architecture",
    "Other",
]

DONOR_TYPES = ["Individual", "Organization", "Corporate Foundation", "Non-Profit", "Government"]

ACADEMIC_YEARS = ["Freshman", "Sophomore", "Junior", "Senior", "Graduate", "PhD"]

PAYMENT_METHODS = ["Bank Transfer", "Check", "Direct Deposit", "Cash", "Other"]
