"""
Strategy comparison and controls blueprint.

Strategy comparison page, list/compare/performance, start/stop strategy APIs.
Routes are registered on this blueprint in dashboard/app.py.
"""

from flask import Blueprint

strategies_bp = Blueprint("strategies", __name__, url_prefix="")
