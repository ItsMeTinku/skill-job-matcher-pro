"""
routes/analysis.py — Resume analysis blueprint
================================================
Handles:
  - POST /analyze   — upload resume → parse → extract skills → AI match
  - GET  /results   — view full results for a specific match session

The full AI pipeline:
  1. Validate & save uploaded file
  2. Parse text from PDF/DOCX
  3. Extract skills with NLP taxonomy
  4. Run semantic + keyword matching against all jobs
  5. Persist Resume + MatchResult rows
  6. Redirect to dashboard
"""

import os
import logging
from datetime import datetime

from flask import (
    Blueprint, request, redirect, url_for, flash, current_app,
)
from flask_login import login_required, current_user

from extensions import db, limiter
from models.resume import Resume
from models.match import MatchResult
from models.job import Job
from utils import allowed_file, save_uploaded_file
from utils.parser import parse_resume
from utils.skill_extractor import extract_skills, skills_to_string
from utils.matcher import match_resume_to_jobs

analysis_bp = Blueprint("analysis", __name__)
logger = logging.getLogger(__name__)


@analysis_bp.route("/analyze", methods=["POST"])
@login_required
@limiter.limit("10 per hour")
def analyze():
    """
    Full pipeline:
    upload → parse → extract skills → semantic matching → persist → dashboard
    """

    # ── 1. File validation ────────────────────────────────────────────
    uploaded_file = request.files.get("resume_file")

    if not uploaded_file or uploaded_file.filename == "":
        flash("Please select a resume file to upload.", "danger")
        return redirect(url_for("dashboard.index"))

    if not allowed_file(uploaded_file.filename):
        flash("Only PDF and DOCX files are supported.", "danger")
        return redirect(url_for("dashboard.index"))

    # ── 2. Save file securely ─────────────────────────────────────────
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    try:
        stored_name, original_name = save_uploaded_file(uploaded_file, upload_folder)
    except Exception as exc:
        logger.error("File save error: %s", exc)
        flash("File upload failed. Please try again.", "danger")
        return redirect(url_for("dashboard.index"))

    filepath = os.path.join(upload_folder, stored_name)
    file_ext = stored_name.rsplit(".", 1)[1].lower()
    file_size = os.path.getsize(filepath)

    # ── 3. Parse resume ───────────────────────────────────────────────
    parse_result = parse_resume(filepath)

    if parse_result["error"]:
        _cleanup_file(filepath)
        flash(f"Could not read resume: {parse_result['error']}", "danger")
        return redirect(url_for("dashboard.index"))

    raw_text = parse_result["text"]

    if not raw_text.strip():
        _cleanup_file(filepath)
        flash(
            "Resume appears to be empty or image-based (scanned PDF). "
            "Please upload a text-based PDF or DOCX.",
            "warning",
        )
        return redirect(url_for("dashboard.index"))

    # ── 4. Extract skills ─────────────────────────────────────────────
    skills_list = extract_skills(raw_text)

    if not skills_list:
        flash(
            "No recognisable technology skills found. "
            "The analysis will run with general text matching.",
            "info",
        )

    # ── 5. Persist Resume record ──────────────────────────────────────
    resume = Resume(
        user_id           = current_user.id,
        original_filename = original_name,
        stored_filename   = stored_name,
        file_type         = file_ext,
        file_size_bytes   = file_size,
        raw_text          = raw_text[:50_000],   # cap storage
        extracted_skills  = skills_to_string(skills_list),
        education_info    = parse_result["education"],
        certifications    = parse_result["certifications"],
        processed_at      = datetime.utcnow(),
    )
    db.session.add(resume)
    db.session.flush()   # get resume.id before committing

    # Merge manual user skills (global + resume-specific) into the extracted skills
    from models.user_skill import UserSkill
    manual_q = (
        UserSkill.query
        .filter_by(user_id=current_user.id)
        .filter((UserSkill.resume_id == None) | (UserSkill.resume_id == resume.id))
        .all()
    )
    manual_skills = [u.skill_name for u in manual_q]
    # merge unique skills
    merged_skills_set = {s for s in skills_list}
    merged_skills_set.update(manual_skills)
    skills_list = sorted(merged_skills_set, key=str.lower)

    # ── 6. Load all active jobs ───────────────────────────────────────
    jobs = Job.query.filter_by(is_active=True).all()

    if not jobs:
        db.session.rollback()
        flash("No job listings found in the database.", "warning")
        return redirect(url_for("dashboard.index"))

    # ── 7. Run AI semantic matching ───────────────────────────────────
    try:
        match_results = match_resume_to_jobs(
            resume_text   = raw_text,
            resume_skills = skills_list,
            jobs          = jobs,
            model_name    = current_app.config.get(
                "SENTENCE_TRANSFORMER_MODEL", "all-MiniLM-L6-v2"
            ),
        )
    except Exception as exc:
        logger.error("Matching engine error: %s", exc, exc_info=True)
        db.session.rollback()
        _cleanup_file(filepath)
        flash(
            "AI matching encountered an error. Please try again. "
            "If the problem persists, contact support.",
            "danger",
        )
        return redirect(url_for("dashboard.index"))

    # ── 8. Persist MatchResult rows ───────────────────────────────────
    job_id_map = {j.id: j for j in jobs}

    for m in match_results:
        job_obj = job_id_map.get(m["job_id"])
        if not job_obj:
            continue

        mr = MatchResult(
            resume_id      = resume.id,
            job_id         = m["job_id"],
            match_score    = m["match_score"],
            semantic_score = m["semantic_score"],
            keyword_score  = m["keyword_score"],
        )
        mr.matched_skills = m["matched_skills"]
        mr.missing_skills = m["missing_skills"]
        db.session.add(mr)

    try:
        db.session.commit()
        logger.info(
            "Analysis complete — user=%s resume=%s skills=%d matches=%d",
            current_user.id, resume.id, len(skills_list), len(match_results),
        )
    except Exception as exc:
        db.session.rollback()
        logger.error("DB commit error after analysis: %s", exc)
        flash("Failed to save analysis results. Please try again.", "danger")
        return redirect(url_for("dashboard.index"))

    top_match = match_results[0]["job_title"] if match_results else "—"
    top_score = match_results[0]["match_score"] if match_results else 0

    flash(
        f"Analysis complete! Found {len(skills_list)} skills. "
        f"Top match: {top_match} ({top_score:.0f}%).",
        "success",
    )
    return redirect(url_for("dashboard.index"))


# ── Helpers ───────────────────────────────────────────────────────────
def _cleanup_file(filepath: str) -> None:
    """Remove a partially-saved file on error."""
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
    except OSError:
        pass
