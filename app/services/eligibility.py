"""
Eligibility checking logic — ported from check_student_eligibility() in the original monolith.
"""
from typing import Optional
from ..models.student import Student
from ..models.scholarship import Scholarship


def check_eligibility(student: Student, scholarship: Scholarship) -> tuple[bool, list[str]]:
    """
    Returns (is_eligible, list_of_unmet_reasons).
    An empty reasons list with eligible=True means all criteria are met.
    No criteria on the scholarship means everyone qualifies.
    """
    criteria = scholarship.criteria
    if not criteria:
        return True, []

    reasons = []

    if criteria.min_gpa:
        student_gpa = student.gpa_float
        if student_gpa < float(criteria.min_gpa):
            reasons.append(
                f"GPA requirement not met (need {criteria.min_gpa}, you have {student_gpa:.2f})"
            )

    if criteria.required_major and criteria.required_major not in ("", "Any Major"):
        student_major = (student.major or "").strip().lower()
        required = criteria.required_major.strip().lower()
        if student_major != required:
            reasons.append(
                f"Major requirement not met (need {criteria.required_major}, "
                f"you have {student.major or 'N/A'})"
            )

    return len(reasons) == 0, reasons


def match_score(student: Optional[Student], scholarship: Scholarship) -> Optional[int]:
    """
    Percentage of verifiable eligibility checks the student passes (0–100).
    Only GPA and major can be verified from the profile; need-based and
    free-text criteria are self-attested at application time and excluded.
    No verifiable criteria means the scholarship is open — 100.
    Returns None when there is no completed profile to score against.
    """
    if student is None or not student.profile_completed:
        return None

    criteria = scholarship.criteria
    if not criteria:
        return 100

    checks: list[bool] = []
    if criteria.min_gpa:
        checks.append(student.gpa_float >= float(criteria.min_gpa))
    if criteria.required_major and criteria.required_major not in ("", "Any Major"):
        checks.append(
            (student.major or "").strip().lower() == criteria.required_major.strip().lower()
        )

    if not checks:
        return 100
    return round(100 * sum(checks) / len(checks))


def eligibility_summary(student: Optional[Student], scholarship: Scholarship) -> dict:
    """
    Returns a dict with keys: eligible, reasons, label, css_class, match_pct.
    Safe to call with student=None (e.g. incomplete profile).
    """
    if student is None or not student.profile_completed:
        return {
            "eligible": None,
            "reasons": [],
            "label": "Complete your profile to check eligibility",
            "css_class": "status-neutral",
            "match_pct": None,
        }

    eligible, reasons = check_eligibility(student, scholarship)
    pct = match_score(student, scholarship)

    if eligible:
        return {
            "eligible": True,
            "reasons": [],
            "label": "You meet all requirements",
            "css_class": "status-success",
            "match_pct": pct,
        }
    return {
        "eligible": False,
        "reasons": reasons,
        "label": "You may not meet all requirements",
        "css_class": "status-warning",
        "match_pct": pct,
    }
