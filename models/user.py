"""
models/user.py — User model
============================
Represents an authenticated user of the platform.
Passwords are stored as Werkzeug bcrypt hashes — never plain text.
"""

from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from extensions import db, login_manager


class User(UserMixin, db.Model):
    """Platform user — recruiter, candidate, or admin."""

    __tablename__ = "users"

    # ── Primary key ───────────────────────────────────────────────────
    id = db.Column(db.Integer, primary_key=True)

    # ── Identity ──────────────────────────────────────────────────────
    full_name = db.Column(db.String(120), nullable=False)
    email     = db.Column(db.String(254), unique=True, nullable=False, index=True)

    # ── Security ──────────────────────────────────────────────────────
    password_hash = db.Column(db.String(256), nullable=False)

    # ── Metadata ──────────────────────────────────────────────────────
    created_at  = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_login  = db.Column(db.DateTime, nullable=True)
    is_active   = db.Column(db.Boolean, default=True, nullable=False)

    # ── Relationships ─────────────────────────────────────────────────
    resumes = db.relationship(
        "Resume",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="dynamic",
        order_by="Resume.uploaded_at.desc()",
    )

    # ── Manual skills added by the user (UserSkill model)
    manual_skills = db.relationship(
        "UserSkill",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="dynamic",
        order_by="UserSkill.created_at.desc()",
    )

    # ── Password helpers ──────────────────────────────────────────────
    def set_password(self, plain_text: str) -> None:
        """Hash and store *plain_text*. Never store raw passwords."""
        self.password_hash = generate_password_hash(plain_text)

    def check_password(self, plain_text: str) -> bool:
        """Return True when *plain_text* matches the stored hash."""
        return check_password_hash(self.password_hash, plain_text)

    # ── Flask-Login required ──────────────────────────────────────────
    def get_id(self) -> str:
        return str(self.id)

    # ── Helpers ───────────────────────────────────────────────────────
    @property
    def first_name(self) -> str:
        return self.full_name.split()[0] if self.full_name else "User"

    @property
    def latest_resume(self):
        return self.resumes.first()

    def __repr__(self) -> str:
        return f"<User {self.email}>"


# ── Flask-Login user loader ───────────────────────────────────────────
@login_manager.user_loader
def load_user(user_id: str):
    return db.session.get(User, int(user_id))
