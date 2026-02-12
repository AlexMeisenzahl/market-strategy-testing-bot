"""
Stable JSON API under /api/* — mirrors key dashboard data.
Additive only; reuses existing service functions and state readers.
"""

from datetime import datetime
from flask import Blueprint, jsonify

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.route("/status", methods=["GET"], endpoint="api_status")
def get_status():
    """GET /api/status — engine_status, connected, last_cycle_time, active_positions, equity."""
    try:
        from dashboard.app import engine_state_reader

        state = engine_state_reader.get_bot_state()
        engine_status = (state.get("status") or "unknown") if isinstance(state, dict) else "unknown"
        connected = engine_state_reader.has_engine_state()

        health = engine_state_reader.get_engine_health()
        last_cycle_time = (health.get("last_cycle_timestamp") if isinstance(health, dict) else None) or None

        positions = engine_state_reader.get_positions_from_engine()
        active_positions = len([p for p in (positions or []) if p.get("quantity") or p.get("size")])

        portfolio = engine_state_reader.get_portfolio_from_engine()
        equity = float(portfolio.get("total_value", 0) or 0) if isinstance(portfolio, dict) else 0.0

        return jsonify({
            "engine_status": engine_status,
            "connected": connected,
            "last_cycle_time": last_cycle_time,
            "active_positions": active_positions,
            "equity": round(equity, 2),
        })
    except Exception as e:
        from logger import get_logger
        get_logger().error(f"API /api/status: {e}", exc_info=True)
        return jsonify({
            "engine_status": "unknown",
            "connected": False,
            "last_cycle_time": None,
            "active_positions": 0,
            "equity": 0.0,
            "error": str(e),
        }), 500


@api_bp.route("/trades", methods=["GET"], endpoint="api_trades")
def get_trades():
    """GET /api/trades — count and list of trades (same source as dashboard trade table)."""
    try:
        from dashboard.app import data_parser, engine_state_reader
        from dashboard.services.trade_adapter import get_normalized_trades

        data = get_normalized_trades(data_parser, engine_state_reader)
        all_trades = data.get("all", [])
        count = data.get("count_open", 0) + data.get("count_closed", 0)
        return jsonify({"count": count, "trades": all_trades})
    except Exception as e:
        from logger import get_logger
        get_logger().error(f"API /api/trades: {e}", exc_info=True)
        return jsonify({"count": 0, "trades": [], "error": str(e)}), 500


@api_bp.route("/strategies", methods=["GET"], endpoint="api_strategies")
def get_strategies():
    """GET /api/strategies — list of strategies (reuses dashboard strategy data)."""
    try:
        from dashboard.app import data_parser, engine_state_reader

        names = data_parser.get_all_strategy_names()
        performance = data_parser.get_strategy_performance()
        positions = engine_state_reader.get_positions_from_engine()
        activity = engine_state_reader.get_activity()

        open_by_strategy = {}
        for p in (positions or []):
            if p.get("quantity") or p.get("size"):
                s = (p.get("strategy") or "Unknown").strip() or "Unknown"
                open_by_strategy[s] = open_by_strategy.get(s, 0) + 1

        last_signal_by_strategy = {}
        for a in (activity or [])[:200]:
            s = (a.get("strategy") or "Unknown").strip() or "Unknown"
            if s not in last_signal_by_strategy:
                last_signal_by_strategy[s] = a.get("timestamp") or ""

        strategies = []
        for name in names:
            perf = performance.get(name) or {}
            strategies.append({
                "name": name,
                "enabled": True,
                "health_score": None,
                "last_signal": last_signal_by_strategy.get(name),
                "open_positions": open_by_strategy.get(name, 0),
                "trades_executed": perf.get("trades_executed", 0),
                "win_rate": perf.get("win_rate"),
                "total_pnl": perf.get("total_pnl"),
                "auto_disable_reason": None,
            })
        return jsonify({"strategies": strategies})
    except Exception as e:
        from logger import get_logger
        get_logger().error(f"API /api/strategies: {e}", exc_info=True)
        return jsonify({"strategies": [], "error": str(e)}), 500


@api_bp.route("/performance", methods=["GET"], endpoint="api_performance")
def get_performance():
    """GET /api/performance — total_pnl, daily_pnl, win_rate, drawdown (reuses analytics)."""
    try:
        from dashboard.app import data_parser, analytics

        stats = analytics.get_overview_stats()
        trades = data_parser.get_all_trades() or []
        today = datetime.now().date()
        daily_pnl = 0.0
        for t in trades:
            ts = t.get("exit_time") or t.get("entry_time") or ""
            if not ts:
                continue
            try:
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                d = dt.date() if dt.tzinfo is None else dt.astimezone().date()
                if d == today:
                    daily_pnl += float(t.get("pnl_usd") or 0)
            except (ValueError, TypeError):
                pass

        return jsonify({
            "total_pnl": stats.get("total_pnl", 0),
            "daily_pnl": round(daily_pnl, 2),
            "win_rate": stats.get("win_rate", 0),
            "drawdown": stats.get("max_drawdown") or stats.get("max_drawdown_pct") or 0,
        })
    except Exception as e:
        from logger import get_logger
        get_logger().error(f"API /api/performance: {e}", exc_info=True)
        return jsonify({
            "total_pnl": 0,
            "daily_pnl": 0,
            "win_rate": 0,
            "drawdown": 0,
            "error": str(e),
        }), 500


@api_bp.route("/logs", methods=["GET"], endpoint="api_logs")
def get_logs():
    """GET /api/logs — activity events (reuses existing activity log reader)."""
    try:
        from dashboard.app import engine_state_reader

        events = engine_state_reader.get_activity()
        return jsonify({"events": events or []})
    except Exception as e:
        from logger import get_logger
        get_logger().error(f"API /api/logs: {e}", exc_info=True)
        return jsonify({"events": [], "error": str(e)}), 500
