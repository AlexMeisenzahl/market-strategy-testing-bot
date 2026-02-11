"""
Leaderboard Routes

API routes for strategy competition leaderboard.
"""

import sys
from pathlib import Path

# Add project root to Python path FIRST
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from flask import Blueprint, jsonify, request

from services.strategy_competition import competition
from services.performance_tracker import performance_tracker
from database.competition_models import Strategy
from logger import get_logger

logger = get_logger()

leaderboard_bp = Blueprint("leaderboard", __name__, url_prefix="/api/leaderboard")


@leaderboard_bp.route("/", methods=["GET"], endpoint="leaderboard_get")
def get_leaderboard():
    """Get strategy leaderboard. Read-only. Optional filters: status, enabled, health."""
    try:
        leaderboard = competition.get_leaderboard()
        # Phase 7D: optional filters (read-only)
        status_filter = request.args.get("status", "").strip().lower()
        enabled_filter = request.args.get("enabled")
        health_filter = request.args.get("health", "").strip().lower()
        if status_filter:
            if status_filter == "winning":
                leaderboard = [s for s in leaderboard if "WINNING" in (s.get("status") or "")]
            elif status_filter == "marginal":
                leaderboard = [s for s in leaderboard if "MARGINAL" in (s.get("status") or "")]
            elif status_filter == "losing":
                leaderboard = [s for s in leaderboard if "LOSING" in (s.get("status") or "")]
        if enabled_filter is not None:
            want_enabled = str(enabled_filter).lower() in ("1", "true", "yes")
            leaderboard = [s for s in leaderboard if s.get("enabled") == want_enabled]
        if health_filter:
            leaderboard = [s for s in leaderboard if (s.get("health") or "").lower() == health_filter]
        return jsonify({"success": True, "leaderboard": leaderboard})
    except Exception as e:
        logger.error(f"Error getting leaderboard: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@leaderboard_bp.route("/summary", methods=["GET"], endpoint="leaderboard_summary")
def get_summary():
    """Get competition summary"""
    try:
        summary = competition.get_competition_summary()
        return jsonify({"success": True, "summary": summary})
    except Exception as e:
        logger.error(f"Error getting summary: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@leaderboard_bp.route("/performance/<strategy_name>", methods=["GET"], endpoint="leaderboard_performance")
def get_strategy_performance(strategy_name):
    """Get historical performance for a strategy"""
    try:
        hours = request.args.get("hours", default=24, type=int)
        history = performance_tracker.get_historical_performance(strategy_name, hours)
        return jsonify({"success": True, "strategy": strategy_name, "history": history})
    except Exception as e:
        logger.error(f"Error getting strategy performance: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@leaderboard_bp.route("/stats", methods=["GET"], endpoint="leaderboard_stats")
def get_realtime_stats():
    """Get real-time statistics"""
    try:
        stats = performance_tracker.get_real_time_stats()
        return jsonify({"success": True, "stats": stats})
    except Exception as e:
        logger.error(f"Error getting realtime stats: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500
