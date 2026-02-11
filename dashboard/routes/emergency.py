"""
Emergency Control Routes

API routes for emergency kill switch and safety controls.
"""

import sys
from pathlib import Path

# Add project root to Python path FIRST
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from flask import Blueprint, jsonify, request

from services.emergency_kill_switch import kill_switch
from services.strategy_health_monitor import health_monitor
from services.strategy_pause_manager import pause_manager
from database.competition_models import Strategy
from logger import get_logger

logger = get_logger()

emergency_bp = Blueprint("emergency", __name__, url_prefix="/api/emergency")


@emergency_bp.route("/kill-switch/status", methods=["GET"], endpoint="emergency_kill_switch_status")
def get_kill_switch_status():
    """Get kill switch status"""
    try:
        status = kill_switch.get_status()
        return jsonify({"success": True, "status": status})
    except Exception as e:
        logger.error(f"Error getting kill switch status: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@emergency_bp.route("/kill-switch/activate", methods=["POST"], endpoint="emergency_kill_switch_activate")
def activate_kill_switch():
    """Activate emergency kill switch"""
    try:
        data = request.json or {}
        reason = data.get("reason", "Manual activation")
        close_positions = data.get("close_positions", False)
        activated_by = data.get("activated_by", "dashboard_user")

        result = kill_switch.activate_kill_switch(
            reason=reason, close_positions=close_positions, activated_by=activated_by
        )

        return jsonify({"success": True, "result": result})
    except Exception as e:
        logger.error(f"Error activating kill switch: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@emergency_bp.route("/kill-switch/deactivate", methods=["POST"], endpoint="emergency_kill_switch_deactivate")
def deactivate_kill_switch():
    """Deactivate emergency kill switch"""
    try:
        data = request.json or {}
        admin_password = data.get("admin_password")

        result = kill_switch.deactivate_kill_switch(admin_password=admin_password)

        return jsonify({"success": True, "result": result})
    except Exception as e:
        logger.error(f"Error deactivating kill switch: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@emergency_bp.route("/health/summary", methods=["GET"], endpoint="emergency_health_summary")
def get_health_summary():
    """Get health summary"""
    try:
        summary = health_monitor.get_health_summary()
        return jsonify({"success": True, "summary": summary})
    except Exception as e:
        logger.error(f"Error getting health summary: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@emergency_bp.route("/strategy/pause", methods=["POST"], endpoint="emergency_strategy_pause")
def pause_strategy():
    """Pause a strategy"""
    try:
        data = request.json or {}
        strategy_name = data.get("strategy_name")
        reason = data.get("reason", "Manual pause")

        if not strategy_name:
            return (
                jsonify({"success": False, "error": "strategy_name is required"}),
                400,
            )

        result = pause_manager.pause_strategy(strategy_name, reason)

        return jsonify({"success": result["success"], "result": result})
    except Exception as e:
        logger.error(f"Error pausing strategy: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@emergency_bp.route("/strategy/resume", methods=["POST"], endpoint="emergency_strategy_resume")
def resume_strategy():
    """Resume a paused strategy"""
    try:
        data = request.json or {}
        strategy_name = data.get("strategy_name")

        if not strategy_name:
            return (
                jsonify({"success": False, "error": "strategy_name is required"}),
                400,
            )

        result = pause_manager.resume_strategy(strategy_name)

        return jsonify({"success": result["success"], "result": result})
    except Exception as e:
        logger.error(f"Error resuming strategy: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@emergency_bp.route("/strategy/enable", methods=["POST"], endpoint="emergency_strategy_enable")
def enable_strategy():
    """Enable a disabled strategy"""
    try:
        data = request.json or {}
        strategy_name = data.get("strategy_name")

        if not strategy_name:
            return (
                jsonify({"success": False, "error": "strategy_name is required"}),
                400,
            )

        strategy = Strategy.get_by_name(strategy_name)
        if not strategy:
            return jsonify({"success": False, "error": "Strategy not found"}), 404

        Strategy.update(
            strategy["id"],
            enabled=1,
            auto_disabled=0,
            emergency_disabled=0,
            disable_reason=None,
        )

        return jsonify(
            {"success": True, "message": f"Strategy {strategy_name} enabled"}
        )
    except Exception as e:
        logger.error(f"Error enabling strategy: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@emergency_bp.route("/strategy/disable", methods=["POST"], endpoint="emergency_strategy_disable")
def disable_strategy():
    """Disable a strategy"""
    try:
        data = request.json or {}
        strategy_name = data.get("strategy_name")
        reason = data.get("reason", "Manual disable")

        if not strategy_name:
            return (
                jsonify({"success": False, "error": "strategy_name is required"}),
                400,
            )

        strategy = Strategy.get_by_name(strategy_name)
        if not strategy:
            return jsonify({"success": False, "error": "Strategy not found"}), 404

        Strategy.update(strategy["id"], enabled=0, disable_reason=reason)

        return jsonify(
            {"success": True, "message": f"Strategy {strategy_name} disabled"}
        )
    except Exception as e:
        logger.error(f"Error disabling strategy: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500
