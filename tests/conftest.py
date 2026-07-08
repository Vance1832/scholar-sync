import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

os.environ.setdefault("ADMIN_PASSWORD", "test-admin-password")

from app import create_app
from app.extensions import db as _db


@pytest.fixture()
def app():
    app = create_app("testing")
    with app.app_context():
        yield app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture()
def db(app):
    return _db


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def donor(db):
    from app.models.user import User
    from app.models.donor import Donor

    user = User(username="testdonor", role="donor")
    user.set_password("password123")
    db.session.add(user)
    db.session.flush()
    profile = Donor(
        user_id=user.id, donor_code="DONOR-9001",
        name="Test Foundation", donor_type="Non-Profit", profile_completed=True,
    )
    db.session.add(profile)
    db.session.commit()
    return profile


@pytest.fixture()
def student(db):
    from app.models.user import User
    from app.models.student import Student

    user = User(username="teststudent", role="student")
    user.set_password("password123")
    db.session.add(user)
    db.session.flush()
    profile = Student(
        user_id=user.id, student_code="STUD-9001",
        first_name="Test", last_name="Student",
        major="Computer Science", gpa="3.60", academic_year="Junior",
        profile_completed=True,
    )
    db.session.add(profile)
    db.session.commit()
    return profile


@pytest.fixture()
def make_scholarship(db, donor):
    """Factory for scholarships owned by the test donor."""
    from datetime import date, timedelta
    from app.models.scholarship import Scholarship, EligibilityCriteria

    def _make(title="Test Award", amount=5000, days=30, category=None,
              effort="essay", is_active=True, min_gpa=None, required_major=None):
        sch = Scholarship(
            donor_id=donor.id, title=title, amount=amount,
            deadline=date.today() + timedelta(days=days) if days is not None else None,
            is_active=is_active, category=category, effort_level=effort,
        )
        db.session.add(sch)
        db.session.flush()
        if min_gpa or required_major:
            db.session.add(EligibilityCriteria(
                scholarship_id=sch.id, min_gpa=min_gpa, required_major=required_major,
            ))
        db.session.commit()
        return sch

    return _make
