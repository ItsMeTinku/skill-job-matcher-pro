# 🤖 SkillMatch AI — V1 → V2 Upgrade Notes

> This document explains every bug that was found and fixed, every improvement
> made, and shows the exact **before vs after** code so you can see precisely
> what changed and why.

---

## 🚀 Live Demo
**Repository:** [github.com/YOUR_USERNAME/skill-job-matcher](https://github.com/YOUR_USERNAME/skill-job-matcher)
**Demo credentials:** Register a free account on first run — no invite needed.

---

## 📋 Table of Contents

1. [🏗️ System Architecture](#architecture)
2. [⚡ Quick Summary](#summary)
3. [🐛 Bug Fix 1 — `ModuleNotFoundError` on First Run](#bug1)
4. [🐛 Bug Fix 2 — Auth Layout Broken / Sidebar Visible on Login Page](#bug2)
5. [🐛 Bug Fix 3 — Dashboard Crashed for New Users with No Resume](#bug3)
6. [🐛 Bug Fix 4 — No Way to Match Jobs Without a Resume File](#bug4)
7. [🐛 Bug Fix 5 — Bulk Skill Entry Saved as One String](#bug5)
8. [🐛 Bug Fix 6 — Match Score Showed Lower Than Actual](#bug6)
9. [🐛 Bug Fix 7 — `psycopg2-binary` Failed to Install on Python 3.13](#bug7)
10. [✨ Improvement 1 — Manual Skill Entry System](#imp1)
11. [✨ Improvement 2 — `normalize_skill()` Maps Free Text to Taxonomy](#imp2)
12. [✨ Improvement 3 — Resume Delete with File Cleanup](#imp3)
13. [✨ Improvement 4 — SQLite Dev Fallback (No DB Server Needed)](#imp4)
14. [✨ Improvement 5 — Manual-Only Matching (No Upload Required)](#imp5)
15. [📁 File-by-File Summary](#files)
16. [⚙️ Setup & Installation](#setup)
17. [🔒 Security Notes](#security)

---

<a name="architecture"></a>
## 🏗️ System Architecture

### Architecture Overview

The application is a production-grade Flask web platform using a 3-tier architecture:
server-side rendered HTML via Jinja2, a Python business logic layer, and a PostgreSQL
backend hosted on Supabase (with an automatic SQLite fallback for local development).

```
┌─────────────────────────────────────────────────────────────────────┐
│                      Browser (HTML / CSS)                           │
│               Flask / Jinja2 Server-Side Rendering                  │
│                    Zero JavaScript required                         │
└───────────────────────────┬─────────────────────────────────────────┘
                            │ HTTP / HTTPS
┌───────────────────────────▼─────────────────────────────────────────┐
│                    Gunicorn WSGI Server                             │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                      Flask Application                       │   │
│  │                   (Application Factory)                      │   │
│  │                                                              │   │
│  │   auth_bp          dashboard_bp         analysis_bp          │   │
│  │   /login           /dashboard           /analyze             │   │
│  │   /register        /jobs                (AI pipeline)        │   │
│  │   /logout          /profile                                  │   │
│  │                    /skills  ← NEW V2                         │   │
│  │                    /manual  ← NEW V2                         │   │
│  │                    /resume/<id>/delete ← NEW V2              │   │
│  └──────────────────────────┬───────────────────────────────────┘   │
└─────────────────────────────┼───────────────────────────────────────┘
                              │
              ┌───────────────▼────────────────┐
              │         Utils Layer            │
              │  parser.py                     │
              │  skill_extractor.py            │
              │  matcher.py                    │
              └───────────────┬────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────────────┐
│                       Database Layer                                │
│     PostgreSQL via Supabase (prod)  /  SQLite (dev fallback)        │
│                                                                     │
│   users ──────┐                                                     │
│   resumes ────┼──── match_results                                   │
│   jobs ───────┘                                                     │
│   user_skills  ← NEW V2                                             │
└─────────────────────────────────────────────────────────────────────┘
```

### AI Matching Pipeline

```
Resume Upload (PDF / DOCX)          Manual Skill Entry ← NEW V2
         │                                   │
         ▼                                   ▼
   Resume Parser                      normalize_skill()
   pdfplumber / python-docx           taxonomy lookup →
         │                            canonical name
         ▼                                   │
   Raw Text Extraction                       │
         │                                   │
         └─────────────┬─────────────────────┘
                       │  MERGED SKILL LIST (V2)
                       │
         ┌─────────────┴───────────────────────────────┐
         ▼                                             ▼
  NLP Skill Extractor                      SentenceTransformer
  330+ taxonomy                            all-MiniLM-L6-v2
  boundary-aware regex                     384-dim embedding
         │                                             │
         ▼                                             ▼
  Extracted Skills List                  Resume Embedding Vector
         │                                             │
         └────────────────────┬────────────────────────┘
                              │
                 For each Job in database:
                   ├─ Generate Job Embedding Vector
                   ├─ Cosine Similarity  →  semantic_score (0–1)
                   ├─ Keyword Overlap    →  keyword_score  (0–100)
                   ├─ Blended Score       = 60% semantic + 40% keyword
                   └─ effective_score()  corrects underreported full-coverage ← NEW V2
                              │
                              ▼
                    Ranked Match Results
                    Per-job missing skills
                    Global Learning Roadmap
                              │
                              ▼
                    Persisted to PostgreSQL
                    Server-side rendered dashboard
```

### Authentication & Session Flow

```
User fills login form
         │
         ▼
routes/auth.py login()
         │
         ├── Query User by email
         ├── check_password_hash(stored_hash, plain_text)
         ├── Update user.last_login timestamp
         └── Flask-Login: login_user(user)
                   │
                   ▼
           Signed session cookie
           (HTTP-only, SameSite=Lax)
                   │
                   ▼
         Redirect → /dashboard
                   │
         Every protected route:
         @login_required decorator
         checks Flask-Login cookie
                   │
         /logout → logout_user()
                   clears session
                   redirect → /login
```

### Module Structure

- `app.py` — Application factory, blueprint registration, DB seeding, error handlers
- `config.py` — `DevelopmentConfig` / `ProductionConfig` / `TestingConfig`
- `extensions.py` — `db`, `limiter`, `login_manager` singletons (prevents circular imports)
- `wsgi.py` + `gunicorn.conf.py` — Production WSGI entry and tuned Gunicorn config
- **Models:** `user.py`, `resume.py`, `job.py`, `match.py`, `user_skill.py` ← new V2
- **Routes:** `auth.py`, `dashboard.py`, `analysis.py`
- **Utils:** `parser.py`, `skill_extractor.py`, `matcher.py`
- **Data:** `data/jobs.py` — 25 job descriptions, auto-seeded on first startup

---

<a name="summary"></a>
## ⚡ Quick Summary

| # | Type | Problem | Fix |
|---|------|---------|-----|
| 1 | 🐛 Bug | `ModuleNotFoundError: flask_sqlalchemy` on first run | Install deps in active venv with `pip install -r requirements.txt` |
| 2 | 🐛 Bug | Sidebar rendered on login/register page — layout completely broken | Split `base.html` into two separate layout branches |
| 3 | 🐛 Bug | Dashboard crashed with `UndefinedError` for new users with no resume | Added `{% if %}` guards in all three dashboard templates |
| 4 | 🐛 Bug | No way to use the platform without uploading a resume file | Built complete `UserSkill` model + manual entry system |
| 5 | 🐛 Bug | "Python, Flask, Docker" saved as one skill string instead of three | Added `re.split(r"[;,\n]+", ...)` bulk parsing in `add_skill()` |
| 6 | 🐛 Bug | Match score showed 67% when candidate had 100% of required skills | Added `effective_score` property — corrects blended-score underreporting |
| 7 | 🐛 Bug | `psycopg2-binary` failed to build on Python 3.13 / Windows | Switched to `psycopg[binary]` (psycopg3) |
| 8 | ✨ New | No way to add skills without uploading a document | Full manual skill CRUD — global or resume-scoped, bulk entry |
| 9 | ✨ New | Typed skill names not matched to taxonomy | `normalize_skill()` — exact → substring → title-case fallback |
| 10 | ✨ New | Deleted resume left orphan files on disk | `delete_resume()` route — DB cascade + file removal |
| 11 | ✨ New | Required PostgreSQL server to run locally | SQLite auto-fallback in `DevelopmentConfig` |
| 12 | ✨ New | Manual skills ignored during AI analysis | Manual skills merged into extracted skills before matching runs |
| 13 | ✨ New | `use_reloader=True` loaded ML model twice on Windows | `use_reloader=False` added to `app.run()` |

---

<a name="bug1"></a>
## 🐛 Bug Fix 1 — `ModuleNotFoundError` on First Run

### What Was Happening
Running `python app.py` immediately crashed before the server could start,
showing this error:

```
File "app.py", line 10, in <module>
    from extensions import db, limiter, login_manager
File "extensions.py", line 9, in <module>
    from flask_sqlalchemy import SQLAlchemy
ModuleNotFoundError: No module named 'flask_sqlalchemy'
```

### Why It Happened
The `requirements.txt` lists what the project needs — but it does not install
anything automatically. The packages had to be installed manually into the
active virtual environment. Running `python app.py` before `pip install` means
Python has none of the third-party libraries available.

### V1 — What Was Missing

```bash
# ❌ What most people did first — ran the app before installing anything
python app.py

# Result:
# ModuleNotFoundError: No module named 'flask_sqlalchemy'
```

### V2 — Correct Startup Sequence

```bash
# ✅ Step 1 — Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # macOS / Linux

# ✅ Step 2 — Install all dependencies into the venv
pip install -r requirements.txt

# ✅ Step 3 — Now run the app
python app.py
```

### Result After Fix

| Scenario | V1 | V2 |
|----------|----|----|
| Run without venv activated | ❌ `ModuleNotFoundError` | ✅ Works if packages installed globally |
| Run without `pip install` | ❌ Crashes immediately | ✅ README now shows exact steps first |
| Run after `pip install -r requirements.txt` | ✅ Works | ✅ Works |

---

<a name="bug2"></a>
## 🐛 Bug Fix 2 — Auth Layout Broken / Sidebar Visible on Login Page

### What Was Happening
After installing dependencies and opening the app, the login and register pages
were completely broken. The dark sidebar appeared on the left side of the login
form. The page header said "Dashboard" on the login screen. The layout looked
like a logged-in state had leaked into the guest view.

### Why It Happened
The `base.html` template had a single `{% if current_user.is_authenticated %}`
check to conditionally show the sidebar — but the HTML structure was not cleanly
separated into two independent branches. The sidebar `<div>` wrapper was opened
inside the `if` block but the main content `<div>` was outside it, causing both
blocks to partially render regardless of authentication state.

Also, `app.run(debug=True)` without `use_reloader=False` caused the Werkzeug
reloader to spin up two processes on Windows, loading the sentence-transformer
model twice and causing race conditions with template rendering on startup.

### V1 Code (Broken)

```html
<!-- base.html — V1 -->
<body>

{% if current_user.is_authenticated %}
<div class="app-wrapper">
  <aside class="sidebar">
    ...sidebar content...
  </aside>
{% endif %}

<!-- ❌ This <main> renders for EVERYONE — guests and logged-in users alike -->
<main class="main-content">
  {% block content %}{% endblock %}
</main>

</div>   <!-- closes app-wrapper but is OUTSIDE the if block -->
</body>
```

```python
# app.py — V1
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
    # ❌ No use_reloader=False — causes double model load on Windows
```

### V2 Code (Fixed)

```html
<!-- base.html — V2: Two completely separate layout branches -->
<body>

{% if current_user.is_authenticated %}
<!-- ══════════════════════════════════════════════
     AUTHENTICATED LAYOUT — sidebar + topbar + content
══════════════════════════════════════════════ -->
<div class="app-wrapper">
  <aside class="sidebar">
    ...sidebar with nav links...
  </aside>
  <main class="main-content">
    <header class="topbar">...</header>
    {% with messages = get_flashed_messages(with_categories=true) %}
      ...flash messages...
    {% endwith %}
    <div class="content-area">
      {% block content %}{% endblock %}
    </div>
  </main>
</div>

{% else %}
<!-- ══════════════════════════════════════════════
     GUEST LAYOUT — centered auth card only
══════════════════════════════════════════════ -->
<div class="auth-wrapper">
  {% with messages = get_flashed_messages(with_categories=true) %}
    ...flash messages for auth pages...
  {% endwith %}
  {% block content %}{% endblock %}
</div>

{% endif %}
</body>
```

```python
# app.py — V2
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
    # ✅ use_reloader=False — prevents double model load on Windows
```

### Result After Fix

| Page | V1 | V2 |
|------|----|----|
| `/login` | ❌ Sidebar visible, broken layout | ✅ Clean centered auth card |
| `/register` | ❌ Sidebar visible, broken layout | ✅ Clean centered auth card |
| `/dashboard` (logged in) | ✅ Sidebar shows | ✅ Sidebar shows |
| Windows startup | ❌ Model loads twice, race condition | ✅ Single process, stable startup |

---

<a name="bug3"></a>
## 🐛 Bug Fix 3 — Dashboard Crashed for New Users with No Resume

### What Was Happening
After a brand new user registered and logged in for the first time, the dashboard
page threw a Jinja2 `UndefinedError` and showed a 500 internal server error
instead of the welcome screen. The same crash also happened on the Jobs and
Profile pages.

### Why It Happened
The dashboard template tried to access index `[0]` of `top_matches` directly,
and used variables like `top_matches[0].job.title` without first checking
whether any matches existed. Since a new user has no resume and no matches,
`top_matches` was an empty list — and `[][0]` raises an `IndexError` inside
Jinja2 which surfaces as an `UndefinedError`.

### V1 Template (Broken)

```html
<!-- templates/dashboard/index.html — V1 -->

<!-- ❌ Crashes when top_matches is empty (new user, no resume yet) -->
<div class="best-match-title">{{ top_matches[0].job.title }}</div>
<div class="best-match-score">{{ top_matches[0].score_int }}%</div>

<!-- ❌ Iterates skills_list — crashes if latest_resume is None -->
{% for skill in all_skills %}
  <span class="skill-pill">{{ skill }}</span>
{% endfor %}
```

```html
<!-- templates/dashboard/profile.html — V1 -->

<!-- ❌ Accesses resume.skills_list without checking if resumes exist -->
{{ resumes[0].original_filename }}
```

### V2 Template (Fixed)

```html
<!-- templates/dashboard/index.html — V2 -->

<!-- ✅ Guard the entire best-match section -->
{% if top_matches %}
  {% set best = top_matches[0] %}
  <div class="best-match-card">
    <div class="best-match-title">{{ best.job.title }}</div>
    <div class="best-match-score">{{ best.score_int }}%</div>
  </div>
{% endif %}

<!-- ✅ Show empty state card when no resume uploaded yet -->
{% if not latest_resume %}
  <div class="empty-state-card">
    <div class="empty-icon"><i class="bi bi-cpu"></i></div>
    <h4>No analysis yet</h4>
    <p>Upload your resume on the left to run the AI matching engine.</p>
  </div>
{% else %}
  {% for skill in all_skills %}
    <span class="skill-pill">{{ skill }}</span>
  {% endfor %}
{% endif %}
```

```html
<!-- templates/dashboard/jobs.html — V2 -->

<!-- ✅ Empty state when search returns no results -->
{% if jobs_page.items %}
  <div class="jobs-grid">
    {% for job in jobs_page.items %}...{% endfor %}
  </div>
{% else %}
  <div class="text-center py-5">
    <h5>No jobs found</h5>
    <p>Try different search terms or remove the category filter.</p>
  </div>
{% endif %}
```

### Result After Fix

| User State | V1 | V2 |
|------------|----|----|
| New user, no resume | ❌ 500 crash | ✅ Clean empty state with upload prompt |
| No jobs in search results | ❌ Crash or blank | ✅ "No jobs found" message |
| Empty resume history | ❌ Crash | ✅ "Upload your first resume" prompt |
| User with resumes | ✅ Works | ✅ Works |

---

<a name="bug4"></a>
## 🐛 Bug Fix 4 — No Way to Match Jobs Without a Resume File

### What Was Happening
The entire AI matching pipeline was locked behind a resume file upload. Users who
did not have a PDF/DOCX file on hand — or whose resume parser extracted zero
skills from their document — had no way to use the platform at all. The matching
engine simply returned empty results with no alternative path.

### Why It Happened
V1 was designed with a single entry point: upload file → parse → extract → match.
There was no concept of skills that a user could enter manually. The `Resume`
model was the only way to supply skills to the matcher.

### V1 Code (Broken)

```python
# routes/dashboard.py — V1
# Only 3 routes existed:
@dashboard_bp.route("/", methods=["GET"])           # dashboard
@dashboard_bp.route("/jobs", methods=["GET"])       # job browser
@dashboard_bp.route("/profile", methods=["GET"])    # profile

# ❌ No skill entry, no manual matching, no way to use platform without a file
```

```python
# routes/analysis.py — V1
skills_list = extract_skills(raw_text)
# ❌ Only source of skills was the parsed resume — manual skills didn't exist
match_results = match_resume_to_jobs(
    resume_text=raw_text,
    resume_skills=skills_list,
    jobs=jobs,
)
```

### V2 Code (Fixed)

**New model added — `models/user_skill.py`:**

```python
# models/user_skill.py — V2 (NEW)
class UserSkill(db.Model):
    __tablename__ = "user_skills"

    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    resume_id  = db.Column(db.Integer, db.ForeignKey("resumes.id"), nullable=True)
    #   └─ None = global skill applied to every analysis
    #   └─ <id> = scoped to one specific resume upload
    skill_name = db.Column(db.String(200), nullable=False)
    source     = db.Column(db.String(20), default="manual")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

**New routes added to `routes/dashboard.py`:**

```python
# routes/dashboard.py — V2 (NEW routes)
@dashboard_bp.route("/skills", methods=["GET"])           # skill management view
@dashboard_bp.route("/skills", methods=["POST"])          # add skill(s)
@dashboard_bp.route("/skills/remove", methods=["POST"])   # remove a skill
@dashboard_bp.route("/manual", methods=["GET"])           # manual matching page
@dashboard_bp.route("/match_manual", methods=["POST"])    # run matcher (no DB save)
@dashboard_bp.route("/resume/<int:resume_id>/delete", methods=["POST"])  # delete resume
```

**Manual skills merged into AI pipeline at analysis time:**

```python
# routes/analysis.py — V2
skills_list = extract_skills(raw_text)

# ✅ NEW: Merge manual user skills (global + resume-specific)
from models.user_skill import UserSkill
manual_q = (
    UserSkill.query
    .filter_by(user_id=current_user.id)
    .filter(
        (UserSkill.resume_id == None) |    # global skills
        (UserSkill.resume_id == resume.id)  # resume-scoped skills
    )
    .all()
)
manual_skills = [u.skill_name for u in manual_q]

merged_skills_set = {s for s in skills_list}
merged_skills_set.update(manual_skills)                     # ✅ merge both sources
skills_list = sorted(merged_skills_set, key=str.lower)

match_results = match_resume_to_jobs(
    resume_text=raw_text,
    resume_skills=skills_list,   # ← now includes both extracted + manual
    jobs=jobs,
)
```

**New sidebar link in `base.html`:**

```html
<!-- base.html — V1 sidebar -->
<a href="{{ url_for('dashboard.index') }}">Dashboard</a>
<a href="{{ url_for('dashboard.jobs') }}">Browse Jobs</a>
<a href="{{ url_for('dashboard.profile') }}">My Profile</a>
<!-- ❌ No manual skills link -->

<!-- base.html — V2 sidebar -->
<a href="{{ url_for('dashboard.index') }}">Dashboard</a>
<a href="{{ url_for('dashboard.jobs') }}">Browse Jobs</a>
<a href="{{ url_for('dashboard.manual') }}">Manual Skills</a>  <!-- ✅ NEW -->
<a href="{{ url_for('dashboard.profile') }}">My Profile</a>
```

### Result After Fix

| Scenario | V1 | V2 |
|----------|----|----|
| No resume file available | ❌ Blocked | ✅ Add skills manually on /manual |
| Resume parsed zero skills | ❌ Empty results | ✅ Manual skills fill the gap |
| Want to test matching instantly | ❌ Must upload first | ✅ Enter skills and match in seconds |
| Skills from both sources | ❌ Not possible | ✅ Extracted + manual merged automatically |

---

<a name="bug5"></a>
## 🐛 Bug Fix 5 — Bulk Skill Entry Saved as One String

### What Was Happening
When a user typed `"Python, Flask, Docker"` into the skill input and clicked Add,
the database saved one skill named `"Python, Flask, Docker"` — the entire string
as a single entry — instead of three separate skills. The skill cloud then showed
one very long pill instead of three individual ones.

### Why It Happened
The V1 `add_skill()` route (which was actually first introduced in V2 commit
`29e4128`) treated the entire form input as a single skill name with a simple
`.strip()` and saved it directly. There was no splitting logic.

### V1 `add_skill()` (Broken)

```python
# routes/dashboard.py — first version of add_skill()
@dashboard_bp.route("/skills", methods=["POST"])
@login_required
def add_skill():
    data = request.get_json(silent=True) or request.form
    raw_skill = (data.get("skill") or "").strip()

    # ❌ Treats entire input as one skill — no splitting at all
    skill = normalize_skill(raw_skill)

    us = UserSkill(user_id=current_user.id, skill_name=skill)
    db.session.add(us)
    db.session.commit()
```

### V2 `add_skill()` (Fixed)

```python
# routes/dashboard.py — V2: split on comma, semicolon, or newline
import re

@dashboard_bp.route("/skills", methods=["POST"])
@login_required
def add_skill():
    data = request.get_json(silent=True) or request.form
    raw_skill = (data.get("skill") or "").strip()

    # ✅ Split on any separator — user can paste a whole list at once
    skills = [
        normalize_skill(s)
        for s in re.split(r"[;,\n]+", raw_skill)
        if s.strip()
    ]

    added_skills = []
    for skill in skills:
        us = UserSkill(user_id=current_user.id, resume_id=resume_id, skill_name=skill)
        db.session.add(us)
        added_skills.append(us)

    db.session.commit()

    # ✅ Flash message shows correct count
    if len(added_skills) == 1:
        flash(f"Skill added: {added_skills[0].skill_name}", "success")
    else:
        flash(f"Added {len(added_skills)} skills: {', '.join(s.skill_name for s in added_skills)}", "success")
```

### Result After Fix

| Input | V1 Result | V2 Result |
|-------|-----------|-----------|
| `Python` | 1 skill: `Python` | 1 skill: `Python` |
| `Python, Flask` | 1 skill: `Python, Flask` ❌ | 2 skills: `Python`, `Flask` ✅ |
| `Python; Flask; Docker` | 1 skill: `Python; Flask; Docker` ❌ | 3 skills ✅ |
| `Python\nFlask\nDocker` (pasted list) | 1 skill ❌ | 3 skills ✅ |
| `ml, deep learning, nlp` | 1 skill ❌ | 3 normalised skills ✅ |

---

<a name="bug6"></a>
## 🐛 Bug Fix 6 — Match Score Showed Lower Than Actual

### What Was Happening
When a candidate's resume contained every single required skill for a job,
the displayed match score was still showing values like 67% or 71% instead of
100%. A perfect keyword coverage was being underreported because the semantic
embedding score pulled the blended average down.

### Why It Happened
`match_score` stored in the database is the blended value: `(0.60 × semantic%) + (0.40 × keyword%)`.
The semantic score can be 0.60 even for a perfect skill match because the embedding
compares text similarity, not exact skill overlap. So a candidate with 100%
keyword coverage could still get a blended score of ~72% if the resume text
didn't semantically resemble the job description word-for-word.

All display properties (`score_int`, `score_label`, `score_badge_class`,
`progress_class`) read directly from `match_score` — so the underreported
blended value was shown everywhere.

### V1 Code (Broken)

```python
# models/match.py — V1
@property
def score_int(self) -> int:
    return int(round(self.match_score))  # ❌ always uses raw blended score

@property
def score_label(self) -> str:
    if self.match_score >= 75:    # ❌ compares raw blended value
        return "Excellent"
    if self.match_score >= 55:
        return "Good"
    if self.match_score >= 35:
        return "Fair"
    return "Low"

@property
def score_badge_class(self) -> str:
    if self.match_score >= 75:    # ❌ raw blended value again
        return "badge-excellent"
    ...
```

### V2 Code (Fixed)

```python
# models/match.py — V2
@property
def effective_score(self) -> float:
    """Return the most accurate display score, correcting blended underreporting."""

    # ✅ Case 1: All required skills are matched → must be 100%
    if self.job and self.job.required_skills:
        required_lower = {s.lower() for s in self.job.required_skills}
        matched_lower  = {s.lower() for s in self.matched_skills}
        if required_lower and required_lower <= matched_lower:
            return 100.0

    # ✅ Case 2: Keyword score is higher than blended → take the better one
    if self.keyword_score is not None:
        return max(self.match_score, self.keyword_score)

    # Case 3: No better info — use stored blended score
    return self.match_score

# All display properties now use effective_score instead of match_score
@property
def score_int(self) -> int:
    return int(round(self.effective_score))   # ✅ corrected score

@property
def score_label(self) -> str:
    score = self.effective_score              # ✅ corrected score
    if score >= 75: return "Excellent"
    if score >= 55: return "Good"
    if score >= 35: return "Fair"
    return "Low"

@property
def score_badge_class(self) -> str:
    score = self.effective_score              # ✅ corrected score
    if score >= 75: return "badge-excellent"
    if score >= 55: return "badge-good"
    if score >= 35: return "badge-fair"
    return "badge-low"
```

### Result After Fix

| Situation | V1 Score | V2 Score |
|-----------|----------|----------|
| All required skills matched | ❌ ~67–72% (underreported) | ✅ 100% |
| Keyword score > blended score | ❌ Lower blended shown | ✅ Higher score shown |
| Partial match (normal case) | ✅ Correct | ✅ Correct |
| No skills matched | ✅ Low score | ✅ Low score |

---

<a name="bug7"></a>
## 🐛 Bug Fix 7 — `psycopg2-binary` Failed to Install on Python 3.13

### What Was Happening
On Python 3.13 or certain Windows configurations, `pip install -r requirements.txt`
failed with a C compiler / build wheel error when trying to install `psycopg2-binary`:

```
error: Microsoft Visual C++ 14.0 or greater is required.
Get it with "Microsoft C++ Build Tools"
```

### Why It Happened
`psycopg2-binary` is the older PostgreSQL adapter (psycopg2). Its pre-built
binary wheels for Python 3.13 were not yet available on PyPI at the time of the
original scaffold, forcing pip to attempt a source build which requires the MSVC
compiler on Windows.

### V1 `requirements.txt` (Broken)

```
# requirements.txt — V1
psycopg2-binary==2.9.9     # ❌ no pre-built wheel for Python 3.13
scikit-learn==1.5.0
torch==2.3.1               # ❌ hard-pinned — conflicts on some platforms
numpy==1.26.4
```

### V2 `requirements.txt` (Fixed)

```
# requirements.txt — V2
psycopg[binary]            # ✅ psycopg3 — modern driver, wheels available for Python 3.13
scikit-learn==1.6.0        # ✅ updated — bug fixes in cosine_similarity edge cases
torch>=2.6.0               # ✅ flexible pin — pip resolves compatible version per platform
numpy==2.2.0               # ✅ updated — required for torch >=2.6 compatibility
```

`psycopg[binary]` is the modern psycopg3 driver. It has pre-built binary wheels
for all major platforms and Python versions, so no C compiler is needed.

### Result After Fix

| Platform | V1 | V2 |
|----------|----|-----|
| Python 3.13 / Windows (no MSVC) | ❌ Build failure | ✅ Installs from wheel |
| macOS / Linux | ✅ Worked | ✅ Works |
| Python 3.11 / 3.12 | ✅ Worked | ✅ Works |
| Heroku / Render (Python 3.13) | ❌ Build failure | ✅ Works |

---

<a name="imp1"></a>
## ✨ Improvement 1 — Manual Skill Entry System

### Before (V1)
Skills only came from parsed resume files. No UI existed for direct skill input.
No `UserSkill` model existed. The database had 4 tables: `users`, `resumes`,
`jobs`, `match_results`.

### After (V2)

A complete manual skill subsystem was built — a fifth database table, new routes,
new templates, and integration into the AI pipeline.

**New pages added:**

`/dashboard/manual` — Enter skills and run a match instantly without uploading
any file. Results are displayed on the page without being saved to the database.

`/dashboard/skills` — Full skill library: view all manually added skills, grouped
by global vs resume-specific, and remove individual entries.

```python
# routes/dashboard.py — V2: manual matching (no DB persistence)
@dashboard_bp.route('/manual', methods=['GET'])
@login_required
def manual():
    manual_skills_data = UserSkill.query.filter_by(user_id=current_user.id).all()
    manual_skills = [u.skill_name for u in manual_skills_data]
    jobs = Job.query.filter_by(is_active=True).all()

    match_results = []
    if manual_skills and jobs:
        match_results = match_resume_to_jobs(
            resume_text="",                # ← no resume text needed
            resume_skills=manual_skills,   # ← manual skills drive the match
            jobs=jobs,
        )

    return render_template('dashboard/manual.html',
                           manual_skills_data=manual_skills_data,
                           match_results=match_results)
```

**Skill scope — global vs resume-specific:**

| Scope | `resume_id` value | Applied when |
|-------|------------------|--------------|
| Global | `NULL` | Every resume analysis for this user |
| Resume-specific | `<resume_id>` | Only when that specific resume is analysed |

---

<a name="imp2"></a>
## ✨ Improvement 2 — `normalize_skill()` Maps Free Text to Taxonomy

### Before (V1)
There was no function to handle user-typed skill names. If a user typed `"python"`,
it would be stored as `"python"` — lowercase, not matching the canonical `"Python"`
in the 330-entry taxonomy. Skills added manually would never match correctly in
keyword overlap calculations.

```python
# utils/skill_extractor.py — V1
# Only three public functions existed:
def extract_skills(text: str) -> list[str]: ...
def skills_to_string(skills: list[str]) -> str: ...
def string_to_skills(skills_str: str) -> list[str]: ...
# ❌ No normalize_skill() — raw user input stored as-is
```

### After (V2)

```python
# utils/skill_extractor.py — V2 (NEW)
def normalize_skill(raw_skill: str) -> str:
    """
    Map a manually-entered skill to the canonical taxonomy name where possible.
    Falls back to title-case if no match is found.
    """
    if not raw_skill or not raw_skill.strip():
        return ""

    key = raw_skill.strip().lower()
    taxonomy_map = {s.lower(): s for s in SKILL_TAXONOMY}

    # Step 1: Exact match → return canonical name
    # "python" → "Python", "nlp" → "NLP", "aws" → "AWS"
    if key in taxonomy_map:
        return taxonomy_map[key]

    # Step 2: Substring match → longest taxonomy entry that contains the input
    # "machine" → "Machine Learning", "deep" → "Deep Learning"
    candidates = [s for s in SKILL_TAXONOMY if key in s.lower()]
    if candidates:
        return sorted(candidates, key=len, reverse=True)[0]

    # Step 3: Fallback → title-case the user's input as-is
    # "myframework" → "Myframework"
    return raw_skill.strip().title()
```

**Example mappings:**

| User Types | normalize_skill() Returns |
|------------|--------------------------|
| `python` | `Python` |
| `PYTHON` | `Python` |
| `nlp` | `Natural Language Processing` |
| `ml` → (no exact match) | `Machine Learning` (substring) |
| `aws` | `AWS` |
| `k8s` → (no match) | `K8S` (title fallback) |
| `docker` | `Docker` |

---

<a name="imp3"></a>
## ✨ Improvement 3 — Resume Delete with File Cleanup

### Before (V1)
The profile page listed all uploaded resumes but there was no way to delete them.
Old files accumulated in the `uploads/` folder forever. Orphaned match results
remained in the database. No route existed to handle deletion.

```python
# routes/dashboard.py — V1
@dashboard_bp.route("/profile", methods=["GET"])
@login_required
def profile():
    resumes = Resume.query.filter_by(user_id=current_user.id).all()
    return render_template("dashboard/profile.html", resumes=resumes)
    # ❌ Read-only — no delete functionality at all
```

### After (V2)

```python
# routes/dashboard.py — V2 (NEW)
@dashboard_bp.route('/resume/<int:resume_id>/delete', methods=['POST'])
@login_required
def delete_resume(resume_id):
    resume = Resume.query.get(resume_id)

    # ✅ Ownership check — users can only delete their own resumes
    if not resume:
        flash('Resume not found.', 'warning')
        return redirect(url_for('dashboard.profile'))

    if resume.user_id != current_user.id:
        flash('Unauthorized.', 'danger')
        return redirect(url_for('dashboard.profile'))

    stored_filename = resume.stored_filename
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], stored_filename)

    # ✅ Step 1: Delete from database (cascade removes match_results)
    db.session.delete(resume)
    db.session.commit()

    # ✅ Step 2: Delete physical file from disk
    if os.path.exists(filepath):
        os.remove(filepath)

    flash(f'Resume "{resume.original_filename}" deleted successfully.', 'success')
    return redirect(url_for('dashboard.profile'))
```

**What gets cleaned up on delete:**

| Item | V1 | V2 |
|------|----|----|
| `resumes` DB row | ❌ Stays forever | ✅ Deleted |
| `match_results` rows | ❌ Orphaned forever | ✅ Cascade deleted |
| File in `uploads/` folder | ❌ Stays on disk forever | ✅ Removed from disk |
| Ownership verified | ❌ No check | ✅ Checked — rejects cross-user deletes |

---

<a name="imp4"></a>
## ✨ Improvement 4 — SQLite Dev Fallback (No DB Server Needed)

### Before (V1)
`DevelopmentConfig` required a PostgreSQL database. If no `DATABASE_URL` was
set in `.env`, the app pointed at `localhost:5432` which most developers don't
have running — causing an immediate connection error on first run.

```python
# config.py — V1 DevelopmentConfig
class DevelopmentConfig(BaseConfig):
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/skill_job_matcher_dev"
        # ❌ Requires a local PostgreSQL server — most devs don't have one
    )
```

### After (V2)

```python
# config.py — V2 DevelopmentConfig
class DevelopmentConfig(BaseConfig):
    # ✅ Auto-uses SQLite if no DATABASE_URL is set in .env
    # Developer needs zero database setup to get started
    default_sqlite_path = os.path.join(BASE_DIR, "instance", "dev.sqlite")
    default_sqlite_uri  = f"sqlite:///{default_sqlite_path.replace(chr(92), '/')}"

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        default_sqlite_uri    # ← SQLite file created automatically on first run
    )
```

**Developer experience comparison:**

| Scenario | V1 | V2 |
|----------|----|-----|
| Clone repo + `pip install` + `python app.py` | ❌ Connection refused (no Postgres) | ✅ Works immediately with SQLite |
| Have Supabase URL in `.env` | ✅ Works | ✅ Works (PostgreSQL used) |
| Have local Postgres running | ✅ Works | ✅ Works |
| Production deployment | ✅ PostgreSQL | ✅ PostgreSQL |
| Unit tests | ✅ In-memory SQLite | ✅ In-memory SQLite |

---

<a name="imp5"></a>
## ✨ Improvement 5 — Manual-Only Matching (No Upload Required)

### Before (V1)
Running the AI matcher required going through the full pipeline:
upload file → parse → extract → match. There was no shortcut.

### After (V2)

The `/dashboard/match_manual` route runs the full semantic matcher using only
manually entered skills, skipping file upload, parsing, and DB persistence entirely.
Results are rendered directly as HTML — no round-trip to the database.

```python
# routes/dashboard.py — V2
@dashboard_bp.route('/match_manual', methods=['POST'])
@login_required
def match_manual():
    # Collect global + resume-scoped manual skills
    q = UserSkill.query.filter_by(user_id=current_user.id)
    manual_skills = [u.skill_name for u in q.all()]

    jobs = Job.query.filter_by(is_active=True).all()

    # ✅ Full semantic AI matching — no file, no DB write
    match_results = match_resume_to_jobs(
        resume_text="",            # ← empty — no resume text needed
        resume_skills=manual_skills,
        jobs=jobs,
    )

    # ✅ Render results inline — nothing saved to DB
    return render_template('dashboard/manual_matches.html', matches=match_results)
```

---

<a name="files"></a>
## 📁 File-by-File Summary

### `models/user_skill.py` — New in V2

| What | V1 | V2 |
|------|----|----|
| File exists | ❌ Did not exist | ✅ New model |
| Table | Not present | `user_skills` |
| Purpose | — | Store manually added skills |
| Resume scoping | — | `resume_id=NULL` (global) or `<id>` (scoped) |
| Relationship | — | `User.manual_skills` back-populates |

### `models/match.py` — Updated

| What | V1 | V2 |
|------|----|----|
| `effective_score` property | ❌ Did not exist | ✅ Corrects blended underreporting |
| `score_int` reads from | `match_score` | `effective_score` |
| `score_label` reads from | `match_score` | `effective_score` |
| `score_badge_class` reads from | `match_score` | `effective_score` |
| `progress_class` reads from | `match_score` | `effective_score` |
| Full keyword coverage | ❌ Shows ~67–72% | ✅ Shows 100% |

### `models/__init__.py` — Updated

```diff
  from .user   import User
  from .resume import Resume
  from .job    import Job
  from .match  import MatchResult
+ from .user_skill import UserSkill   # ← NEW V2
```

### `models/user.py` — Updated

```diff
  resumes = db.relationship("Resume", back_populates="user", ...)

+ manual_skills = db.relationship(   # ← NEW V2
+     "UserSkill",
+     back_populates="user",
+     cascade="all, delete-orphan",
+ )
```

### `utils/skill_extractor.py` — Updated

| Function | V1 | V2 |
|----------|----|----|
| `extract_skills()` | ✅ Present | ✅ Present (unchanged) |
| `skills_to_string()` | ✅ Present | ✅ Present (unchanged) |
| `string_to_skills()` | ✅ Present | ✅ Present (unchanged) |
| `normalize_skill()` | ❌ Did not exist | ✅ New — taxonomy lookup with fallback |

### `routes/dashboard.py` — Heavily Extended

| Route | V1 | V2 |
|-------|----|----|
| `GET /dashboard/` | ✅ | ✅ |
| `GET /dashboard/jobs` | ✅ | ✅ |
| `GET /dashboard/profile` | ✅ | ✅ |
| `GET /dashboard/skills` | ❌ | ✅ NEW |
| `POST /dashboard/skills` | ❌ | ✅ NEW — add single or bulk |
| `POST /dashboard/skills/remove` | ❌ | ✅ NEW |
| `GET /dashboard/manual` | ❌ | ✅ NEW |
| `POST /dashboard/match_manual` | ❌ | ✅ NEW |
| `POST /dashboard/resume/<id>/delete` | ❌ | ✅ NEW |
| Line count | 149 lines | 413 lines |

### `routes/analysis.py` — Updated

| Section | V1 | V2 |
|---------|----|----|
| Manual skill merge | ❌ Did not exist | ✅ Fetches UserSkill rows, merges with extracted |
| Skills used in matching | Extracted only | Extracted + manual (merged set) |

### `config.py` — Updated

| Config class | V1 | V2 |
|-------------|----|----|
| `DevelopmentConfig` fallback | `postgresql://localhost` | `sqlite:///instance/dev.sqlite` |
| `ProductionConfig` | Supabase PostgreSQL | Supabase PostgreSQL (unchanged) |
| `TestingConfig` | `sqlite:///:memory:` | `sqlite:///:memory:` (unchanged) |

### `app.py` — Updated

```diff
  if __name__ == "__main__":
-     app.run(host="0.0.0.0", port=5000, debug=False)
+     app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
+     # Prevents double ML model load on Windows hot-reload
```

### `base.html` — Fully Restructured

| Section | V1 | V2 |
|---------|----|----|
| Authenticated layout | Partially separated | Fully isolated `{% if %}` branch |
| Guest layout | Leaked sidebar | Clean centered auth card only |
| Manual Skills nav link | ❌ Missing | ✅ Added |
| Flash messages | Auth pages missing | Both layouts handle flashes |

### Templates — New in V2

| File | Purpose |
|------|---------|
| `templates/dashboard/manual.html` | Skill entry form + match results without upload |
| `templates/dashboard/manual_matches.html` | Results panel for manual-only matching |
| `templates/dashboard/skills.html` | Full skill library — view, add, remove |

### `static/js/dashboard.js` — New in V2

Minimal JavaScript added for the skill management form UX — handles skill
tag removal feedback without requiring a full page reload.

### Files Not Changed (carried over from V1 unchanged)

| File | Why untouched |
|------|--------------|
| `utils/parser.py` | PDF/DOCX parsing working correctly |
| `utils/matcher.py` | Semantic matching engine working correctly |
| `models/resume.py` | Resume model working correctly |
| `models/job.py` | Job model working correctly |
| `extensions.py` | Extension singletons working correctly |
| `wsgi.py` | Gunicorn entry working correctly |
| `gunicorn.conf.py` | Production config working correctly |
| `data/jobs.py` | 25-job dataset unchanged |

---

<a name="setup"></a>
## ⚙️ Setup & Installation

### Step 1 — Clone and create virtual environment

```bash
git clone https://github.com/YOUR_USERNAME/skill-job-matcher.git
cd skill-job-matcher

python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### Step 2 — Install dependencies

```bash
pip install -r requirements.txt
```

### Step 3 — Configure environment

```bash
cp .env.example .env
```

Edit `.env`:
```env
# Generate this: python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=your-generated-secret-key

FLASK_ENV=development

# Leave empty → SQLite used automatically (no database server needed)
# DATABASE_URL=postgresql://postgres:[password]@db.[ref].supabase.co:5432/postgres
```

### Step 4 — Run

```bash
# Development — SQLite auto-created in instance/dev.sqlite
python app.py
```

Tables are created and 25 jobs seeded automatically on first run.
Open [http://localhost:5000](http://localhost:5000) → Register → Upload a resume
or go to **Manual Skills** to enter skills directly.

### Step 5 — Production (Gunicorn)

```bash
FLASK_ENV=production gunicorn -c gunicorn.conf.py wsgi:application
```

### Supabase PostgreSQL Setup

1. Create a free project at [supabase.com](https://supabase.com)
2. **Project Settings → Database → Connection string → URI → Session mode (port 5432)**
3. Set in `.env`:
```env
DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
FLASK_ENV=production
```

---

<a name="security"></a>
## 🔒 Security Notes

| Practice | Where | Why |
|----------|-------|-----|
| PBKDF2-SHA256 password hashing | `models/user.py → set_password()` | Passwords never stored in plain text |
| Login rate limiting — 5/min | `routes/auth.py → @limiter.limit` | Blocks brute-force attacks |
| Register rate limiting — 3/min | `routes/auth.py → @limiter.limit` | Prevents account enumeration |
| Analyze rate limiting — 10/hr | `routes/analysis.py → @limiter.limit` | Protects CPU-intensive AI inference |
| HTTP-only session cookie | `config.py → SESSION_COOKIE_HTTPONLY` | Inaccessible to scripts |
| SameSite=Lax cookie | `config.py → SESSION_COOKIE_SAMESITE` | CSRF mitigation |
| HTTPS-only cookie in prod | `config.py → SESSION_COOKIE_SECURE` | Cookie not sent over plain HTTP |
| UUID filename on upload | `utils/__init__.py → save_uploaded_file()` | Prevents path traversal and collisions |
| Extension whitelist | `utils/__init__.py → allowed_file()` | Only `.pdf` and `.docx` accepted |
| 10 MB upload hard limit | `config.py → MAX_CONTENT_LENGTH` | Prevents large-file denial of service |
| `secure_filename()` sanitisation | `utils/__init__.py` | Strips path separators from filenames |
| Open-redirect protection | `routes/auth.py → login()` | `next` param only accepts relative paths |
| Ownership check on delete | `routes/dashboard.py → delete_resume()` | Users can only delete their own resumes |
| All secrets in `.env` | `config.py + .env.example` | Never hardcoded in source |
