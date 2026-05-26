"""
utils/matcher.py — Semantic AI Job Matching Engine
====================================================
Implements REAL semantic matching using:
  - sentence-transformers (all-MiniLM-L6-v2)
  - cosine similarity via sklearn

Algorithm
---------
1. Build a "resume profile" string from extracted skills + raw text snippet.
2. Build a "job profile" string from job description + required skills.
3. Encode both with SentenceTransformer → dense embedding vectors.
4. Compute cosine similarity (0–1).
5. Blend with keyword overlap score for robust final score.
6. Return ranked match results with skill gap analysis.

Public API
----------
    match_resume_to_jobs(resume_text, resume_skills, jobs) -> list[MatchData]

Where MatchData is a dict:
    {
        "job_id":         int,
        "job_title":      str,
        "job_category":   str,
        "experience_level": str,
        "match_score":    float,   # 0–100 blended score
        "semantic_score": float,   # raw cosine similarity 0–1
        "keyword_score":  float,   # keyword overlap 0–100
        "matched_skills": list[str],
        "missing_skills": list[str],
    }
"""

import logging
import threading
from functools import lru_cache

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

# Thread lock so the model is only loaded once in multi-threaded gunicorn
_model_lock = threading.Lock()
_model = None


def _get_model(model_name: str = "all-MiniLM-L6-v2"):
    """Lazy-load the SentenceTransformer model (cached in the process)."""
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:
                logger.info("Loading SentenceTransformer model '%s' …", model_name)
                from sentence_transformers import SentenceTransformer  # noqa
                _model = SentenceTransformer(model_name)
                logger.info("Model loaded successfully.")
    return _model


# ── Match data type alias (plain dict for JSON-serialisability) ───────
MatchData = dict


def match_resume_to_jobs(
    resume_text: str,
    resume_skills: list[str],
    jobs: list,
    model_name: str = "all-MiniLM-L6-v2",
    top_k: int = 25,
) -> list[MatchData]:
    """
    Run semantic + keyword matching between a resume and all job listings.

    Parameters
    ----------
    resume_text   : raw text extracted from the resume
    resume_skills : list of canonical skill names from skill_extractor
    jobs          : list of Job ORM objects (from models.job)
    model_name    : sentence-transformer model to use
    top_k         : maximum results to return

    Returns
    -------
    list[MatchData] sorted by match_score descending
    """

    if not resume_text.strip() and not resume_skills:
        logger.warning("Empty resume — returning empty match list.")
        return []

    if not jobs:
        logger.warning("No jobs in database — cannot match.")
        return []

    # ── Build resume profile text ─────────────────────────────────────
    skills_str = ", ".join(resume_skills) if resume_skills else ""
    # Take first 400 words of resume text for embedding (avoids token overflow)
    resume_snippet = " ".join(resume_text.split()[:400])
    resume_profile = f"Skills: {skills_str}. Experience: {resume_snippet}"

    # ── Build job profile texts ────────────────────────────────────────
    job_profiles = []
    for job in jobs:
        job_skills_str = ", ".join(job.required_skills)
        job_profile = f"Job: {job.title}. Skills required: {job_skills_str}. {job.description}"
        job_profiles.append(job_profile)

    # ── Semantic embedding ─────────────────────────────────────────────
    try:
        model = _get_model(model_name)
        all_texts  = [resume_profile] + job_profiles
        embeddings = model.encode(all_texts, convert_to_numpy=True, show_progress_bar=False)

        resume_emb = embeddings[0].reshape(1, -1)
        job_embs   = embeddings[1:]

        # cosine_similarity returns shape (1, n_jobs)
        semantic_scores = cosine_similarity(resume_emb, job_embs)[0]   # shape (n_jobs,)

    except Exception as exc:
        logger.error("Semantic embedding failed: %s — falling back to keyword-only.", exc)
        semantic_scores = np.zeros(len(jobs))

    # ── Build results ─────────────────────────────────────────────────
    resume_skills_lower = {s.lower() for s in resume_skills}
    results: list[MatchData] = []

    for idx, job in enumerate(jobs):
        job_skills_lower = {s.lower() for s in job.required_skills}

        # ── Keyword overlap score ─────────────────────────────────────
        matched = resume_skills_lower & job_skills_lower
        missing = job_skills_lower - resume_skills_lower

        keyword_score = (
            (len(matched) / len(job_skills_lower)) * 100
            if job_skills_lower
            else 0.0
        )

        # ── Semantic score (0–1 → 0–100) ─────────────────────────────
        semantic_score = float(semantic_scores[idx])
        semantic_pct   = semantic_score * 100

        # ── If all required skills are matched exactly, treat as a perfect match.
        # This prevents a low semantic embedding score from incorrectly downgrading
        # an exact skills match in manual skill entry mode.
        if job_skills_lower and len(matched) == len(job_skills_lower):
            blended = 100.0
        else:
            blended = (0.60 * semantic_pct) + (0.40 * keyword_score)
            blended = max(blended, keyword_score)

        # ── Canonical casing for display ──────────────────────────────
        matched_display = _restore_casing(matched, job.required_skills)
        missing_display = _restore_casing(missing, job.required_skills)

        results.append({
            "job_id":           job.id,
            "job_title":        job.title,
            "job_category":     job.category,
            "experience_level": job.experience_level or "",
            "match_score":      round(blended, 2),
            "semantic_score":   round(semantic_score, 4),
            "keyword_score":    round(keyword_score, 2),
            "matched_skills":   sorted(matched_display),
            "missing_skills":   sorted(missing_display),
        })

    # ── Sort descending by match_score ────────────────────────────────
    results.sort(key=lambda x: x["match_score"], reverse=True)
    return results[:top_k]


def compute_global_skill_gap(
    resume_skills: list[str],
    all_jobs: list,
    top_n_missing: int = 10,
) -> list[str]:
    """
    Across all job listings, identify the most frequently missing skills
    from the candidate's profile — a high-priority learning roadmap.

    Parameters
    ----------
    resume_skills : candidate's extracted skills
    all_jobs      : all Job ORM objects
    top_n_missing : how many to return

    Returns
    -------
    list[str] of skill names ordered by frequency of absence
    """
    from collections import Counter

    resume_set = {s.lower() for s in resume_skills}
    gap_counter: Counter = Counter()

    for job in all_jobs:
        for skill in job.required_skills:
            if skill.lower() not in resume_set:
                gap_counter[skill] += 1

    return [skill for skill, _ in gap_counter.most_common(top_n_missing)]


# ── Helpers ───────────────────────────────────────────────────────────
def _restore_casing(
    lower_skills: set[str],
    canonical_source: list[str],
) -> list[str]:
    """
    Given a set of lower-cased skill names and the canonical source list,
    restore the original casing for display purposes.
    """
    canonical_map = {s.lower(): s for s in canonical_source}
    return [canonical_map.get(s, s.title()) for s in lower_skills]
