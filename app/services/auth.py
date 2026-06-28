from ..extensions import db
from ..models.user import User
from ..models.student import Student
from ..models.donor import Donor
from ..utils.validators import validate_username, validate_password


def register_user(username: str, password: str, confirm: str, role: str) -> tuple[bool, str]:
    username = username.strip()

    ok, msg = validate_username(username)
    if not ok:
        return False, msg

    ok, msg = validate_password(password, confirm)
    if not ok:
        return False, msg

    if User.query.filter_by(username=username).first():
        return False, "Username is already taken"

    user = User(username=username, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.flush()

    if role == "student":
        profile = Student(
            user_id=user.id,
            student_code=f"STUD-{user.id:04d}",
            profile_completed=False,
        )
        db.session.add(profile)
    elif role == "donor":
        profile = Donor(
            user_id=user.id,
            donor_code=f"DONOR-{user.id:04d}",
            profile_completed=False,
        )
        db.session.add(profile)

    db.session.commit()
    return True, "Account created successfully. Please log in."


def authenticate(username: str, password: str, role: str):
    """Return User if credentials are valid for the given role, else None."""
    user = User.query.filter_by(username=username.strip(), role=role).first()
    if user and user.check_password(password):
        return user
    return None


def change_password(user: User, current_password: str, new_password: str, confirm: str) -> tuple[bool, str]:
    if not user.check_password(current_password):
        return False, "Current password is incorrect"
    ok, msg = validate_password(new_password, confirm)
    if not ok:
        return False, msg
    user.set_password(new_password)
    db.session.commit()
    return True, "Password updated successfully"


def change_username(user: User, new_username: str) -> tuple[bool, str]:
    new_username = new_username.strip()
    ok, msg = validate_username(new_username)
    if not ok:
        return False, msg
    if User.query.filter(User.username == new_username, User.id != user.id).first():
        return False, "Username is already taken"
    user.username = new_username
    db.session.commit()
    return True, "Username updated successfully"
