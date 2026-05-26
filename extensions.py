"""
extensions.py — Flask extension singletons
==========================================
All extensions are instantiated here (without an app) and later
initialised inside the application factory via .init_app().
This pattern prevents circular imports between app.py, models, and routes.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import LoginManager

# ── SQLAlchemy ORM ────────────────────────────────────────────────────────
db = SQLAlchemy()

# ── Rate limiter (brute-force protection) ────────────────────────────────
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",          # swap for redis:// in production
)

# ── Flask-Login ───────────────────────────────────────────────────────────
login_manager = LoginManager()
