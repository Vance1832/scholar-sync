from ..extensions import db


class Application(db.Model):
    __tablename__ = "applications"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    scholarship_id = db.Column(db.Integer, db.ForeignKey("scholarships.id"), nullable=False)

    status = db.Column(db.String(16), default="pending")  # pending | approved | rejected | withdrawn
    application_message = db.Column(db.Text)
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
