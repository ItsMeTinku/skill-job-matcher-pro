"""
models/user_skill.py — UserSkill model
=====================================
Stores manual skills added by users, optionally attached to a specific resume.
"""
from datetime import datetime
from extensions import db


class UserSkill(db.Model):
    __tablename__ = "user_skills"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    resume_id = db.Column(db.Integer, db.ForeignKey("resumes.id"), nullable=True, index=True)
    skill_name = db.Column(db.String(200), nullable=False, index=True)
    source = db.Column(db.String(20), default="manual", nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # relationships
    user = db.relationship("User", back_populates="manual_skills")

    def __repr__(self) -> str:
        return f"<UserSkill {self.skill_name} user={self.user_id} resume={self.resume_id}>"
