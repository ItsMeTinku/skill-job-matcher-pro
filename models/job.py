"""
models/job.py — Job listing model
===================================
Stores job titles, descriptions, required skills, and category.
The table is seeded once from data/jobs.py on first run.
"""

import json
from datetime import datetime
from extensions import db


class Job(db.Model):
    """A job listing against which resumes are semantically matched."""

    __tablename__ = "jobs"

    # ── Primary key ───────────────────────────────────────────────────
    id = db.Column(db.Integer, primary_key=True)

    # ── Job details ───────────────────────────────────────────────────
    title            = db.Column(db.String(200), nullable=False, index=True)
    description      = db.Column(db.Text,        nullable=False)
    category         = db.Column(db.String(100), nullable=False, index=True)
    experience_level = db.Column(db.String(50),  nullable=True)   # Junior/Mid/Senior

    # ── Skills stored as JSON array string ───────────────────────────
    _required_skills = db.Column("required_skills", db.Text, nullable=False, default="[]")

    # ── Timestamps ────────────────────────────────────────────────────
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    is_active  = db.Column(db.Boolean,  default=True, nullable=False)

    # ── Relationships ─────────────────────────────────────────────────
    matches = db.relationship(
        "MatchResult",
        back_populates="job",
        lazy="dynamic",
    )

    # ── required_skills property (JSON <-> list) ──────────────────────
    @property
    def required_skills(self) -> list[str]:
        try:
            return json.loads(self._required_skills)
        except (TypeError, ValueError):
            return []

    @required_skills.setter
    def required_skills(self, skills: list[str]) -> None:
        self._required_skills = json.dumps([s.lower().strip() for s in skills])

    # ── Helpers ───────────────────────────────────────────────────────
    @property
    def skills_text(self) -> str:
        """Comma-separated skills string for display."""
        return ", ".join(self.required_skills)

    @property
    def badge_class(self) -> str:
        """Bootstrap badge class for experience level."""
        mapping = {"Junior": "success", "Mid": "primary", "Senior": "warning"}
        return mapping.get(self.experience_level, "secondary")

    def __repr__(self) -> str:
        return f"<Job {self.title}>"
