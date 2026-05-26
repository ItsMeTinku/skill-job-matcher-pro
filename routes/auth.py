"""
routes/auth.py — Authentication blueprint
==========================================
Handles:
  - User registration  (POST /register)
  - Login              (POST /login)    ← rate-limited: 5/min
  - Logout             (GET  /logout)

Security measures:
  - Werkzeug password hashing (pbkdf2:sha256)
  - Flask-Limiter brute-force protection on login
  - Input sanitisation and email validation
  - No plain-text secrets ever stored
"""

import re
import logging
from datetime import datetime

from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash,
)
from flask_login import login_user, logout_user, login_required, current_user

from extensions import db, limiter
from models.user import User

auth_bp = Blueprint("auth", __name__)
logger  = logging.getLogger(__name__)

_EMAIL_RE = re.compile(r"^[\w\.\+\-]+@[\w\-]+\.[a-z]{2,}$", re.IGNORECASE)


# ── Registration ─────────────────────────────────────────────────────
@auth_bp.route("/register", methods=["GET", "POST"])
@limiter.limit("3 per minute")
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email     = request.form.get("email", "").strip().lower()
        password  = request.form.get("password", "")
        confirm   = request.form.get("confirm_password", "")

        # ── Validation ────────────────────────────────────────────────
        errors = []

        if not full_name or len(full_name) < 2:
            errors.append("Full name must be at least 2 characters.")

        if not _EMAIL_RE.match(email):
            errors.append("Please enter a valid email address.")

        if len(password) < 8:
            errors.append("Password must be at least 8 characters.")

        if password != confirm:
            errors.append("Passwords do not match.")

        if errors:
            for err in errors:
                flash(err, "danger")
            return render_template(
                "auth/register.html",
                full_name=full_name,
                email=email,
            )

        # ── Duplicate check ───────────────────────────────────────────
        if User.query.filter_by(email=email).first():
            flash("An account with this email already exists. Please log in.", "warning")
            return redirect(url_for("auth.login"))

        # ── Create user ───────────────────────────────────────────────
        user = User(full_name=full_name, email=email)
        user.set_password(password)

        try:
            db.session.add(user)
            db.session.commit()
            logger.info("New user registered: %s", email)
            flash("Account created! Please log in.", "success")
            return redirect(url_for("auth.login"))
        except Exception as exc:
            db.session.rollback()
            logger.error("Registration DB error: %s", exc)
            flash("Registration failed due to a server error. Please try again.", "danger")

    return render_template("auth/register.html")


# ── Login ─────────────────────────────────────────────────────────────
@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Please enter both email and password.", "danger")
            return render_template("auth/login.html", email=email)

        user = User.query.filter_by(email=email).first()

        if user is None or not user.check_password(password):
            logger.warning("Failed login attempt for email: %s", email)
            flash("Invalid email or password.", "danger")
            return render_template("auth/login.html", email=email)

        if not user.is_active:
            flash("This account has been deactivated. Please contact support.", "warning")
            return render_template("auth/login.html", email=email)

        # ── Successful login ──────────────────────────────────────────
        user.last_login = datetime.utcnow()
        db.session.commit()

        login_user(user, remember=False)
        logger.info("User logged in: %s", email)

        next_page = request.args.get("next")
        if next_page and next_page.startswith("/"):   # prevent open redirect
            return redirect(next_page)
        return redirect(url_for("dashboard.index"))

    return render_template("auth/login.html")


# ── Logout ────────────────────────────────────────────────────────────
@auth_bp.route("/logout")
@login_required
def logout():
    logger.info("User logged out: %s", current_user.email)
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))
