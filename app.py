"""
Skill & Job Matcher — Production Flask Application
===================================================
Entry point for the AI-powered recruitment platform.
Registers blueprints, extensions, and error handlers.
"""

import os
from flask import Flask, render_template, redirect, url_for
from extensions import db, limiter, login_manager
from config import get_config


def create_app(config_name: str = None) -> Flask:
    """Application factory — creates and configures the Flask app."""

    app = Flask(__name__, instance_relative_config=True)

    # ── Configuration ────────────────────────────────────────────────
    cfg = get_config(config_name or os.getenv("FLASK_ENV", "production"))
    app.config.from_object(cfg)

    # Ensure the upload folder exists
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.instance_path, exist_ok=True)

    # ── Extensions ───────────────────────────────────────────────────
    db.init_app(app)
    limiter.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to access this page."
    login_manager.login_message_category = "warning"

    # ── Database tables ──────────────────────────────────────────────
    with app.app_context():
        from models import user, resume, job, match  # noqa: F401 — register models
        db.create_all()
        _seed_jobs_if_empty()

    # ── Blueprints ───────────────────────────────────────────────────
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.analysis import analysis_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(analysis_bp)

    # ── Error handlers ───────────────────────────────────────────────
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_error(e):
        db.session.rollback()
        return render_template("errors/500.html"), 500

    @app.errorhandler(429)
    def rate_limit_error(e):
        return render_template(
            "errors/429.html",
            message="Too many requests. Please slow down and try again shortly."
        ), 429

    @app.route("/")
    def index():
        return redirect(url_for("auth.login"))

    return app


def _seed_jobs_if_empty():
    """Seed the jobs table from the static dataset if it is empty."""
    from models.job import Job
    from data.jobs import JOB_DATASET

    if Job.query.count() == 0:
        for entry in JOB_DATASET:
            job = Job(
                title=entry["title"],
                description=entry["description"],
                required_skills=entry["required_skills"],
                category=entry["category"],
                experience_level=entry["experience_level"],
            )
            db.session.add(job)
        db.session.commit()


# ── WSGI entry point ─────────────────────────────────────────────────
app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
