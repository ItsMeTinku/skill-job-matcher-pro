"""
wsgi.py — Gunicorn entry point
==============================
Run in production with:
    gunicorn wsgi:application --workers 4 --bind 0.0.0.0:8000 --timeout 120
"""

from app import create_app

application = create_app("production")
