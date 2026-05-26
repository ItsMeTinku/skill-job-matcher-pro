"""
models/match.py — Match result model
======================================
Stores the output of semantic AI matching:
  - cosine similarity score
  - matched skills
  - missing skills (skill gap)
"""

import json
from datetime import datetime
from extensions import db


class MatchResult(db.Model):
    """Result of matching a specific resume against a specific job."""

    __tablename__ = "match_results"

    # ── Primary key ───────────────────────────────────────────────────
    id = db.Column(db.Integer, primary_key=True)

    # ── Foreign keys ──────────────────────────────────────────────────
    resume_id = db.Column(db.Integer, db.ForeignKey("resumes.id"), nullable=False, index=True)
    job_id    = db.Column(db.Integer, db.ForeignKey("jobs.id"),    nullable=False, index=True)

    # ── Scores ───────────────────────────────────────────────────────
    match_score        = db.Column(db.Float, nullable=False)   # 0.0 – 100.0
    semantic_score     = db.Column(db.Float, nullable=True)    # raw cosine 0–1
    keyword_score      = db.Column(db.Float, nullable=True)    # keyword overlap %

    # ── Gap analysis stored as JSON ───────────────────────────────────
    _matched_skills = db.Column("matched_skills", db.Text, default="[]")
    _missing_skills = db.Column("missing_skills", db.Text, default="[]")

    # ── Timestamps ────────────────────────────────────────────────────
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # ── Relationships ─────────────────────────────────────────────────
    resume = db.relationship("Resume", back_populates="matches")
    job    = db.relationship("Job",    back_populates="matches")

    # ── JSON helpers ─────────────────────────────────────────────────
    @property
    def matched_skills(self) -> list[str]:
        try:
            return json.loads(self._matched_skills)
        except (TypeError, ValueError):
            return []

    @matched_skills.setter
    def matched_skills(self, skills: list[str]) -> None:
        self._matched_skills = json.dumps(skills)

    @property
    def missing_skills(self) -> list[str]:
        try:
            return json.loads(self._missing_skills)
        except (TypeError, ValueError):
            return []

    @missing_skills.setter
    def missing_skills(self, skills: list[str]) -> None:
        self._missing_skills = json.dumps(skills)

    # ── Display helpers ───────────────────────────────────────────────
    @property
    def score_int(self) -> int:
        return int(round(self.match_score))

    @property
    def score_label(self) -> str:
        if self.match_score >= 75:
            return "Excellent"
        if self.match_score >= 55:
            return "Good"
        if self.match_score >= 35:
            return "Fair"
        return "Low"

    @property
    def score_badge_class(self) -> str:
        if self.match_score >= 75:
            return "badge-excellent"
        if self.match_score >= 55:
            return "badge-good"
        if self.match_score >= 35:
            return "badge-fair"
        return "badge-low"

    @property
    def progress_class(self) -> str:
        if self.match_score >= 75:
            return "progress-excellent"
        if self.match_score >= 55:
            return "progress-good"
        if self.match_score >= 35:
            return "progress-fair"
        return "progress-low"

    def __repr__(self) -> str:
        return f"<MatchResult resume={self.resume_id} job={self.job_id} score={self.match_score:.1f}>"
