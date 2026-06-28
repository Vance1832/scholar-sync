from ..extensions import db


class Application(db.Model):
    __tablename__ = "applications"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    scholarship_id = db.Column(db.Integer, db.ForeignKey("scholarships.id"), nullable=False)

    status = db.Column(db.String(16), default="pending")  # pending | approved | rejected | withdrawn
    # Structured application fields
    personal_statement = db.Column(db.Text)       # Why I deserve this scholarship
    financial_need = db.Column(db.Text)           # Financial situation / need
    intended_use = db.Column(db.Text)             # How funds will be used
    # Legacy field kept for backward compat
    application_message = db.Column(db.Text)
    # Review fields
    rejection_reason = db.Column(db.Text)         # Required when rejecting
    reviewer_notes = db.Column(db.Text)           # Internal notes by reviewer
    date_applied = db.Column(db.DateTime, default=db.func.now())
    date_reviewed = db.Column(db.DateTime)

    student = db.relationship("Student", back_populates="applications")
    scholarship = db.relationship("Scholarship", back_populates="applications")
    award = db.relationship("Award", back_populates="application", uselist=False)

    @property
    def status_label(self) -> str:
        labels = {
            "pending": "Pending",
            "approved": "Approved",
            "rejected": "Rejected",
            "withdrawn": "Withdrawn",
        }
        return labels.get(self.status, self.status.title())

    def __repr__(self) -> str:
        return f"<Application {self.id} [{self.status}]>"
