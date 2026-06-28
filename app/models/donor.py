from ..extensions import db


class Donor(db.Model):
    __tablename__ = "donors"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    donor_code = db.Column(db.String(20), unique=True)

    name = db.Column(db.String(128))
    donor_type = db.Column(db.String(64))  # Individual | Organization | Corporate
    contact_email = db.Column(db.String(128))
    contact_phone = db.Column(db.String(32))
    address = db.Column(db.String(256))

    profile_completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=db.func.now())

    user = db.relationship("User", back_populates="donor_profile")
    scholarships = db.relationship("Scholarship", back_populates="donor", lazy="dynamic")

    @property
    def display_name(self) -> str:
        return self.name or (self.user.username if self.user else "Unknown")

    def __repr__(self) -> str:
        return f"<Donor {self.display_name}>"
