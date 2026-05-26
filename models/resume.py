"""
models/resume.py — Resume model
================================
Stores uploaded resume metadata, extracted text, and parsed skills.
"""

from datetime import datetime
from extensions import db


class Resume(db.Model):
    """An uploaded resume file and its parsed content."""

    __tablename__ = "resumes"

    # ── Primary key ───────────────────────────────────────────────────
    id = db.Column(db.Integer, primary_key=True)

    # ── Foreign key ───────────────────────────────────────────────────
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    # ── File metadata ─────────────────────────────────────────────────
    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename   = db.Column(db.String(255), nullable=False)   # sanitised name on disk
    file_type         = db.Column(db.String(10),  nullable=False)   # "pdf" or "docx"
    file_size_bytes   = db.Column(db.Integer,     nullable=True)

    # ── Parsed content ────────────────────────────────────────────────
    raw_text          = db.Column(db.Text,  nullable=True)
    extracted_skills  = db.Column(db.Text,  nullable=True)   # comma-separated
    education_info    = db.Column(db.Text,  nullable=True)
    certifications    = db.Column(db.Text,  nullable=True)

    # ── Timestamps ────────────────────────────────────────────────────
    uploaded_at   = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    processed_at  = db.Column(db.DateTime, nullable=True)

    # ── Relationships ─────────────────────────────────────────────────
    user    = db.relationship("User",        back_populates="resumes")
    matches = db.relationship(
        "MatchResult",
        back_populates="resume",
        cascade="all, delete-orphan",
        lazy="dynamic",
        order_by="MatchResult.match_score.desc()",
    )

    # ── Helpers ───────────────────────────────────────────────────────
    @property
    def skills_list(self) -> list[str]:
        """Return extracted skills as a sorted list."""
        if not self.extracted_skills:
            return []
        return sorted({s.strip() for s in self.extracted_skills.split(",") if s.strip()})

    @property
    def top_matches(self):
        """Return top 10 job matches ordered by score descending."""
        return self.matches.limit(10).all()

    def __repr__(self) -> str:
        return f"<Resume {self.original_filename} user={self.user_id}>"
