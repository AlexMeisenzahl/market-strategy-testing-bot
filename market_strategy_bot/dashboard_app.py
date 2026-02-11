"""
Dashboard app factory - creates Flask app for the web dashboard.

Delegates to the existing dashboard implementation.
Ensures project root is on sys.path.
"""

import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))


def create_app():
    """Create and return the Flask application (app factory)."""
    from dashboard.app import create_app as _create_app
    return _create_app()
