"""
Unit tests for dashboard Flask app startup and endpoint uniqueness.

Asserts that the dashboard app imports successfully and has no duplicate
endpoint names (which would cause Flask to crash or behave incorrectly).
"""

import sys
from pathlib import Path

# Ensure project root is on path for dashboard imports
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import pytest


def test_flask_app_imports_without_error():
    """Importing the dashboard app must succeed (no import-time crashes)."""
    from dashboard.app import app

    assert app is not None
    assert hasattr(app, "url_map")


def test_no_duplicate_endpoints():
    """App must have no duplicate endpoint names (startup validation passes)."""
    from dashboard.app import app
    from dashboard.routes import validate_no_duplicate_endpoints

    # Re-run validation: should not raise (module load already ran it)
    validate_no_duplicate_endpoints(app)


def test_app_has_registered_routes():
    """App must have at least one registered route after startup."""
    from dashboard.app import app

    rules = list(app.url_map.iter_rules())
    assert len(rules) > 0, "Expected at least one registered route"
