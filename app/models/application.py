from ..extensions import db


class Application(db.Model):
    __tablename__ = "applications"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    scholarship_id = db.Column(db.Integer, db.ForeignKey("scholarships.id"), nullable=False)

    status = db.Column(db.String(16), default="pending")  # pending | shortlisted | approved | rejected | withdrawn
    # Structured application fields
    personal_statement = db.Column(db.Text)
    financial_need = db.Column(db.Text)
    intended_use = db.Column(db.Text)
    application_message = db.Column(db.Text)
    # Review fields
    rejection_reason = db.Column(db.Text)
    reviewer_notes = db.Column(db.Text)
    star_rating = db.Column(db.Integer)           # 1–5, donor-only, never shown to student
    date_applied = db.Column(db.DateTime, default=db.func.now())
    date_reviewed = db.Column(db.DateTime)

    student = db.relationship("Student", back_populates="applications")
    scholarship = db.relationship("Scholarship", back_populates="applications")
    award = db.relationship("Award", back_populates="application", uselist=False)

    @property
    def status_label(self) -> str:
        labels = {
            "pending": "Under Review",
            "shortlisted": "Shortlisted",
            "approved": "Awarded",
            "rejected": "Not Selected",
            "withdrawn": "Withdrawn",
        }
        return labels.get(self.status, self.status.title())

    @property
    def status_step(self) -> int:
        """1-4 pipeline step for the visual tracker shown to students."""
        return {"pending": 2, "shortlisted": 3, "approved": 4, "rejected": 4, "withdrawn": 1}.get(self.status, 1)

    def __repr__(self) -> str:
        return f"<Application {self.id} [{self.status}]>"
