"""
User and system settings blueprint.

Settings pages (main, system, advanced), manage/reset/export/import settings.
Routes are registered on this blueprint in dashboard/app.py.
"""

from flask import Blueprint

settings_bp = Blueprint("settings", __name__, url_prefix="")
