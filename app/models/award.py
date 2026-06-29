from ..extensions import db


class Award(db.Model):
    __tablename__ = "awards"

    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey("applications.id"), unique=True, nullable=False)

    amount = db.Column(db.Numeric(12, 2), nullable=False)
    award_date = db.Column(db.Date, default=db.func.current_date())
    payment_status = db.Column(db.String(24), default="pending_acceptance")  # pending_acceptance | accepted | processing | completed | failed | cancelled
    payment_method = db.Column(db.String(64))
    payment_reference = db.Column(db.String(256))
    recipient_account = db.Column(db.String(512))
    disbursement_date = db.Column(db.Date)
    notes = db.Column(db.Text)
    disbursement_proof = db.Column(db.Text)
    student_accepted = db.Column(db.Boolean, default=False)
    student_payment_info = db.Column(db.Text)
    accepted_at = db.Column(db.DateTime)

    application = db.relationship("Application", back_populates="award")

    @property
    def amount_float(self) -> float:
        return float(self.amount) if self.amount is not None else 0.0

    @property
    def student(self):
        return self.application.student if self.application else None

    @property
    def scholarship(self):
        return self.application.scholarship if self.application else None

    def __repr__(self) -> str:
        return f"<Award {self.id} [{self.payment_status}]>"
