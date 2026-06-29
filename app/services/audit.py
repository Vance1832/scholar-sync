from flask_login import current_user
from ..extensions import db
from ..models.audit_log import AuditLog


def log(action: str, target_type: str = None, target_id: int = None, details: str = None):
    try:
        user_id = current_user.id if current_user and current_user.is_authenticated else None
        entry = AuditLog(
            user_id=user_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            details=details,
        )
        db.session.add(entry)
        db.session.commit()
    except Exception:
        db.session.rollback()
