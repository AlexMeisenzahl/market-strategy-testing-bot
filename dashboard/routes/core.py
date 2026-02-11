"""
Core dashboard blueprint.

Dashboard pages, health, metrics, overview, trades, analytics, bot control,
logs, tax, alerts, workspaces, feature flags, positions, portfolio, realtime,
API keys (deprecated), intelligence, export, and related API routes.
Routes are registered on this blueprint in dashboard/app.py.
"""

from flask import Blueprint

core_bp = Blueprint("core", __name__, url_prefix="")
