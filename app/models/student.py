from ..extensions import db


class Student(db.Model):
    __tablename__ = "students"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    student_code = db.Column(db.String(20), unique=True)

    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    email = db.Column(db.String(128))
    phone = db.Column(db.String(32))
    address = db.Column(db.String(256))
    date_of_birth = db.Column(db.Date)

    major = db.Column(db.String(100))
    gpa = db.Column(db.Numeric(3, 2))
    academic_year = db.Column(db.String(32))
    department = db.Column(db.String(100))

    profile_completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=db.func.now())

    user = db.relationship("User", back_populates="student_profile")
    applications = db.relationship("Application", back_populates="student", lazy="dynamic")

    @property
    def full_name(self) -> str:
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.user.username if self.user else "Unknown"

    @property
    def gpa_float(self) -> float:
        return float(self.gpa) if self.gpa is not None else 0.0

    def __repr__(self) -> str:
        return f"<Student {self.full_name}>"
