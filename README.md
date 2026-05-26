# SkillMatch AI — Semantic Skill & Job Matching Platform

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/Flask-3.0-000000?style=for-the-badge&logo=flask&logoColor=white"/>
  <img src="https://img.shields.io/badge/PostgreSQL-Supabase-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white"/>
  <img src="https://img.shields.io/badge/AI-Sentence_Transformers-FF6F00?style=for-the-badge&logo=pytorch&logoColor=white"/>
  <img src="https://img.shields.io/badge/Deploy-Gunicorn-499848?style=for-the-badge"/>
</p>

> An AI-powered recruitment platform that parses your resume, extracts skills with NLP, and ranks job matches using **real semantic embeddings** — not simple keyword overlap.

---

## Table of Contents

1. [Problem Statement](#-problem-statement)
2. [Key Features](#-key-features)
3. [AI Workflow](#-ai-workflow)
4. [Architecture](#-architecture)
5. [Tech Stack](#-tech-stack)
6. [Project Structure](#-project-structure)
7. [Quick Start](#-quick-start)
8. [Supabase PostgreSQL Setup](#-supabase-postgresql-setup)
9. [Environment Variables](#-environment-variables)
10. [Deployment (Render / Railway)](#-deployment)
11. [Security Design](#-security-design)
12. [API Rate Limiting](#-api-rate-limiting)
13. [Semantic Matching Explained](#-semantic-matching-explained)
14. [Skill Gap Analysis](#-skill-gap-analysis)
15. [Database Schema](#-database-schema)
16. [Future Enhancements](#-future-enhancements)

---

## 🎯 Problem Statement

Traditional recruitment platforms match candidates to jobs using **rigid keyword filtering**. A resume mentioning "ML" won't match a job asking for "Machine Learning", and a candidate with "PyTorch" experience may be filtered out of a "Deep Learning" role.

**SkillMatch AI** solves this with sentence-level semantic embeddings that understand *meaning*, not just characters — similar to how a human recruiter reads a resume.

---

## ✨ Key Features

| Feature | Description |
|---|---|
| **Semantic AI Matching** | `all-MiniLM-L6-v2` sentence embeddings + cosine similarity |
| **Resume Parsing** | PDF (pdfplumber) and DOCX (python-docx) text extraction |
| **NLP Skill Extraction** | 330+ skill taxonomy with boundary-aware regex matching |
| **Skill Gap Analysis** | Per-job missing skills + global learning roadmap |
| **Brute-force Protection** | Flask-Limiter: 5 login attempts/minute |
| **Secure Auth** | PBKDF2-SHA256 password hashing, HTTP-only session cookies |
| **PostgreSQL / Supabase** | Production-grade DB with SQLAlchemy ORM |
| **Server-Side Rendering** | 100% Flask/Jinja2 — zero JavaScript required |
| **Professional Dashboard** | Dark sidebar, match score cards, skill cloud |
| **Gunicorn Ready** | Production WSGI server configuration included |

---

## 🧠 AI Workflow

```
Resume Upload (PDF / DOCX)
        │
        ▼
  Resume Parser (pdfplumber / python-docx)
        │
        ▼
  Raw Text Extraction
        │
        ├──────────────────────────┐
        ▼                          ▼
NLP Skill Extractor          SentenceTransformer
(330+ taxonomy, regex)       (all-MiniLM-L6-v2)
        │                          │
        ▼                          ▼
Extracted Skills List      Resume Embedding Vector
        │                          │
        └──────────┬───────────────┘
                   ▼
         For each Job in DB:
           ├─ Generate Job Embedding
           ├─ Cosine Similarity  → semantic_score (0–1)
           ├─ Keyword Overlap    → keyword_score  (0–100)
           └─ Blended Score      = 60% semantic + 40% keyword
                   │
                   ▼
         Ranked Match Results
         + Missing Skills (Gap Analysis)
         + Global Learning Roadmap
                   │
                   ▼
         Persisted to PostgreSQL
         Rendered on Dashboard
```

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Browser (HTML / CSS)                  │
│              Flask/Jinja2 Server-Side Rendering          │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP
┌──────────────────────▼──────────────────────────────────┐
│                   Gunicorn WSGI Server                   │
│  ┌─────────────────────────────────────────────────────┐ │
│  │                    Flask App                        │ │
│  │  ┌──────────┐  ┌───────────┐  ┌─────────────────┐  │ │
│  │  │ auth_bp  │  │dashboard  │  │  analysis_bp    │  │ │
│  │  │ /login   │  │/dashboard │  │  /analyze       │  │ │
│  │  │ /register│  │/jobs      │  │  (pipeline)     │  │ │
│  │  │ /logout  │  │/profile   │  └────────┬────────┘  │ │
│  │  └──────────┘  └───────────┘           │           │ │
│  │                                         │           │ │
│  │  ┌──────────────────────────────────────▼─────────┐ │ │
│  │  │              Utils Layer                       │ │ │
│  │  │  parser.py │ skill_extractor.py │ matcher.py   │ │ │
│  │  └──────────────────────────────────────┬─────────┘ │ │
│  └────────────────────────────────────────┼────────────┘ │
└───────────────────────────────────────────┼──────────────┘
                                            │
        ┌───────────────────────────────────▼────────────────┐
        │         Supabase PostgreSQL                        │
        │   users │ resumes │ jobs │ match_results           │
        └────────────────────────────────────────────────────┘
```

---

## 🛠 Tech Stack

**Backend**
- Flask 3.0 (application factory pattern, blueprints)
- Flask-Login 0.6 (session management)
- Flask-Limiter 3.7 (rate limiting)
- Flask-SQLAlchemy 3.1 (ORM)

**Frontend**
- Jinja2 server-side templates
- Bootstrap 5.3 (CSS only)
- Bootstrap Icons
- Custom CSS (dark sidebar, gradient cards)
- ⚡ **Zero JavaScript** in production

**AI / ML**
- `sentence-transformers` — `all-MiniLM-L6-v2` model
- `scikit-learn` — cosine similarity
- Custom NLP taxonomy — 330+ skills, boundary-aware regex

**Database**
- PostgreSQL (Supabase-hosted)
- SQLAlchemy 2.0 ORM
- `psycopg2-binary` driver

**Security**
- Werkzeug `generate_password_hash` (PBKDF2-SHA256)
- Flask-Limiter brute-force protection
- HTTP-only session cookies
- UUID-named file uploads
- Environment-variable secrets

**Deployment**
- Gunicorn 22 (production WSGI)
- Environment-based config classes

---

## 📁 Project Structure

```
skill-job-matcher/
│
├── app.py                  # Application factory + WSGI entry
├── config.py               # Dev / Prod / Test configuration classes
├── extensions.py           # Flask extension singletons (db, limiter, login)
├── wsgi.py                 # Gunicorn entry point
├── gunicorn.conf.py        # Gunicorn production settings
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
│
├── models/
│   ├── __init__.py
│   ├── user.py             # User model + Flask-Login mixin
│   ├── resume.py           # Resume metadata + parsed content
│   ├── job.py              # Job listings (seeded from data/jobs.py)
│   └── match.py            # MatchResult — scores + skill gap
│
├── routes/
│   ├── auth.py             # /login  /register  /logout
│   ├── dashboard.py        # /dashboard  /dashboard/jobs  /profile
│   └── analysis.py         # /analyze  (full AI pipeline)
│
├── utils/
│   ├── __init__.py         # File upload helpers
│   ├── parser.py           # PDF/DOCX resume parser
│   ├── skill_extractor.py  # NLP skill extraction (330+ skills)
│   └── matcher.py          # Semantic AI matching engine
│
├── data/
│   └── jobs.py             # 25 rich job descriptions (seed dataset)
│
├── templates/
│   ├── base.html           # Sidebar layout (auth) + centered (guest)
│   ├── auth/
│   │   ├── login.html
│   │   └── register.html
│   ├── dashboard/
│   │   ├── index.html      # Main dashboard with match results
│   │   ├── jobs.html       # Browseable job grid with filters
│   │   └── profile.html    # User profile + resume history
│   └── errors/
│       ├── 404.html
│       ├── 500.html
│       └── 429.html
│
├── static/
│   └── css/
│       └── main.css        # Full custom CSS (~700 lines)
│
├── uploads/                # Uploaded resumes (UUID-named, gitignored)
└── instance/               # Flask instance folder (gitignored)
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL database (local or [Supabase](https://supabase.com) — free tier works)

### 1. Clone & set up environment

```bash
git clone https://github.com/YOUR_USERNAME/skill-job-matcher.git
cd skill-job-matcher

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env — set SECRET_KEY and DATABASE_URL
```

### 3. Initialise the database

```bash
# Tables are created automatically on first run via db.create_all()
# Jobs are seeded automatically if the jobs table is empty
FLASK_ENV=development flask run
```

### 4. Run locally

```bash
# Development
FLASK_ENV=development flask run

# Production-like (Gunicorn)
gunicorn -c gunicorn.conf.py wsgi:application
```

Open [http://localhost:5000](http://localhost:5000) — register an account and upload a resume.

---

## 🟢 Supabase PostgreSQL Setup

1. Create a free project at [supabase.com](https://supabase.com)
2. Go to **Project Settings → Database**
3. Copy the **Connection string** (URI format, Session mode port 5432)
4. Paste into your `.env` as `DATABASE_URL`

```env
DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
```

> Tables are created automatically via `db.create_all()` on startup.
> No manual migration commands needed for initial setup.

---

## 🔐 Environment Variables

| Variable | Required | Description |
|---|---|---|
| `SECRET_KEY` | ✅ | Flask session secret (min 32 chars, random) |
| `DATABASE_URL` | ✅ | PostgreSQL connection URI |
| `FLASK_ENV` | ✅ | `production` or `development` |
| `SENTENCE_TRANSFORMER_MODEL` | ❌ | AI model name (default: `all-MiniLM-L6-v2`) |
| `PORT` | ❌ | Gunicorn port (default: 8000) |
| `WEB_CONCURRENCY` | ❌ | Gunicorn workers (default: 2) |

Generate a strong `SECRET_KEY`:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## ☁️ Deployment

### Render (recommended)

1. Push to GitHub
2. Create a new **Web Service** on [render.com](https://render.com)
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn -c gunicorn.conf.py wsgi:application`
5. Add environment variables in the Render dashboard
6. Link your Supabase `DATABASE_URL`

### Railway

```bash
railway init
railway add postgresql    # or use Supabase external DB
railway up
```

### Environment variables to set on your host

```
SECRET_KEY=<generated>
DATABASE_URL=<supabase-url>
FLASK_ENV=production
WEB_CONCURRENCY=2
```

---

## 🔒 Security Design

### Password Storage
Passwords are hashed using Werkzeug's `generate_password_hash` with the PBKDF2-SHA256 algorithm and a random salt. The raw password is never stored or logged anywhere in the application.

```python
from werkzeug.security import generate_password_hash, check_password_hash

user.password_hash = generate_password_hash(plain_text)        # store
is_valid = check_password_hash(user.password_hash, plain_text) # verify
```

### Session Security
- Sessions use Flask's signed cookie (HMAC-SHA1) with `SECRET_KEY`
- `SESSION_COOKIE_HTTPONLY = True` — inaccessible to client scripts
- `SESSION_COOKIE_SAMESITE = "Lax"` — CSRF mitigation
- `SESSION_COOKIE_SECURE = True` in production (HTTPS only)

### File Upload Security
- Filenames sanitised with `werkzeug.utils.secure_filename`
- UUIDs prepended to stored filenames (prevents path traversal)
- Extension whitelist: only `.pdf` and `.docx` accepted
- 10 MB maximum file size enforced

### Route Protection
All dashboard and analysis routes are decorated with `@login_required` from Flask-Login. Unauthenticated requests are redirected to `/login` with the original URL preserved as a `next` parameter (open-redirect protection: only relative paths accepted).

---

## 🛡 API Rate Limiting

Flask-Limiter enforces request rate limits using the client IP address:

| Endpoint | Limit | Protection |
|---|---|---|
| `POST /login` | **5 per minute** | Brute-force login attacks |
| `POST /register` | **3 per minute** | Account enumeration / spam |
| `POST /analyze` | **10 per hour** | Abuse of AI inference |
| All routes | 200/day · 50/hour | General DDoS mitigation |

When the limit is exceeded, the server returns HTTP 429 with a user-friendly error page.

To use distributed rate limiting across multiple Gunicorn workers, set:
```env
REDIS_URL=redis://localhost:6379/0
```
And update `storage_uri` in `extensions.py`.

---

## 🤖 Semantic Matching Explained

Traditional keyword matching gives a score of 0 if "ML" is in a resume but the job says "Machine Learning". Semantic matching uses **dense vector embeddings** to understand that these terms are related.

### How it works

1. **Resume profile** string is built from extracted skills + first 400 words of resume text
2. **Job profile** string is built from the job description + required skills list
3. Both are encoded by `SentenceTransformer("all-MiniLM-L6-v2")` into 384-dimensional vectors
4. **Cosine similarity** between the two vectors gives a score from 0 (unrelated) to 1 (identical meaning)
5. Final score blends **60% semantic** + **40% keyword overlap** for robustness

```python
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

model      = SentenceTransformer("all-MiniLM-L6-v2")
embeddings = model.encode([resume_profile, job_profile])
score      = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
```

### Why `all-MiniLM-L6-v2`?
- 22M parameters — fast inference (~100ms per batch on CPU)
- Trained specifically for semantic similarity tasks
- 384-dimensional embeddings — compact but expressive
- MIT licensed, runs offline after first download

---

## 📊 Skill Gap Analysis

For every job match, SkillMatch AI computes two lists:

- **Matched skills** — skills found in both the resume and the job requirements
- **Missing skills** — required by the job but absent from the resume

The **Learning Roadmap** on the dashboard aggregates missing skills across *all* job matches, ranked by frequency — giving you a prioritised learning plan tailored to the jobs you're most interested in.

```
Your Resume:  Python, Flask, SQL, Docker, Git
Job Required: Python, Flask, SQL, Docker, Kubernetes, AWS, Terraform

Matched:  Python ✓  Flask ✓  SQL ✓  Docker ✓
Missing:  Kubernetes ✗  AWS ✗  Terraform ✗
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
    stored_filename   VARCHAR(255),   -- UUID-named
    file_type         VARCHAR(10),
    raw_text          TEXT,
    extracted_skills  TEXT,           -- comma-separated
    education_info    TEXT,
    certifications    TEXT,
    uploaded_at       TIMESTAMP DEFAULT NOW(),
    processed_at      TIMESTAMP
);

-- Jobs (seeded from data/jobs.py)
CREATE TABLE jobs (
    id               SERIAL PRIMARY KEY,
    title            VARCHAR(200) NOT NULL,
    description      TEXT NOT NULL,
    category         VARCHAR(100),
    experience_level VARCHAR(50),
    required_skills  TEXT,            -- JSON array
    created_at       TIMESTAMP DEFAULT NOW(),
    is_active        BOOLEAN DEFAULT TRUE
);

-- Match Results
CREATE TABLE match_results (
    id              SERIAL PRIMARY KEY,
    resume_id       INT REFERENCES resumes(id) ON DELETE CASCADE,
    job_id          INT REFERENCES jobs(id),
    match_score     FLOAT NOT NULL,   -- 0–100 blended
    semantic_score  FLOAT,            -- raw cosine 0–1
    keyword_score   FLOAT,            -- keyword overlap %
    matched_skills  TEXT,             -- JSON array
    missing_skills  TEXT,             -- JSON array
    created_at      TIMESTAMP DEFAULT NOW()
);
```

---

## 🔮 Future Enhancements

- [ ] **Resume builder** — guided form that outputs a structured resume PDF
- [ ] **Email job alerts** — notify users of new high-match jobs (Celery + Redis)
- [ ] **Admin panel** — manage jobs, users, and analytics
- [ ] **Recruiter mode** — search and rank candidates for a given job
- [ ] **Cover letter generator** — AI-drafted letters tailored to each match
- [ ] **Multi-language** — support non-English resumes with multilingual model
- [ ] **OAuth login** — Google / LinkedIn sign-in via Flask-Dance
- [ ] **REST API** — expose matching endpoint for external integrations
- [ ] **Redis caching** — cache embeddings for repeated analyses
- [ ] **Alembic migrations** — full schema migration history

---

## 👤 Author

Built as a production-quality AI/ML portfolio project.
Demonstrates: Flask architecture, semantic NLP, PostgreSQL, secure auth, rate limiting, and responsive CSS design — with zero JavaScript.

---

## 📄 License

MIT License — free to use, modify, and distribute.
