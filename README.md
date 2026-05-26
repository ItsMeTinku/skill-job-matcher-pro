# SkillMatch AI — Semantic Skill & Job Matching Platform

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/Flask-3.0-000000?style=for-the-badge&logo=flask&logoColor=white"/>
  <img src="https://img.shields.io/badge/PostgreSQL-Supabase-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white"/>
  <img src="https://img.shields.io/badge/SQLite-Dev_Fallback-003B57?style=for-the-badge&logo=sqlite&logoColor=white"/>
  <img src="https://img.shields.io/badge/AI-Sentence_Transformers-FF6F00?style=for-the-badge&logo=pytorch&logoColor=white"/>
  <img src="https://img.shields.io/badge/Deploy-Gunicorn-499848?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/Status-Production_Ready-brightgreen?style=for-the-badge"/>
</p>

> An AI-powered recruitment platform that parses resumes, extracts skills with NLP, lets users add skills manually, and ranks job matches using **real semantic embeddings** — not simple keyword overlap. Built and debugged through 6 iterative development commits from prototype to production.

---

## Table of Contents

1. [Problem Statement](#-problem-statement)
2. [Original vs Upgraded — What Changed](#-original-vs-upgraded--what-changed)
3. [Development Journey — Bugs & Fixes](#-development-journey--bugs--fixes)
4. [Key Features](#-key-features)
5. [AI Workflow](#-ai-workflow)
6. [Architecture](#-architecture)
7. [Tech Stack](#-tech-stack)
8. [Project Structure](#-project-structure)
9. [Quick Start](#-quick-start)
10. [Supabase PostgreSQL Setup](#-supabase-postgresql-setup)
11. [Environment Variables](#-environment-variables)
12. [Deployment](#-deployment)
13. [Security Design](#-security-design)
14. [Rate Limiting](#-rate-limiting)
15. [Semantic Matching Explained](#-semantic-matching-explained)
16. [Skill Gap Analysis](#-skill-gap-analysis)
17. [Database Schema](#-database-schema)
18. [Future Enhancements](#-future-enhancements)

---

## 🎯 Problem Statement

Traditional recruitment platforms match candidates to jobs using **rigid keyword filtering**. A resume mentioning "ML" won't match a job asking for "Machine Learning". A candidate with "PyTorch" experience gets filtered out of a "Deep Learning" role. Candidates without a resume — or with skills that don't appear in documents — are invisible.

**SkillMatch AI** solves this on three fronts:

1. **Semantic understanding** — sentence-level embeddings understand *meaning*, not just characters
2. **Resume parsing** — automatic skill extraction from PDF and DOCX files
3. **Manual skill input** — candidates can add skills directly without uploading a document, and those skills are merged into every analysis

---

## 🔄 Original vs Upgraded — What Changed

This project started as a basic Flask skeleton with SQLite and placeholder matching logic. Here is an honest, side-by-side comparison of every dimension.

### Architecture

| Dimension | Original (v0) | Current (v1 — This Project) |
|---|---|---|
| Structure | Single `app.py`, no blueprints | Application factory + 3 blueprints (`auth`, `dashboard`, `analysis`) |
| Database | SQLite only | PostgreSQL (Supabase) in production, SQLite fallback in dev |
| ORM | Raw sqlite3 queries | SQLAlchemy 2.0 with full model layer |
| DB Driver | sqlite3 (built-in) | `psycopg[binary]` for PostgreSQL |
| Models | None (flat dict logic) | `User`, `Resume`, `Job`, `MatchResult`, `UserSkill` |
| Config | Hardcoded values | `DevelopmentConfig` / `ProductionConfig` / `TestingConfig` classes |
| Extensions | None | `Flask-Login`, `Flask-Limiter`, `Flask-SQLAlchemy` as singletons |
| WSGI | Flask dev server only | `gunicorn.conf.py` + `wsgi.py` for production |

### AI & Matching

| Dimension | Original (v0) | Current (v1) |
|---|---|---|
| Matching algorithm | Keyword count / string overlap | Sentence-transformer embeddings + cosine similarity |
| Model | None | `all-MiniLM-L6-v2` (384-dimensional dense vectors) |
| Score formula | Simple ratio | 60% semantic + 40% keyword overlap blend |
| Score display | Raw float, no normalisation | `effective_score` property — corrects edge cases where matched ≥ required |
| Skill extraction | None | 330+ skill taxonomy, boundary-aware compiled regex (LRU-cached) |
| Manual skills | Not supported | `UserSkill` model — global or resume-scoped, merged at analysis time |
| Skill normalisation | None | `normalize_skill()` — taxonomy lookup, substring match, title-case fallback |
| Resume parsing | None | `pdfplumber` (PDF) + `python-docx` (DOCX, includes tables) |

### Features

| Feature | Original (v0) | Current (v1) |
|---|---|---|
| Authentication | Basic Flask session, plain text password risk | Werkzeug PBKDF2-SHA256 hashing, Flask-Login, HTTP-only cookies |
| Rate limiting | None | 5 login/min, 3 register/min, 10 analyze/hour via Flask-Limiter |
| Manual skill entry | Not present | Full CRUD — add single or bulk (comma/semicolon separated), remove, scope to resume |
| Skill gap analysis | Not present | Per-job missing skills + global learning roadmap across all matches |
| Job browser | Not present | Paginated grid with category filter and search |
| Resume management | Not present | Delete resume + file from disk, cascade-deletes match results |
| Dashboard | Minimal | Stat cards, best-match banner, match score rings, skill cloud |
| Error pages | None | Custom 404, 500, 429 pages |
| File uploads | Unsecured | UUID-named, extension whitelist, 10 MB limit, `secure_filename` sanitisation |

### Dependencies — Old vs New

| Package | v0 | v1 | Reason for change |
|---|---|---|---|
| `psycopg2-binary` | Added | Changed to `psycopg[binary]` | `psycopg[binary]` is the modern psycopg3 driver; better async support and maintained actively |
| `numpy` | 1.26.4 | 2.2.0 | Compatibility with torch ≥ 2.6 |
| `scikit-learn` | 1.5.0 | 1.6.0 | Bug fixes in cosine_similarity edge cases |
| `torch` | `==2.3.1` | `>=2.6.0` | Removed hard pin so pip resolves compatible version per platform |
| `SQLite` | Default | Dev fallback only | PostgreSQL is the production target; SQLite retained so developers can run without a DB server |

---

## 🐛 Development Journey — Bugs & Fixes

This project was debugged across **6 git commits** after the initial production-ready scaffold. Each commit solved a real problem encountered during local testing on Windows with Python 3.13.

---

### Bug 1 — `ModuleNotFoundError: No module named 'flask_sqlalchemy'`

**Commit:** `cb12a66 fix: auth layout and template rendering`

**What happened:**
Running `python app.py` immediately crashed because the virtual environment didn't have the dependencies installed.

```
File "app.py", line 10, in <module>
    from extensions import db, limiter, login_manager
File "extensions.py", line 9, in <module>
    from flask_sqlalchemy import SQLAlchemy
ModuleNotFoundError: No module named 'flask_sqlalchemy'
```

**Root cause:** The `requirements.txt` was present but `pip install -r requirements.txt` had not been run in the active virtual environment.

**Fix:** Install all dependencies first:
```bash
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

**Lesson:** A `requirements.txt` only describes what is needed — it does not install anything automatically. Always activate the venv and run `pip install` before the first run.

---

### Bug 2 — Jinja2 `TemplateNotFound` / auth layout broken

**Commit:** `cb12a66 fix: auth layout and template rendering`

**What happened:**
After installing dependencies, the login page raised a `TemplateNotFound` error. The base template was also rendering the sidebar for unauthenticated users, causing a broken layout on the login and register pages.

**Root cause:**
- Template paths did not match the subdirectory structure (`auth/login.html` vs `login.html`)
- The `base.html` `{% if current_user.is_authenticated %}` conditional was not scoped correctly — the sidebar HTML leaked into the guest layout

**Fix in `templates/base.html`:**
- Separated the authenticated layout (sidebar + topbar + content area) from the guest layout (centered auth card) into two completely distinct `{% if %}` branches
- Added `use_reloader=False` to `app.run()` to prevent double-initialisation on Windows

```python
# app.py — added to prevent model loading twice on Windows hot-reload
app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
```

---

### Bug 3 — Dashboard templates not rendering (Jinja2 variable errors)

**Commit:** `dd5ae13 fix: stable flask rendering and dashboard layout`

**What happened:**
After logging in successfully, the dashboard, jobs, and profile pages threw `UndefinedError` for template variables — e.g. `top_matches` was undefined when no resume existed yet.

**Root cause:**
Template variables were used without `default` filters or `{% if %}` guards. When a new user had no resume, the route passed `top_matches=[]` but the template tried to access `top_matches[0]` unconditionally.

**Fix:**
Added null/empty guards in `templates/dashboard/index.html`, `jobs.html`, and `profile.html`:
```jinja2
{# Before (crashes when top_matches is empty) #}
{{ top_matches[0].job.title }}

{# After (safe) #}
{% if top_matches %}
  {{ top_matches[0].job.title }}
{% endif %}
```

---

### Bug 4 — No way to match jobs without uploading a resume

**Commit:** `29e4128 fix: added the manual page to add skills manually`

**What happened:**
Users who didn't have a resume file, or whose resume parser extracted no skills, had no way to use the matching engine. The platform was entirely blocked behind file upload.

**Fix — New feature: Manual Skill Entry**

Added a complete new subsystem:

**New model — `models/user_skill.py`:**
```python
class UserSkill(db.Model):
    __tablename__ = "user_skills"
    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    resume_id  = db.Column(db.Integer, db.ForeignKey("resumes.id"), nullable=True)
    skill_name = db.Column(db.String(200), nullable=False)
    source     = db.Column(db.String(20), default="manual")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

`resume_id=None` means the skill is **global** (applied to every analysis). `resume_id=<id>` means it is scoped to one specific resume upload.

**New routes added to `routes/dashboard.py`:**
- `GET /dashboard/manual` — dedicated manual matching page
- `POST /dashboard/skills` — add one or more skills
- `POST /dashboard/skills/remove` — remove a skill
- `GET /dashboard/skills` — skill management view
- `POST /dashboard/match_manual` — run matcher with manual skills only (no DB persistence)
- `POST /dashboard/resume/<id>/delete` — delete a resume + file from disk

**Integration in `routes/analysis.py`:**
At analysis time, manual skills are merged with extracted skills before matching runs:
```python
manual_q = UserSkill.query.filter_by(user_id=current_user.id)\
           .filter((UserSkill.resume_id == None) | (UserSkill.resume_id == resume.id)).all()
merged_skills_set = {s for s in skills_list}
merged_skills_set.update([u.skill_name for u in manual_q])
skills_list = sorted(merged_skills_set, key=str.lower)
```

---

### Bug 5 — Could only add one skill at a time

**Commit:** `2a45757 fix: now you can add multiple skills at a time`

**What happened:**
The manual skill form accepted a single text input. Typing "Python, Flask, Docker" added the full string as one skill name, not three separate skills.

**Root cause:**
`add_skill()` treated the entire input as a single skill with no splitting logic.

**Fix in `routes/dashboard.py`:**
```python
# Before — treated whole input as one skill
skill = raw_skill.strip()

# After — splits on comma, semicolon, or newline
import re
skills = [normalize_skill(s) for s in re.split(r"[;,\n]+", raw_skill) if s.strip()]
```

**New utility function added — `normalize_skill()` in `utils/skill_extractor.py`:**
Maps free-text user input to canonical taxonomy names:
```python
def normalize_skill(raw_skill: str) -> str:
    key = raw_skill.strip().lower()
    taxonomy_map = {s.lower(): s for s in SKILL_TAXONOMY}
    if key in taxonomy_map:
        return taxonomy_map[key]          # exact match → canonical
    candidates = [s for s in SKILL_TAXONOMY if key in s.lower()]
    if candidates:
        return sorted(candidates, key=len, reverse=True)[0]  # substring match
    return raw_skill.strip().title()      # fallback → title case
```

---

### Bug 6 — Match scores displayed incorrectly (score shown lower than actual)

**Commit:** `6c3a058 fix: solved sum bug and update the readme`

**What happened:**
When a candidate's skills fully covered all required skills for a job, the displayed score was still showing a value like 67% instead of 100%. The semantic embedding score was dragging the blended score down even when keyword coverage was perfect.

**Root cause:**
`match_score` stored in the DB was the 60/40 blended value computed at time of analysis. The display layer used `match_score` directly, which didn't account for the case where `matched_skills ⊇ required_skills`.

**Fix — `effective_score` property in `models/match.py`:**
```python
@property
def effective_score(self) -> float:
    """Return corrected score — bumps to 100 when all required skills are matched."""
    if self.job and self.job.required_skills:
        required_lower = {s.lower() for s in self.job.required_skills}
        matched_lower  = {s.lower() for s in self.matched_skills}
        if required_lower and required_lower <= matched_lower:
            return 100.0                          # full coverage → 100%
    if self.keyword_score is not None:
        return max(self.match_score, self.keyword_score)   # take the higher score
    return self.match_score
```

All display properties (`score_int`, `score_label`, `score_badge_class`, `progress_class`) now use `effective_score` instead of `match_score`.

---

### Bug 7 — `psycopg2-binary` installation failure on some platforms

**Commit:** `2a45757` (requirements.txt change)

**What happened:**
`psycopg2-binary` failed to build wheels on Python 3.13 / certain Windows configurations.

**Fix:**
Switched to the modern `psycopg[binary]` (psycopg3):
```
# Before
psycopg2-binary==2.9.9

# After
psycopg[binary]
```

Also added SQLite as a **local development fallback** in `DevelopmentConfig` so developers without a PostgreSQL server can still run the project:
```python
class DevelopmentConfig(BaseConfig):
    default_sqlite_uri = f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'dev.sqlite')}"
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", default_sqlite_uri)
```

---

## ✨ Key Features

| Feature | Description |
|---|---|
| **Semantic AI Matching** | `all-MiniLM-L6-v2` sentence embeddings + cosine similarity, blended 60/40 with keyword overlap |
| **Resume Parsing** | `pdfplumber` (PDF multi-column) + `python-docx` (DOCX paragraphs + tables) |
| **NLP Skill Extraction** | 330+ skill taxonomy, boundary-aware compiled regex, LRU-cached pattern compilation |
| **Manual Skill Entry** | Add individual or bulk skills (comma/semicolon separated), global or resume-scoped |
| **Skill Normalisation** | Free-text → canonical taxonomy name via `normalize_skill()` |
| **Skill Gap Analysis** | Per-job missing skills + global learning roadmap ranked by frequency |
| **Score Correction** | `effective_score` property fixes blended-score under-reporting on full skill coverage |
| **Brute-force Protection** | Flask-Limiter: 5 login/min, 3 register/min, 10 analyze/hour |
| **Secure Auth** | PBKDF2-SHA256 password hashing, HTTP-only session cookies, open-redirect protection |
| **PostgreSQL + SQLite** | Supabase PostgreSQL for production; SQLite auto-fallback for local dev |
| **Server-Side Rendering** | 100% Flask/Jinja2 — minimal JavaScript dependency |
| **Resume Management** | Delete resume + file from disk with cascade match-result cleanup |
| **Professional Dashboard** | Dark sidebar, stat cards, best-match banner, score rings, skill cloud |
| **Gunicorn Ready** | `wsgi.py` + `gunicorn.conf.py` for production deployment |

---

## 🧠 AI Workflow

```
Resume Upload (PDF / DOCX)        Manual Skill Entry
        │                                │
        ▼                                ▼
  Resume Parser                   normalize_skill()
  (pdfplumber / python-docx)      taxonomy lookup
        │                                │
        ▼                                │
  Raw Text Extraction                    │
        │                                │
        ├────────────────────────────────┘
        │         MERGED SKILL LIST
        │
        ├─────────────────────────────────────────────────┐
        ▼                                                   ▼
NLP Skill Extractor                              SentenceTransformer
(330+ taxonomy, regex)                           (all-MiniLM-L6-v2)
        │                                                   │
        ▼                                                   ▼
Extracted Skills List                         Resume Embedding Vector
        │                                                   │
        └───────────────────┬───────────────────────────────┘
                            ▼
              For each Job in database:
                ├─ Generate Job Embedding
                ├─ Cosine Similarity     → semantic_score (0–1)
                ├─ Keyword Overlap       → keyword_score  (0–100)
                ├─ Blended Score         = 60% semantic + 40% keyword
                └─ effective_score()     corrects underreported full-coverage scores
                            │
                            ▼
                  Ranked Match Results (persisted to DB)
                  + Per-job missing skills
                  + Global Learning Roadmap
                            │
                            ▼
                  Dashboard (server-side rendered)
```

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────┐
│              Browser (HTML / CSS / minimal JS)           │
│           Flask/Jinja2 Server-Side Rendering             │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP
┌──────────────────────▼──────────────────────────────────┐
│                  Gunicorn WSGI Server                    │
│  ┌────────────────────────────────────────────────────┐  │
│  │                   Flask App                        │  │
│  │  ┌──────────┐  ┌────────────┐  ┌───────────────┐  │  │
│  │  │ auth_bp  │  │dashboard_bp│  │ analysis_bp   │  │  │
│  │  │ /login   │  │/dashboard  │  │ /analyze      │  │  │
│  │  │ /register│  │/jobs       │  │ (pipeline)    │  │  │
│  │  │ /logout  │  │/profile    │  └───────┬───────┘  │  │
│  │  └──────────┘  │/skills     │          │           │  │
│  │                │/manual     │          │           │  │
│  │                └────────────┘          │           │  │
│  │  ┌─────────────────────────────────────▼─────────┐ │  │
│  │  │                Utils Layer                    │ │  │
│  │  │  parser.py │ skill_extractor.py │ matcher.py  │ │  │
│  │  └─────────────────────────────────────┬─────────┘ │  │
│  └───────────────────────────────────────┼────────────┘  │
└──────────────────────────────────────────┼───────────────┘
                                           │
       ┌───────────────────────────────────▼──────────────┐
       │            Database Layer                        │
       │  PostgreSQL (Supabase)  /  SQLite (dev fallback) │
       │  users │ resumes │ jobs │ match_results          │
       │  user_skills                                     │
       └──────────────────────────────────────────────────┘
```

---

## 🛠 Tech Stack

**Backend**
- Flask 3.0 (application factory, blueprints)
- Flask-Login 0.6 (session management, `@login_required`)
- Flask-Limiter 3.7 (rate limiting per IP)
- Flask-SQLAlchemy 3.1 (ORM)

**Frontend**
- Jinja2 server-side templates
- Bootstrap 5.3 (CSS only)
- Bootstrap Icons
- Custom CSS (~700 lines, dark sidebar, gradient cards)
- Minimal JavaScript (skill management UX only)

**AI / ML**
- `sentence-transformers` — `all-MiniLM-L6-v2` model
- `scikit-learn 1.6` — cosine similarity
- Custom 330+ skill NLP taxonomy with boundary-aware compiled regex
- `normalize_skill()` — maps free-text input to canonical skill names

**Database**
- PostgreSQL via Supabase (production)
- SQLite (development fallback — no server needed)
- SQLAlchemy 2.0 ORM + `psycopg[binary]` driver

**Security**
- Werkzeug `generate_password_hash` (PBKDF2-SHA256)
- Flask-Limiter brute-force protection
- HTTP-only session cookies, SameSite=Lax
- UUID-named file uploads, extension whitelist

**Deployment**
- Gunicorn 22 + `gunicorn.conf.py`
- Environment-based config classes (Dev / Prod / Test)

---

## 📁 Project Structure

```
skill-job-matcher/
│
├── app.py                  # Application factory + WSGI entry
├── config.py               # Dev / Prod / Test config classes (SQLite fallback in dev)
├── extensions.py           # Extension singletons (db, limiter, login_manager)
├── wsgi.py                 # Gunicorn entry point
├── gunicorn.conf.py        # Gunicorn production settings
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
│
├── models/
│   ├── __init__.py
│   ├── user.py             # User model + Flask-Login mixin + manual_skills relationship
│   ├── resume.py           # Resume metadata + parsed content
│   ├── job.py              # Job listings (seeded from data/jobs.py)
│   ├── match.py            # MatchResult — scores + effective_score fix + skill gap
│   └── user_skill.py       # ★ NEW — manual skills (global or resume-scoped)
│
├── routes/
│   ├── auth.py             # /login  /register  /logout  (rate-limited)
│   ├── dashboard.py        # /dashboard  /jobs  /profile  /skills  /manual  /delete
│   └── analysis.py         # /analyze — full AI pipeline (merges manual skills)
│
├── utils/
│   ├── __init__.py         # File upload helpers (UUID naming, extension check)
│   ├── parser.py           # PDF/DOCX parser (pdfplumber + python-docx)
│   ├── skill_extractor.py  # 330+ skill taxonomy + normalize_skill() ★ NEW
│   └── matcher.py          # Semantic AI engine (embeddings + cosine similarity)
│
├── data/
│   └── jobs.py             # 25 rich job descriptions (auto-seeded on first run)
│
├── templates/
│   ├── base.html           # Split layout: sidebar (auth) / centered card (guest)
│   ├── auth/
│   │   ├── login.html
│   │   └── register.html
│   ├── dashboard/
│   │   ├── index.html      # Main dashboard — matches, skill cloud, gap roadmap
│   │   ├── jobs.html       # Paginated job browser with category filter
│   │   ├── profile.html    # Account info + resume history + delete buttons
│   │   ├── skills.html     # ★ NEW — manual skill management view
│   │   ├── manual.html     # ★ NEW — manual skill entry + match without resume
│   │   └── manual_matches.html  # ★ NEW — results from manual-only matching
│   └── errors/
│       ├── 404.html
│       ├── 500.html
│       └── 429.html
│
├── static/
│   ├── css/main.css        # Full custom CSS
│   └── js/dashboard.js     # ★ NEW — minimal JS for skill form UX
│
├── uploads/                # UUID-named resume files (gitignored)
└── instance/               # SQLite dev DB lives here (gitignored)
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- A database: [Supabase](https://supabase.com) (free tier) **or** nothing — SQLite is used automatically in development

### 1. Clone & create virtual environment

```bash
git clone https://github.com/YOUR_USERNAME/skill-job-matcher.git
cd skill-job-matcher

python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

> **Windows / Python 3.13 note:** If `psycopg[binary]` fails, ensure you have Visual C++ Build Tools installed, or run SQLite-only mode (no `DATABASE_URL` in `.env`).

### 3. Configure environment

```bash
cp .env.example .env
```

Edit `.env`:
```env
SECRET_KEY=your-long-random-secret-key
FLASK_ENV=development
# Leave DATABASE_URL empty for automatic SQLite fallback
# DATABASE_URL=postgresql://...
```

Generate a strong secret key:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 4. Run

```bash
# Development (SQLite fallback, auto-creates tables + seeds 25 jobs)
python app.py

# Or with Flask CLI
flask run
```

Open [http://localhost:5000](http://localhost:5000) → Register → Upload a resume or enter skills manually.

### 5. Production (Gunicorn)

```bash
FLASK_ENV=production gunicorn -c gunicorn.conf.py wsgi:application
```

---

## 🟢 Supabase PostgreSQL Setup

1. Create a free project at [supabase.com](https://supabase.com)
2. **Project Settings → Database → Connection string → URI**
3. Select **Session mode** (port 5432)
4. Copy the URI and set it in `.env`:

```env
DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
FLASK_ENV=production
```

> Tables and the job seed dataset are created automatically on first startup via `db.create_all()`.

---

## 🔐 Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `SECRET_KEY` | ✅ | random (insecure) | Flask session signing key — must be set in production |
| `FLASK_ENV` | ✅ | `production` | `development`, `production`, or `testing` |
| `DATABASE_URL` | ❌ | SQLite (dev only) | PostgreSQL URI — required for production |
| `SENTENCE_TRANSFORMER_MODEL` | ❌ | `all-MiniLM-L6-v2` | Sentence-transformer model name |
| `PORT` | ❌ | `8000` | Gunicorn bind port |
| `WEB_CONCURRENCY` | ❌ | `2` | Gunicorn worker count |

---

## ☁️ Deployment

### Render (recommended)

1. Push to GitHub
2. New Web Service → connect repo
3. **Build command:** `pip install -r requirements.txt`
4. **Start command:** `gunicorn -c gunicorn.conf.py wsgi:application`
5. Add environment variables: `SECRET_KEY`, `DATABASE_URL`, `FLASK_ENV=production`

### Railway

```bash
railway init
railway up
```

Set environment variables in the Railway dashboard.

### Important for any host
- Set `FLASK_ENV=production` — enables `SESSION_COOKIE_SECURE=True` (HTTPS-only cookies)
- Use 1–2 Gunicorn workers if loading the ML model to avoid out-of-memory issues
- The sentence-transformer model (~90 MB) downloads on first run — the host needs outbound internet access

---

## 🔒 Security Design

### Password Storage

Raw passwords are never stored or logged. Werkzeug PBKDF2-SHA256 is used with a unique random salt per password:

```python
from werkzeug.security import generate_password_hash, check_password_hash

user.password_hash = generate_password_hash(plain_text)          # store
is_valid = check_password_hash(user.password_hash, plain_text)   # verify
```

### Session Security

- Signed cookie with `SECRET_KEY` (HMAC)
- `SESSION_COOKIE_HTTPONLY = True` — inaccessible to scripts
- `SESSION_COOKIE_SAMESITE = "Lax"` — CSRF mitigation
- `SESSION_COOKIE_SECURE = True` in production (HTTPS only)

### File Upload Security

- `secure_filename()` sanitises all filenames
- UUID prefix on stored filename prevents path traversal and collisions
- Extension whitelist: only `.pdf` and `.docx`
- 10 MB hard limit via `MAX_CONTENT_LENGTH`

### Route Protection

All dashboard, analysis, and skill routes use `@login_required`. The `next` redirect parameter only accepts relative paths — prevents open-redirect attacks.

---

## 🛡 Rate Limiting

Flask-Limiter enforces per-IP limits. Exceeding a limit returns HTTP 429 with a custom error page.

| Route | Limit | Reason |
|---|---|---|
| `POST /login` | **5 per minute** | Brute-force login attack prevention |
| `POST /register` | **3 per minute** | Account enumeration / spam prevention |
| `POST /analyze` | **10 per hour** | AI inference is CPU-intensive |
| All routes | 200/day · 50/hour | General DDoS baseline |

---

## 🤖 Semantic Matching Explained

### Why not keyword matching?

```
Resume says:  "built ML pipelines with PyTorch"
Job requires: "Machine Learning", "Deep Learning"
Keyword match: 0%   ← completely wrong
Semantic match: ~82% ← understands they are related
```

### How it works

1. **Resume profile** = extracted skills + first 400 words of resume text
2. **Job profile** = job description + required skills list
3. Both are encoded by `SentenceTransformer("all-MiniLM-L6-v2")` → 384-dimensional vectors
4. **Cosine similarity** gives a score 0 (unrelated) to 1 (identical meaning)
5. Final score = `(0.60 × semantic%) + (0.40 × keyword_overlap%)`
6. **`effective_score`** corrects the result upward when all required skills are matched

```python
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

model      = SentenceTransformer("all-MiniLM-L6-v2")
embeddings = model.encode([resume_profile, job_profile])
score      = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
```

### Why `all-MiniLM-L6-v2`?

- 22M parameters — fast CPU inference (~50–200ms per batch)
- Trained specifically for semantic similarity (not just language modelling)
- 384-dimensional embeddings — compact but expressive
- MIT licensed, fully offline after first download (~90 MB)

---

## 📊 Skill Gap Analysis

For every job match the platform computes:

- **Matched skills** — present in both resume and job requirements
- **Missing skills** — required by the job but absent from the resume

The **Learning Roadmap** on the dashboard aggregates missing skills across *all* job matches, ranking by frequency — giving a prioritised learning plan for the roles you're closest to qualifying for.

```
Resume:       Python ✓  Flask ✓  SQL ✓  Docker ✓  Git ✓
Job requires: Python ✓  Flask ✓  SQL ✓  Docker ✓  Kubernetes ✗  AWS ✗  Terraform ✗

Matched:  5 skills
Missing:  Kubernetes, AWS, Terraform
Score:    71% (effective_score = max(blended, keyword_overlap))
```

---

## 🗄 Database Schema

```sql
-- Users
CREATE TABLE users (
    id            SERIAL PRIMARY KEY,
    full_name     VARCHAR(120) NOT NULL,
    email         VARCHAR(254) UNIQUE NOT NULL,
    password_hash VARCHAR(256) NOT NULL,
    created_at    TIMESTAMP DEFAULT NOW(),
    last_login    TIMESTAMP,
    is_active     BOOLEAN DEFAULT TRUE
);

-- Resumes
CREATE TABLE resumes (
    id                SERIAL PRIMARY KEY,
    user_id           INT REFERENCES users(id) ON DELETE CASCADE,
    original_filename VARCHAR(255),
    stored_filename   VARCHAR(255),   -- UUID-named on disk
    file_type         VARCHAR(10),    -- 'pdf' or 'docx'
    raw_text          TEXT,
    extracted_skills  TEXT,           -- comma-separated canonical names
    education_info    TEXT,
    certifications    TEXT,
    uploaded_at       TIMESTAMP DEFAULT NOW(),
    processed_at      TIMESTAMP
);

-- Jobs (auto-seeded from data/jobs.py)
CREATE TABLE jobs (
    id               SERIAL PRIMARY KEY,
    title            VARCHAR(200) NOT NULL,
    description      TEXT NOT NULL,
    category         VARCHAR(100),
    experience_level VARCHAR(50),
    required_skills  TEXT,           -- JSON array of lowercase skill names
    created_at       TIMESTAMP DEFAULT NOW(),
    is_active        BOOLEAN DEFAULT TRUE
);

-- Match Results
CREATE TABLE match_results (
    id              SERIAL PRIMARY KEY,
    resume_id       INT REFERENCES resumes(id) ON DELETE CASCADE,
    job_id          INT REFERENCES jobs(id),
    match_score     FLOAT NOT NULL,   -- 0–100 blended score
    semantic_score  FLOAT,            -- raw cosine 0–1
    keyword_score   FLOAT,            -- keyword overlap 0–100
    matched_skills  TEXT,             -- JSON array
    missing_skills  TEXT,             -- JSON array
    created_at      TIMESTAMP DEFAULT NOW()
);

-- Manual Skills (NEW)
CREATE TABLE user_skills (
    id         SERIAL PRIMARY KEY,
    user_id    INT REFERENCES users(id) ON DELETE CASCADE,
    resume_id  INT REFERENCES resumes(id) ON DELETE CASCADE,  -- NULL = global
    skill_name VARCHAR(200) NOT NULL,
    source     VARCHAR(20) DEFAULT 'manual',
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 🔮 Future Enhancements

- [ ] **Cover letter generator** — AI-drafted letter tailored to each job match
- [ ] **Email job alerts** — notify users of new high-match jobs (Celery + Redis)
- [ ] **Admin panel** — manage jobs, users, system analytics
- [ ] **Recruiter mode** — search and rank candidates for a given job description
- [ ] **OAuth login** — Google / LinkedIn sign-in via Flask-Dance
- [ ] **Redis rate limiting** — distributed limits across multiple Gunicorn workers
- [ ] **Resume builder** — guided form that outputs a formatted resume PDF
- [ ] **Alembic migrations** — full schema migration history for schema evolution
- [ ] **Multi-language resumes** — multilingual sentence-transformer model support
- [ ] **REST API** — expose `/api/match` endpoint for external integrations
- [ ] **Embedding cache** — cache job embeddings in Redis to skip re-encoding on every upload

---

## 👤 Author

Built as a production-quality AI/ML portfolio project — scaffolded, debugged through 6 real development iterations, and extended with new features based on actual usage gaps discovered during testing.

Demonstrates: Flask application factory architecture · Semantic NLP with sentence-transformers · PostgreSQL with ORM · Secure authentication · Rate limiting · Manual skill management · Responsive CSS design · Real debugging practice.

---

## 📄 License

MIT License — free to use, modify, and distribute.
