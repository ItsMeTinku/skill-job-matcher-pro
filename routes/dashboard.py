"""
routes/dashboard.py — Dashboard blueprint
==========================================
Main user dashboard after login:
  - GET /dashboard         — show latest analysis results
  - GET /dashboard/jobs    — browse all jobs with category filter
  - GET /dashboard/profile — user profile page
"""

import logging

from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required, current_user

from extensions import db
from models.resume import Resume
from models.job import Job
from models.match import MatchResult

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")
logger = logging.getLogger(__name__)


# ── Main dashboard ────────────────────────────────────────────────────
@dashboard_bp.route("/", methods=["GET"])
@login_required
def index():
    """
    Show the user's latest resume analysis results.
    If no resume has been analysed yet, prompt them to upload one.
    """
    # Latest processed resume for this user
    latest_resume = (
        Resume.query
        .filter_by(user_id=current_user.id)
        .order_by(Resume.uploaded_at.desc())
        .first()
    )

    top_matches   = []
    all_skills    = []
    global_gap    = []
    total_resumes = Resume.query.filter_by(user_id=current_user.id).count()

    if latest_resume:
        all_skills = latest_resume.skills_list

        # Top 10 job matches by score
        top_matches = (
            MatchResult.query
            .filter_by(resume_id=latest_resume.id)
            .order_by(MatchResult.match_score.desc())
            .limit(10)
            .all()
        )

        # Aggregate missing skills across all matches (skill gap roadmap)
        global_gap = _compute_global_gap(latest_resume.id)

    # Category breakdown for the stats panel
    categories = (
        db.session.query(Job.category, db.func.count(Job.id))
        .filter_by(is_active=True)
        .group_by(Job.category)
        .all()
    )

    return render_template(
        "dashboard/index.html",
        latest_resume=latest_resume,
        top_matches=top_matches,
        all_skills=all_skills,
        global_gap=global_gap,
        total_resumes=total_resumes,
        categories=categories,
        total_jobs=Job.query.filter_by(is_active=True).count(),
    )


# ── Job browser ───────────────────────────────────────────────────────
@dashboard_bp.route("/jobs", methods=["GET"])
@login_required
def jobs():
    """Browse all job listings, optionally filtered by category or search term."""
    category = request.args.get("category", "").strip()
    search   = request.args.get("q", "").strip()
    page     = request.args.get("page", 1, type=int)

    query = Job.query.filter_by(is_active=True)

    if category:
        query = query.filter_by(category=category)

    if search:
        query = query.filter(Job.title.ilike(f"%{search}%"))

    jobs_page = query.order_by(Job.title).paginate(page=page, per_page=12, error_out=False)

    categories = (
        db.session.query(Job.category)
        .distinct()
        .order_by(Job.category)
        .all()
    )
    category_list = [c[0] for c in categories]

    return render_template(
        "dashboard/jobs.html",
        jobs_page=jobs_page,
        categories=category_list,
        selected_category=category,
        search_query=search,
    )


# ── User profile ──────────────────────────────────────────────────────
@dashboard_bp.route("/profile", methods=["GET"])
@login_required
def profile():
    """User profile — upload history and account info."""
    resumes = (
        Resume.query
        .filter_by(user_id=current_user.id)
        .order_by(Resume.uploaded_at.desc())
        .all()
    )
    return render_template("dashboard/profile.html", resumes=resumes)


# ── Helpers ───────────────────────────────────────────────────────────
def _compute_global_gap(resume_id: int, top_n: int = 10) -> list[str]:
    """
    Return the top-N most frequently missing skills across all matches
    for a given resume — a priority learning roadmap.
    """
    from collections import Counter

    results = (
        MatchResult.query
        .filter_by(resume_id=resume_id)
        .all()
    )

    counter: Counter = Counter()
    for r in results:
        for skill in r.missing_skills:
            counter[skill] += 1

    return [skill for skill, _ in counter.most_common(top_n)]
