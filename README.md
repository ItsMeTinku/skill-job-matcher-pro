<div align="center">

# Skill Job Matcher Pro

### AI-Powered Semantic Recruitment & Career Intelligence Platform

*Matching candidates to opportunities through contextual understanding — not keyword coincidence.*

---

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0-000000?style=flat-square&logo=flask&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Supabase-3ECF8E?style=flat-square&logo=supabase&logoColor=white)
![AI](https://img.shields.io/badge/AI-SentenceTransformers-FF6F00?style=flat-square&logo=pytorch&logoColor=white)
![NLP](https://img.shields.io/badge/NLP-Semantic_Embeddings-8B5CF6?style=flat-square)
![Security](https://img.shields.io/badge/Security-Rate_Limited_Auth-DC2626?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-22C55E?style=flat-square)
![Status](https://img.shields.io/badge/Status-Production_Ready-0EA5E9?style=flat-square)

</div>

---

## Overview

**Skill Job Matcher Pro** is a production-grade recruitment intelligence platform that replaces brittle keyword filtering with transformer-based semantic matching. It ingests a candidate's resume — or a manually curated skill profile — generates dense vector embeddings using `all-MiniLM-L6-v2`, and scores every job in the database against that representation using cosine similarity.

The result is a ranked list of opportunities with explainable match scores, per-job skill gap analysis, and a global learning roadmap — all rendered server-side through a secure, rate-limited Flask application backed by Supabase PostgreSQL.

**Built for:** developers building a portfolio that demonstrates real AI/ML integration, and candidates who want to understand precisely where their profile sits relative to the market.

---

## Table of Contents

1. [The Problem with Keyword Matching](#1-the-problem-with-keyword-matching)
2. [Why Semantic Embeddings](#2-why-semantic-embeddings)
3. [AI Workflow](#3-ai-workflow)
4. [Architecture](#4-architecture)
5. [Security](#5-security)
6. [Feature Set](#6-feature-set)
7. [Tech Stack](#7-tech-stack)
8. [Project Structure](#8-project-structure)
9. [Installation](#9-installation)
10. [Environment Variables](#10-environment-variables)
11. [Screenshots](#11-screenshots)
12. [Deployment](#12-deployment)
13. [Future Roadmap](#13-future-roadmap)

---

## 1. The Problem with Keyword Matching

Most applicant tracking systems and job boards evaluate fit by scanning a resume for exact string matches against a job description. This approach is fast to implement and easy to explain — and it consistently produces wrong results.

Consider a senior candidate whose resume describes building "ML pipelines with PyTorch and distributed training on AWS". A job posting asks for experience in "Machine Learning", "Deep Learning", and "cloud infrastructure". A keyword filter compares character sequences. It finds no overlap with "ML", partial overlap with "cloud", and nothing for "Deep Learning" — and rejects the candidate.

The failure mode is symmetric. Junior candidates who have learned to game ATS systems by pasting exact job-description phrases into a hidden white-on-white text block score higher than qualified candidates who simply wrote their resume in plain professional language.

**The underlying issue:** keyword matching treats text as a bag of unrelated tokens. It has no model of meaning, no understanding of domain synonymy, and no mechanism for recognising that "Backend Engineer" and "Python Developer" describe substantially overlapping skill sets.

| Keyword Match | Reality |
|---|---|
| "ML Engineer" ≠ "AI Developer" | Same role, different titles |
| "PostgreSQL" ≠ "relational databases" | Same concept, different specificity |
| "Python" ≠ "Flask, Django, FastAPI" | Subset relationship, not equivalence |
| "cloud infrastructure" ≠ "AWS, GCP, Azure" | Abstraction vs. implementation |

Semantic matching resolves all four of these correctly because it operates on meaning, not characters.

---

## 2. Why Semantic Embeddings

### What an Embedding Is

A text embedding is a fixed-length numerical vector that encodes the semantic content of a passage. Two passages that describe similar concepts — regardless of the specific words used — will produce vectors that are geometrically close in the embedding space. Two passages describing unrelated concepts will produce vectors that are far apart.

`all-MiniLM-L6-v2`, the model used in this system, is a 22-million-parameter sentence transformer trained specifically on semantic similarity tasks. It maps any passage of text to a 384-dimensional dense vector. The model is compact enough for CPU inference (50–200ms per batch) while retaining strong performance on domain-specific vocabulary including technical skill names, job titles, and engineering terminology.

### How Similarity Is Computed

Given a resume profile vector **r** and a job profile vector **j**, similarity is computed as cosine similarity — the cosine of the angle between the two vectors in 384-dimensional space:

```
similarity(r, j) = (r · j) / (‖r‖ × ‖j‖)
```

This produces a value between 0 (orthogonal — no semantic relationship) and 1 (identical direction — strong semantic alignment). The result is scale-invariant: a short skills list and a long resume produce comparable scores because direction, not magnitude, determines the output.

### The Blended Scoring Strategy

Pure semantic similarity alone has a weakness: a resume that uses eloquent prose about "building scalable systems" may score high against a job requiring specific tools like Kubernetes and Terraform even when the candidate has never used those tools. Conversely, a candidate who has used those tools but wrote a terse resume may score lower than deserved.

This system addresses that by blending two complementary signals:

```
final_score = (0.60 × semantic_score%) + (0.40 × keyword_overlap%)
```

The semantic component captures contextual alignment. The keyword component directly rewards explicit skill coverage. The 60/40 split was chosen to weight understanding above vocabulary while preserving the signal from direct skill matches.

A post-processing correction (`effective_score`) handles the edge case where a candidate's skill set fully covers all required skills for a role — in which case the score is normalised to 100% regardless of the semantic component's contribution.

### What This Means for Match Quality

| Scenario | Keyword System | This System |
|---|---|---|
| Same role, different title | ❌ No match | ✅ High similarity |
| Framework listed, language not | ❌ Partial match | ✅ Inferred relationship |
| Terse resume, relevant experience | ❌ Low score | ✅ Context recognised |
| Buzzword-stuffed resume, weak skills | ✅ High score | ⚠️ Penalised by keyword overlap |
| Full skill coverage | ❌ Possible undercount | ✅ Corrected to 100% |

---

## 3. AI Workflow

Every resume analysis runs through a deterministic pipeline. Each stage has a single responsibility and fails explicitly with a user-visible error if it cannot proceed.

```
┌─────────────────────────────────────────────────────────────┐
│  STAGE 1 — Ingestion                                        │
│                                                             │
│  User uploads PDF or DOCX via the secure upload form.       │
│  File is validated (extension whitelist, 10 MB hard limit), │
│  renamed to a UUID to prevent path traversal, and saved     │
│  to the uploads/ directory.                                 │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│  STAGE 2 — Parsing                                          │
│                                                             │
│  utils/parser.py dispatches to pdfplumber (PDF) or          │
│  python-docx (DOCX). Text is extracted page by page,        │
│  including table cells. Section heuristics identify         │
│  education and certification blocks for structured storage. │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│  STAGE 3 — Skill Extraction                                 │
│                                                             │
│  utils/skill_extractor.py runs the raw text against a       │
│  261-entry curated skill taxonomy. Each skill has a         │
│  compiled, LRU-cached boundary-aware regex pattern.         │
│  Longer phrases match before shorter substrings to          │
│  prevent partial hits. Output is a sorted list of           │
│  canonical skill names.                                     │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│  STAGE 4 — Manual Skill Merge                               │
│                                                             │
│  Any skills the user has added manually (via /skills or     │
│  /manual) are fetched from the user_skills table and        │
│  merged into the extracted skill set using set union.       │
│  normalize_skill() maps free-text input to canonical        │
│  taxonomy names before merge.                               │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│  STAGE 5 — Embedding Generation                             │
│                                                             │
│  utils/matcher.py builds a resume profile string:           │
│  "Skills: <skill list>. Experience: <first 400 words>"      │
│  and a job profile string per listing:                      │
│  "Job: <title>. Skills required: <skills>. <description>"   │
│                                                             │
│  SentenceTransformer("all-MiniLM-L6-v2") encodes all        │
│  strings in a single batch call, producing 384-dimensional  │
│  numpy arrays. The model is loaded once per process and     │
│  cached in memory (thread-safe lazy load with a lock).      │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│  STAGE 6 — Cosine Similarity                                │
│                                                             │
│  sklearn.metrics.pairwise.cosine_similarity computes the    │
│  similarity between the resume embedding and every job      │
│  embedding in a single matrix operation (1 × n_jobs).       │
│  Output is the semantic_score for each job.                 │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│  STAGE 7 — Keyword Overlap Scoring                          │
│                                                             │
│  For each job, the candidate's skill set is intersected     │
│  with the job's required_skills list (case-normalised).     │
│  keyword_score = |matched| / |required| × 100               │
│  matched_skills and missing_skills are recorded per job.    │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│  STAGE 8 — Score Blending & Ranking                         │
│                                                             │
│  blended = (0.60 × semantic_pct) + (0.40 × keyword_score)   │
│  Results are sorted descending by blended score.            │
│  effective_score() post-processes: full keyword coverage    │
│  → 100%; blended < keyword_score → use keyword_score.       │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│  STAGE 9 — Persistence                                      │
│                                                             │
│  One Resume row and up to 25 MatchResult rows are           │
│  written to PostgreSQL in a single transaction.             │
│  matched_skills and missing_skills stored as JSON arrays.   │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│  STAGE 10 — Skill Gap Analysis & Dashboard                  │
│                                                             │
│  The dashboard aggregates missing_skills across all matches │
│  ranked by frequency — producing a global learning roadmap. │
│  The top 10 matches, skill cloud, and gap analysis are      │
│  rendered server-side via Jinja2 and returned as HTML.      │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. Architecture

### Application Layer

The Flask application is structured using the **application factory pattern**. No global `app` object is created at module import time — instead, `create_app()` instantiates Flask, applies configuration, initialises extensions, registers blueprints, seeds the database, and returns the configured application. This design enables clean environment switching, straightforward unit testing with `TestingConfig`, and avoids circular import issues between models, extensions, and routes.

Three blueprints handle all request routing:

| Blueprint | Prefix | Responsibility |
|---|---|---|
| `auth_bp` | `/` | Registration, login, logout |
| `dashboard_bp` | `/dashboard` | UI pages — dashboard, job browser, profile, skills, manual matching |
| `analysis_bp` | `/` | The `/analyze` POST route — owns the full AI pipeline |

Extensions (`db`, `limiter`, `login_manager`) are instantiated in `extensions.py` without an app object and wired to the application via `.init_app()` inside the factory. This singleton pattern is the standard approach for avoiding circular imports in non-trivial Flask applications.

### Database Layer

SQLAlchemy 2.0 ORM manages all database interaction. Five models define the schema:

```
users
  │
  ├── resumes ─────────── match_results ── jobs
  │         (1:many)           (many:1)
  │
  └── user_skills
        resume_id nullable:
          NULL  → global skill (applied to every analysis)
          <id>  → scoped to one specific resume
```

The `MatchResult` model stores both raw scores (`match_score`, `semantic_score`, `keyword_score`) and derived arrays (`matched_skills`, `missing_skills`) as JSON text columns. The `effective_score` property computes the corrected display score at read time without requiring a database write — keeping the persistence layer simple and the display layer accurate.

### Configuration Strategy

Three configuration classes inherit from `BaseConfig`:

- **`DevelopmentConfig`** — falls back to a local SQLite file if `DATABASE_URL` is not set, enabling zero-setup local development
- **`ProductionConfig`** — requires a PostgreSQL URI, enforces HTTPS-only session cookies
- **`TestingConfig`** — in-memory SQLite, disables CSRF, used by the test suite

The active class is selected by the `FLASK_ENV` environment variable. All secrets are read from environment variables — never hardcoded.

### Rendering Strategy

All pages are rendered server-side using Jinja2 templates. There is no client-side routing, no API layer consumed by a JavaScript frontend, and no SPA framework. This keeps the attack surface small, eliminates an entire class of CORS and token-storage vulnerabilities, and produces pages that are functional without JavaScript enabled.

---

## 5. Security

Production systems are not an afterthought here. Security controls are applied at every layer of the stack.

### Authentication

Passwords are hashed using Werkzeug's `generate_password_hash`, which applies PBKDF2-SHA256 with a randomly generated salt per password. The plain-text password exists in memory only for the duration of the hash computation and is never written to any log, database column, or session variable.

```python
# Storage — one-way hash, never reversible
user.password_hash = generate_password_hash(plain_text)

# Verification — constant-time comparison prevents timing attacks
is_valid = check_password_hash(user.password_hash, plain_text)
```

Flask-Login manages session state. The session cookie is:

| Property | Value | Why |
|---|---|---|
| `HttpOnly` | `True` | Inaccessible to JavaScript — prevents XSS cookie theft |
| `SameSite` | `Lax` | Cookie not sent on cross-origin POST requests — CSRF mitigation |
| `Secure` | `True` in production | Cookie only transmitted over HTTPS |
| Lifetime | 1 hour | Limits exposure window for a stolen session |

### Brute-Force Protection

Flask-Limiter enforces per-IP rate limits using the `get_remote_address` key function:

| Endpoint | Limit | Rationale |
|---|---|---|
| `POST /login` | **5 requests / minute** | Limits password guessing to impractical speed |
| `POST /register` | **3 requests / minute** | Prevents automated account creation |
| `POST /analyze` | **10 requests / hour** | Protects CPU-intensive AI inference from abuse |
| Global baseline | 200 / day · 50 / hour | Baseline DDoS mitigation |

Exceeding any limit returns HTTP 429 with a custom error page — no stack trace, no internal detail.

### File Upload Security

Every uploaded file passes four validation gates before the parser sees it:

1. **Extension whitelist** — only `.pdf` and `.docx` are accepted; the check reads the extension after the last `.`, not the MIME type header which is trivially spoofed
2. **Size limit** — Flask's `MAX_CONTENT_LENGTH = 10 MB` hard limit rejects oversized payloads at the WSGI layer before Python processes the body
3. **Filename sanitisation** — `werkzeug.utils.secure_filename()` strips path separators, null bytes, and directory traversal sequences from the original filename
4. **UUID renaming** — the sanitised filename is discarded; the file is stored under a randomly generated UUID with only the original extension preserved, preventing enumeration and path prediction

### Route Protection

Every dashboard, analysis, and skill management route carries `@login_required` from Flask-Login. Unauthenticated requests are redirected to `/login` with the original URL preserved as the `next` parameter. The login handler validates that `next` is a relative path before following it — preventing open-redirect attacks where an attacker crafts a login URL that redirects to a malicious external site after authentication.

Ownership is verified before destructive operations. A user attempting to delete another user's resume receives HTTP 403 — the application does not expose whether the resource exists.

---

## 6. Feature Set

**AI Matching Engine**
- Semantic job matching via `all-MiniLM-L6-v2` sentence embeddings and cosine similarity
- Blended scoring: 60% semantic similarity + 40% keyword overlap
- `effective_score` correction — full keyword coverage is normalised to 100%
- Ranked results across 24 curated job listings spanning 14 industry categories
- Per-job skill gap analysis with matched and missing skill arrays

**Resume Intelligence**
- PDF parsing via `pdfplumber` — handles multi-column layouts and embedded tables
- DOCX parsing via `python-docx` — extracts paragraphs and table cell content
- Section heuristics for education and certification block detection
- 261-entry curated NLP skill taxonomy with boundary-aware compiled regex patterns

**Manual Skill System**
- Skill entry without file upload — useful when no document is available
- Bulk entry via comma or semicolon-separated input
- `normalize_skill()` maps free text to canonical taxonomy names
- Global skills applied to every analysis; resume-scoped skills applied to one
- Full CRUD: add, remove, scope management

**Career Analysis Dashboard**
- Stat cards: total resumes analysed, jobs in database, skills detected, top match score
- Top-match banner with visual score ring per job
- Global learning roadmap: missing skills ranked by frequency across all matches
- Paginated job browser with category filter and full-text search

**Platform Infrastructure**
- Application factory pattern with three registered blueprints
- Supabase PostgreSQL in production; SQLite auto-fallback for local development
- Gunicorn WSGI server with configurable workers and 120-second AI timeout
- Environment-based configuration classes (Development / Production / Testing)
- Custom 404, 500, and 429 error pages

---

## 7. Tech Stack

**Backend**

| Package | Version | Role |
|---|---|---|
| Flask | 3.0 | Web framework, routing, templating |
| Flask-Login | 0.6 | Session management, route protection |
| Flask-Limiter | 3.7 | Rate limiting, brute-force protection |
| Flask-SQLAlchemy | 3.1 | ORM integration |
| SQLAlchemy | 2.0 | Database models, query construction |
| Werkzeug | 3.0 | Password hashing, file utilities |
| Gunicorn | 22 | Production WSGI server |
| python-dotenv | 1.0 | Environment variable loading |

**AI / Machine Learning**

| Package | Version | Role |
|---|---|---|
| sentence-transformers | 3.0 | `all-MiniLM-L6-v2` embedding model |
| torch | ≥ 2.6 | Model inference backend |
| scikit-learn | 1.6 | Cosine similarity matrix computation |
| numpy | 2.2 | Embedding array manipulation |

**Resume Processing**

| Package | Version | Role |
|---|---|---|
| pdfplumber | 0.11 | PDF text and table extraction |
| python-docx | 1.1 | DOCX paragraph and table extraction |

**Database**

| Component | Role |
|---|---|
| PostgreSQL (Supabase) | Production database |
| psycopg[binary] | PostgreSQL driver (psycopg3) |
| SQLite | Local development fallback |

---

## 8. Project Structure

```
skill-job-matcher/
│
├── app.py                   # Application factory, blueprint registration,
│                            # DB table creation, job seeding, error handlers
│
├── config.py                # DevelopmentConfig / ProductionConfig / TestingConfig
├── extensions.py            # db, limiter, login_manager — instantiated without app
├── wsgi.py                  # Gunicorn entry point: application = create_app()
├── gunicorn.conf.py         # Workers, timeout, bind port, logging
├── requirements.txt
├── .env.example
├── .gitignore
│
├── models/
│   ├── user.py              # User, password hashing, Flask-Login mixin
│   ├── resume.py            # Resume metadata, parsed content, skills_list property
│   ├── job.py               # Job listings, required_skills JSON column
│   ├── match.py             # MatchResult, blended scores, effective_score property
│   └── user_skill.py        # Manual skills — NULL resume_id = global scope
│
├── routes/
│   ├── auth.py              # /login (5/min), /register (3/min), /logout
│   ├── dashboard.py         # /dashboard, /jobs, /profile, /skills,
│   │                        # /manual, /match_manual, /resume/<id>/delete
│   └── analysis.py          # /analyze (10/hr) — full AI pipeline
│
├── utils/
│   ├── __init__.py          # save_uploaded_file(), allowed_file() — UUID renaming
│   ├── parser.py            # pdfplumber + python-docx, section heuristics
│   ├── skill_extractor.py   # 261-entry taxonomy, compiled regex, normalize_skill()
│   └── matcher.py           # SentenceTransformer, cosine_similarity, gap analysis
│
├── data/
│   └── jobs.py              # 24 job listings across 14 categories — auto-seeded
│
├── templates/
│   ├── base.html            # Split layout: sidebar (auth) / centered card (guest)
│   ├── auth/
│   │   ├── login.html
│   │   └── register.html
│   ├── dashboard/
│   │   ├── index.html       # Main dashboard
│   │   ├── jobs.html        # Paginated job browser
│   │   ├── profile.html     # Account info, resume history, delete
│   │   ├── skills.html      # Manual skill management
│   │   ├── manual.html      # Skill entry + match without upload
│   │   └── manual_matches.html
│   └── errors/
│       ├── 404.html
│       ├── 500.html
│       └── 429.html
│
├── static/
│   ├── css/main.css         # Dark sidebar, gradient cards, responsive layout
│   └── js/dashboard.js      # Minimal JS for skill form UX only
│
├── uploads/                 # UUID-named resume files (not committed)
└── instance/                # SQLite dev database (not committed)
```

---

## 9. Installation

### Prerequisites

- Python 3.11 or later
- A database: [Supabase](https://supabase.com) free tier, or nothing — SQLite is used automatically in development

### Clone and create a virtual environment

```bash
git clone https://github.com/YOUR_USERNAME/skill-job-matcher.git
cd skill-job-matcher

python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### Install dependencies

```bash
pip install -r requirements.txt
```

The sentence-transformer model (~90 MB) downloads automatically on first analysis run. The host needs outbound internet access for the initial download; subsequent runs use the local cache.

### Configure environment

```bash
cp .env.example .env
```

Edit `.env` with your values — see [Environment Variables](#10-environment-variables) below.

### Run

```bash
# Development — SQLite created automatically, 24 jobs seeded on first startup
python app.py

# Production
gunicorn -c gunicorn.conf.py wsgi:application
```

Open [http://localhost:5000](http://localhost:5000). Register an account, then upload a resume or navigate to **Manual Skills** to enter your profile directly.

---

## 10. Environment Variables

| Variable | Required | Description |
|---|---|---|
| `SECRET_KEY` | **Yes** | Flask session signing key. Must be at least 32 random bytes. Never reuse across environments. |
| `DATABASE_URL` | Production only | Full PostgreSQL URI. If absent in development, SQLite is used automatically. |
| `FLASK_ENV` | **Yes** | `development`, `production`, or `testing`. Controls config class selection and cookie security. |
| `SENTENCE_TRANSFORMER_MODEL` | No | Override the embedding model. Default: `all-MiniLM-L6-v2`. |
| `PORT` | No | Gunicorn bind port. Default: `8000`. |
| `WEB_CONCURRENCY` | No | Gunicorn worker count. Default: `2`. Keep at 1–2 if memory is constrained — the model consumes ~300 MB per worker. |

Generate a cryptographically strong `SECRET_KEY`:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

`.env.example` for reference:

```env
SECRET_KEY=replace-with-output-of-command-above
FLASK_ENV=development
DATABASE_URL=postgresql://postgres:[PASSWORD]@db.[REF].supabase.co:5432/postgres
```

---

##11. Screenshots

### Login

![Login page](screenshots/login.png)

### Dashboard — Match Results

![Dashboard](screenshots/dashboard.png)

### Resume Upload

![Resume upload](screenshots/upload.png)

### AI Match Results & Score Breakdown

![Match results](screenshots/matches.png)

### Skill Gap Analysis & Learning Roadmap

![Skill gap](screenshots/skill_gap.png)

### Manual Skill Entry

![Manual skills](screenshots/manual.png)

---

## 12. Deployment

The application ships with a `gunicorn.conf.py` and `wsgi.py` — no additional configuration is required to run in production.

```bash
# Production start command
gunicorn -c gunicorn.conf.py wsgi:application
```

Key Gunicorn settings:

```python
workers    = int(os.getenv("WEB_CONCURRENCY", 2))  # set to 1–2 with large ML model
timeout    = 120   # AI inference on large resumes can take several seconds
bind       = f"0.0.0.0:{os.getenv('PORT', '8000')}"
```

### Deployment Platforms

**Render** (recommended for zero-config deployment)

1. Connect repository → New Web Service
2. Build command: `pip install -r requirements.txt`
3. Start command: `gunicorn -c gunicorn.conf.py wsgi:application`
4. Add environment variables in the Render dashboard
5. Set `WEB_CONCURRENCY=1` if the free tier has memory constraints

**Railway**

```bash
railway init && railway up
```

Set environment variables in the Railway dashboard. PostgreSQL can be provisioned through Railway or pointed at an external Supabase instance.

**VPS / Docker**

The application has no external service dependencies beyond the database. A basic `Dockerfile` using `python:3.11-slim` as the base image, installing requirements, and running `gunicorn -c gunicorn.conf.py wsgi:application` as the entrypoint is sufficient.

### Supabase Setup

1. Create a project at [supabase.com](https://supabase.com)
2. Navigate to **Project Settings → Database → Connection string → URI**
3. Select **Session mode, port 5432**
4. Set the URI as `DATABASE_URL` in your environment
5. Tables and the job dataset are created automatically on first startup via `db.create_all()` and the seeding function in `app.py`

---

## 13. Future Roadmap

The following enhancements are architecturally compatible with the current codebase and represent the logical next development phase:

| Enhancement | Description |
|---|---|
| **Async analysis pipeline** | Offload embedding generation to Celery workers, return a job ID immediately, and poll for results — eliminates the blocking HTTP request during AI inference |
| **Redis embedding cache** | Cache job embeddings keyed by `job_id + model_name`. Job descriptions change infrequently; caching eliminates re-encoding the same 25 vectors on every upload |
| **Recruiter portal** | Role-based access for recruiters to search and rank candidates by job description, with inverse matching (job → candidates) |
| **Cover letter generation** | Given a matched job and a candidate's skill profile, prompt an LLM API to draft a personalised cover letter addressing the specific skill gap |
| **LLM resume feedback** | Send parsed resume text to an LLM with a structured rubric and return actionable improvement suggestions per section |
| **Advanced analytics** | Aggregate match score distributions per category, track improvement over successive uploads, visualise skill trajectory |
| **OAuth login** | Google and LinkedIn authentication via Flask-Dance — reduces registration friction and enables profile enrichment |
| **Alembic migrations** | Replace `db.create_all()` with a full migration history for safe schema evolution in production |
| **Interview recommendation** | Map skill gaps to curated learning resources and estimated preparation timelines for each matched role |

---

## Engineering Notes

This project was developed iteratively through seven debugging cycles that produced meaningful improvements to the codebase. The `effective_score` correction in `models/match.py`, the `normalize_skill()` function in `utils/skill_extractor.py`, the manual skill merge in `routes/analysis.py`, and the SQLite development fallback in `config.py` all emerged from real problems encountered during testing — not from speculative design.

The architecture prioritises explainability. Every match result carries both its semantic score (what the model thought) and its keyword score (what the taxonomy found), displayed separately in the dashboard. A candidate can understand not just their ranking but why it is what it is and what specific skills would improve it.

The choice to use server-side rendering throughout — rather than a decoupled API and SPA frontend — reflects a deliberate engineering trade-off. The application is simpler to deploy, easier to reason about, and significantly harder to exploit than an equivalent system with a JavaScript client managing authentication tokens in `localStorage`.

---

<div align="center">

**Skill Job Matcher Pro** — where semantic intelligence meets practical career engineering.

MIT License · Built with Flask, Supabase, and SentenceTransformers

</div>
----------
