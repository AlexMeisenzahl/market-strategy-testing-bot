"""
Trade journal blueprint.

Trade journal page and journal entry APIs.
Routes are registered on this blueprint in dashboard/app.py.
"""

from flask import Blueprint

journal_bp = Blueprint("journal", __name__, url_prefix="")
