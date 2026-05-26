"""
config.py — Environment-based configuration
============================================
Three configuration classes:
  - DevelopmentConfig  (local dev, DEBUG=True, SQLite fallback allowed)
  - ProductionConfig   (Supabase PostgreSQL, strict security)
  - TestingConfig      (in-memory SQLite for unit tests)

Usage:
    FLASK_ENV=production python app.py
    FLASK_ENV=development flask run
"""

import os
from dotenv import load_dotenv

# Load .env file if present (local development)
load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class BaseConfig:
    """Shared settings across all environments."""

    # ── Security ─────────────────────────────────────────────────────
    SECRET_KEY = os.getenv("SECRET_KEY", os.urandom(32).hex())
    WTF_CSRF_ENABLED = True

    # ── File uploads ─────────────────────────────────────────────────
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024   # 10 MB max upload
    ALLOWED_EXTENSIONS = {"pdf", "docx"}

    # ── SQLAlchemy ────────────────────────────────────────────────────
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }

    # ── Session ───────────────────────────────────────────────────────
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour

    # ── AI Model ──────────────────────────────────────────────────────
    SENTENCE_TRANSFORMER_MODEL = "all-MiniLM-L6-v2"

    # ── Rate limiting ─────────────────────────────────────────────────
    RATELIMIT_LOGIN = "5 per minute"
    RATELIMIT_REGISTER = "3 per minute"
    RATELIMIT_UPLOAD = "10 per hour"


class DevelopmentConfig(BaseConfig):
    """Local development configuration."""

    DEBUG = True
    TESTING = False
    SESSION_COOKIE_SECURE = False

    # Prefer DATABASE_URL from .env; fall back to local PostgreSQL
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/skill_job_matcher_dev"
    )


class ProductionConfig(BaseConfig):
    """Production configuration — Supabase PostgreSQL."""

    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True  # HTTPS only

    _db_url = os.getenv("DATABASE_URL", "")

    # Supabase / Heroku supply postgres:// but SQLAlchemy needs postgresql://
    if _db_url.startswith("postgres://"):
        _db_url = _db_url.replace("postgres://", "postgresql://", 1)

    SQLALCHEMY_DATABASE_URI = _db_url

    # Tighter pool for production
    SQLALCHEMY_ENGINE_OPTIONS = {
        **BaseConfig.SQLALCHEMY_ENGINE_OPTIONS,
        "pool_size": 5,
        "max_overflow": 10,
    }


class TestingConfig(BaseConfig):
    """Unit-test configuration — in-memory SQLite."""

    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False


_CONFIG_MAP = {
    "development": DevelopmentConfig,
    "production":  ProductionConfig,
    "testing":     TestingConfig,
}


def get_config(env_name: str = "production"):
    """Return the correct config class for the given environment name."""
    return _CONFIG_MAP.get(env_name.lower(), ProductionConfig)
