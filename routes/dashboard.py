"""
routes/dashboard.py — Dashboard blueprint
==========================================
Main user dashboard after login:
  - GET /dashboard         — show latest analysis results
  - GET /dashboard/jobs    — browse all jobs with category filter
  - GET /dashboard/profile — user profile page
  - GET /dashboard/manual  — manual skills entry and matching
"""

import logging
import os

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user

from extensions import db
from models.resume import Resume
from models.job import Job
from models.match import MatchResult
from models.user_skill import UserSkill
from utils.skill_extractor import normalize_skill
from utils.matcher import match_resume_to_jobs
from flask import current_app

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


# ── User skills API / views ─────────────────────────────────────────
@dashboard_bp.route("/skills", methods=["GET"]) 
@login_required
def skills_view():
    """Show user's manual skills, optionally filtered by resume_id."""
    resume_id = request.args.get("resume_id", type=int)

    query = UserSkill.query.filter_by(user_id=current_user.id)
    if resume_id is not None:
        query = query.filter_by(resume_id=resume_id)

    skills = query.order_by(UserSkill.created_at.desc()).all()

    # Group by resume (None => Global)
    grouped = {}
    for s in skills:
        key = s.resume_id or "global"
        grouped.setdefault(key, []).append(s)

    resumes = (
        Resume.query
        .filter_by(user_id=current_user.id)
        .order_by(Resume.uploaded_at.desc())
        .all()
    )

    return render_template("dashboard/skills.html", grouped=grouped, resumes=resumes)


@dashboard_bp.route("/skills", methods=["POST"])
@login_required
def add_skill():
    """Add a manual skill for the current user. Accepts form or JSON."""
    # Accept JSON body or form data for progressive enhancement
    data = request.get_json(silent=True) or request.form
    raw_skill = (data.get("skill") or "").strip()
    resume_id = data.get("resume_id")
    if resume_id == "" or resume_id is None:
        resume_id = None
    else:
        try:
            resume_id = int(resume_id)
        except Exception:
            resume_id = None

    if not raw_skill:
        if request.is_json:
            return jsonify({"ok": False, "error": "empty skill"}), 400
        flash("Please enter a skill to add.", "warning")
        return redirect(url_for("dashboard.index"))

    skill = normalize_skill(raw_skill)

    us = UserSkill(user_id=current_user.id, resume_id=resume_id, skill_name=skill)
    db.session.add(us)
    try:
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        if request.is_json:
            return jsonify({"ok": False, "error": "db"}), 500
        flash("Failed to add skill. Please try again.", "danger")
        return redirect(url_for("dashboard.index"))

    if request.is_json:
        return jsonify({"ok": True, "skill": skill, "id": us.id})

    flash(f"Skill added: {skill}", "success")
    return redirect(url_for("dashboard.skills_view"))


@dashboard_bp.route("/skills/remove", methods=["POST"])
@login_required
def remove_skill():
    data = request.get_json(silent=True) or request.form
    skill_id = data.get("skill_id")
    if not skill_id:
        flash("Invalid request.", "danger")
        return redirect(url_for("dashboard.skills_view"))

    try:
        skill_id = int(skill_id)
    except Exception:
        flash("Invalid skill id.", "danger")
        return redirect(url_for("dashboard.skills_view"))

    us = UserSkill.query.get(skill_id)
    if not us or us.user_id != current_user.id:
        flash("Skill not found.", "warning")
        return redirect(url_for("dashboard.skills_view"))

    db.session.delete(us)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        flash("Failed to remove skill.", "danger")
        return redirect(url_for("dashboard.skills_view"))

    flash(f"Removed skill: {us.skill_name}", "success")
    return redirect(url_for("dashboard.skills_view"))



# ── Manual Matching (Dedicated Page) ──────────────────────────────────
@dashboard_bp.route('/manual', methods=['GET'])
@login_required
def manual():
    """
    Dedicated page for manual skill entry and matching.
    Display user's manual skills and recent matches based on those skills.
    """
    # Get user's manual skills
    manual_skills_data = UserSkill.query.filter_by(user_id=current_user.id).all()
    
    # Get user's resumes for dropdown
    resumes = (
        Resume.query
        .filter_by(user_id=current_user.id)
        .order_by(Resume.uploaded_at.desc())
        .all()
    )
    
    # Compute matches if there are manual skills
    match_results = []
    if manual_skills_data:
        manual_skills = [u.skill_name for u in manual_skills_data]
        jobs = Job.query.filter_by(is_active=True).all()
        
        if jobs:
            try:
                match_results = match_resume_to_jobs(
                    resume_text="",
                    resume_skills=manual_skills,
                    jobs=jobs,
                    model_name=current_app.config.get(
                        "SENTENCE_TRANSFORMER_MODEL", "all-MiniLM-L6-v2"
                    ),
                )
            except Exception as exc:
                logger.error('Manual matching error: %s', exc, exc_info=True)
    
    return render_template(
        'dashboard/manual.html',
        manual_skills_data=manual_skills_data,
        match_results=match_results,
        resumes=resumes
    )


@dashboard_bp.route('/match_manual', methods=['POST'])
@login_required
def match_manual():
    """Run matching using manual skills only (optionally include a temp skill).

    Accepts form or JSON with 'resume_id' (optional) and 'temp_skill' (optional).
    Returns a rendered page with match results (no DB persistence).
    """
    data = request.get_json(silent=True) or request.form
    resume_id = data.get('resume_id')
    temp_skill = (data.get('temp_skill') or '').strip()

    try:
        resume_id = int(resume_id) if resume_id not in (None, '', 'None') else None
    except Exception:
        resume_id = None

    # collect manual skills (global + resume-specific if resume_id provided)
    q = UserSkill.query.filter_by(user_id=current_user.id)
    if resume_id is not None:
        q = q.filter((UserSkill.resume_id == None) | (UserSkill.resume_id == resume_id))
    else:
        q = q.filter_by(resume_id=None)

    manual_skills = [u.skill_name for u in q.all()]
    if temp_skill:
        manual_skills.append(normalize_skill(temp_skill))

    # Load jobs and run matcher
    jobs = Job.query.filter_by(is_active=True).all()
    if not jobs:
        flash('No job listings available.', 'warning')
        return redirect(url_for('dashboard.index'))

    try:
        match_results = match_resume_to_jobs(
            resume_text="",
            resume_skills=manual_skills,
            jobs=jobs,
            model_name=current_app.config.get(
                "SENTENCE_TRANSFORMER_MODEL", "all-MiniLM-L6-v2"
            ),
        )
    except Exception as exc:
        logger.error('Manual matching error: %s', exc, exc_info=True)
        flash('Matching failed. Please try again.', 'danger')
        return redirect(url_for('dashboard.index'))

    # Build lightweight match objects expected by templates
    return render_template('dashboard/manual_matches.html', matches=match_results)


# ── Resume Management ──────────────────────────────────────────────────
@dashboard_bp.route('/resume/<int:resume_id>/delete', methods=['POST'])
@login_required
def delete_resume(resume_id):
    """Delete a resume and all associated match results."""
    resume = Resume.query.get(resume_id)
    
    if not resume:
        flash('Resume not found.', 'warning')
        return redirect(url_for('dashboard.profile'))
    
    if resume.user_id != current_user.id:
        flash('Unauthorized: Resume does not belong to you.', 'danger')
        return redirect(url_for('dashboard.profile'))
    
    # Get filename for cleanup
    stored_filename = resume.stored_filename
    upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
    filepath = os.path.join(upload_folder, stored_filename)
    
    # Delete from database (cascade will delete MatchResults)
    try:
        db.session.delete(resume)
        db.session.commit()
        
        # Delete file from disk
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception as e:
                logger.warning('Could not delete resume file %s: %s', filepath, e)
        
        flash(f'Resume "{resume.original_filename}" deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error('Error deleting resume: %s', e, exc_info=True)
        flash('Failed to delete resume. Please try again.', 'danger')
    
    return redirect(url_for('dashboard.profile'))


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
