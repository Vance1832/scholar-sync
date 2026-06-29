from ..extensions import db


class EligibilityCriteria(db.Model):
    __tablename__ = "eligibility_criteria"

    id = db.Column(db.Integer, primary_key=True)
    scholarship_id = db.Column(
        db.Integer, db.ForeignKey("scholarships.id"), unique=True, nullable=False
    )
    min_gpa = db.Column(db.Numeric(3, 2))
    required_major = db.Column(db.String(100))
    need_based = db.Column(db.Boolean, default=False)
    criterion_text = db.Column(db.Text)

    scholarship = db.relationship("Scholarship", back_populates="criteria")

    def as_display_string(self) -> str:
        parts = []
        if self.min_gpa:
            parts.append(f"GPA ≥ {self.min_gpa}")
        if self.required_major and self.required_major != "Any Major":
            parts.append(f"{self.required_major} major")
        if self.need_based:
            parts.append("Financial need required")
        if self.criterion_text:
            parts.append(self.criterion_text)
        return ", ".join(parts) if parts else "Open to all students"


class Scholarship(db.Model):
    __tablename__ = "scholarships"

    id = db.Column(db.Integer, primary_key=True)
    donor_id = db.Column(db.Integer, db.ForeignKey("donors.id"), nullable=False)

    title = db.Column(db.String(256), nullable=False)
    description = db.Column(db.Text)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    deadline = db.Column(db.Date)
    is_active = db.Column(db.Boolean, default=True)
    slots = db.Column(db.Integer, default=1)
    category = db.Column(db.String(64))
    effort_level = db.Column(db.String(16), default="essay")  # easy | essay | detailed
    created_at = db.Column(db.DateTime, default=db.func.now())

    donor = db.relationship("Donor", back_populates="scholarships")
    criteria = db.relationship(
        "EligibilityCriteria", back_populates="scholarship", uselist=False, cascade="all, delete-orphan"
    )
    applications = db.relationship("Application", back_populates="scholarship", lazy="dynamic")

    @property
    def amount_float(self) -> float:
        return float(self.amount) if self.amount is not None else 0.0

    @property
    def application_count(self) -> int:
        return self.applications.count()

    @property
    def pending_count(self) -> int:
        return self.applications.filter_by(status="pending").count()

    def __repr__(self) -> str:
        return f"<Scholarship {self.title}>"
