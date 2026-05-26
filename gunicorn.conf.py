"""
gunicorn.conf.py — Gunicorn production configuration
=====================================================
Run: gunicorn -c gunicorn.conf.py wsgi:application
"""

import multiprocessing
import os

# ── Binding ───────────────────────────────────────────────────────
bind    = f"0.0.0.0:{os.getenv('PORT', '8000')}"
backlog = 2048

# ── Workers ───────────────────────────────────────────────────────
# Recommended: (2 × CPU cores) + 1
# Keep at 1-2 if loading large ML model to avoid OOM
workers     = int(os.getenv("WEB_CONCURRENCY", 2))
worker_class = "sync"
threads      = 1
timeout      = 120          # AI inference can take a few seconds
keepalive    = 5

# ── Logging ───────────────────────────────────────────────────────
accesslog  = "-"             # stdout
errorlog   = "-"             # stderr
loglevel   = os.getenv("LOG_LEVEL", "info")
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s %(f)s %(a)s'

# ── Process naming ────────────────────────────────────────────────
proc_name = "skillmatch-ai"

# ── Limits ────────────────────────────────────────────────────────
max_requests          = 1000
max_requests_jitter   = 50
limit_request_line    = 8192
limit_request_fields  = 100
