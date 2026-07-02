from ..extensions import db


class SavedScholarship(db.Model):
    __tablename__ = "saved_scholarships"
    __table_args__ = (
        db.UniqueConstraint("student_id", "scholarship_id", name="uq_saved_student_scholarship"),
    )

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    scholarship_id = db.Column(db.Integer, db.ForeignKey("scholarships.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.now())

    student = db.relationship("Student", backref=db.backref("saved_scholarships", lazy="dynamic"))
    scholarship = db.relationship("Scholarship")

    def __repr__(self) -> str:
        return f"<SavedScholarship student={self.student_id} scholarship={self.scholarship_id}>"
