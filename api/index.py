"""Vercel serverless entrypoint.

Vercel runs files under api/ as functions and looks for an ASGI `app`.
The project root is not on sys.path by default, hence the insert below.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app  # noqa: E402,F401
