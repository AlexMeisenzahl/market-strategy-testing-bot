"""
System actions blueprint.

Update check/start/progress/cancel/rollback, backups, force-stop, unlock.
Routes are registered on this blueprint in dashboard/app.py.
"""

from flask import Blueprint

system_bp = Blueprint("system", __name__, url_prefix="")
