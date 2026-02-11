"""
Professional Web Dashboard for Market Strategy Testing Bot

A beautiful, responsive web interface for monitoring and controlling
the trading bot with comprehensive analytics and customization.
"""

import sys
from pathlib import Path

# Add parent directory to path FIRST, before any other imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from flask import (
    Flask,
    render_template,
    jsonify,
    request,
    send_file,
    Response,
    make_response,
)
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import yaml
import os
import shutil
from datetime import datetime, timezone, timedelta
import json
import psutil  # For process monitoring
import csv
import io
import traceback

from dashboard.services.data_parser import DataParser
from dashboard.services.analytics import AnalyticsService
from dashboard.services.chart_data import ChartDataService
from dashboard.services.config_manager import ConfigManager
from dashboard.services.engine_state import EngineStateReader
from dashboard.services.trade_adapter import get_normalized_trades
from services.strategy_analytics import StrategyAnalytics
from services.market_analytics import MarketAnalytics
from services.time_analytics import TimeAnalytics
from services.risk_metrics import RiskMetrics
from logger import get_logger
from database.settings_models import (
    UserSettings,
    NotificationChannel,
    NotificationPreference,
    init_db,
)
from services.notification_service import notification_service
from services.realtime_server import init_realtime_server
from dashboard.routes.config_api import config_api
from dashboard.routes.leaderboard import leaderboard_bp
from dashboard.routes.emergency import emergency_bp
from dashboard.routes.data_sources_api import data_sources_api
from dashboard.routes.core import core_bp
from dashboard.routes.journal import journal_bp
from dashboard.routes.settings import settings_bp
from dashboard.routes.strategies import strategies_bp
from dashboard.routes.system import system_bp
from dashboard.routes import validate_no_duplicate_endpoints
from version_manager import VersionManager
from services.update_service import UpdateService
from services.process_manager import ProcessManager
from services.health_check import health_service
from services.prometheus_metrics import metrics
from monitoring.metrics import get_metrics_collector
from config.config_loader import get_config
from services.data_flow_manager import DataFlowManager
from services.strategy_intelligence import (
    run_analysis as strategy_intelligence_run,
    get_cached_diagnostics,
    get_cached_suggestions,
    get_last_run_at as strategy_intelligence_last_run_at,
    export_to_reports_dir,
)
from services.execution_gate import get_gate_status as execution_gate_status

app = Flask(__name__)
CORS(app)  # Enable CORS for API access

# Initialize WebSocket server
from dashboard.websocket_server import init_socketio

socketio = init_socketio(app)

# Initialize logger first for error handling
logger_instance = get_logger()
logger = logger_instance  # Alias for backward compatibility

# Load configuration with environment variable support
try:
    config_loader = get_config(config_path="config.yaml")
    logger_instance.info("Configuration loaded successfully")
except Exception as e:
    logger_instance.warning(
        f"Could not load config via ConfigLoader: {e}, using defaults"
    )
    config_loader = None

# Initialize rate limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["100 per hour"],
    storage_uri="memory://",
)

# Initialize metrics collector
try:
    metrics_collector = get_metrics_collector(enable_prometheus=True)
    logger_instance.info("Metrics collector initialized")
except Exception as e:
    logger_instance.warning(f"Could not initialize metrics collector: {e}")
    metrics_collector = None

# Register blueprints that have all routes defined in their own modules
app.register_blueprint(config_api)
app.register_blueprint(leaderboard_bp)
app.register_blueprint(emergency_bp)
app.register_blueprint(data_sources_api)
# core_bp, journal_bp, settings_bp, strategies_bp, system_bp are registered at end of file
# after all their routes are defined below (Flask does not allow adding routes after register)

# Configuration
BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config.yaml"
LOGS_DIR = BASE_DIR / "logs"
STATE_DIR = BASE_DIR / "state"

# Engine state reader (read-only: state/bot_state.json, logs/activity.json)
engine_state_reader = EngineStateReader(BASE_DIR)

# Initialize services
# Note: logger already initialized above for error handlers
config_manager = ConfigManager(CONFIG_PATH)
data_parser = DataParser(LOGS_DIR)
analytics = AnalyticsService(data_parser)
chart_data = ChartDataService(data_parser)

# Default statistics for error handling
DEFAULT_OVERVIEW_STATS = {
    "total_pnl": 0,
    "pnl_change_pct": 0,
    "win_rate": 0,
    "active_trades": 0,
    "today_opportunities": 0,
    "total_trades": 0,
    "profit_factor": 0,
    "avg_trade_duration": 0,
    "best_strategy": "N/A",
    "gross_profit": 0,
    "gross_loss": 0,
    "largest_win": 0,
    "largest_loss": 0,
    "avg_win": 0,
    "avg_loss": 0,
    "win_loss_ratio": 0,
    "sharpe_ratio": 0,
    "max_drawdown": 0,
    "max_drawdown_pct": 0,
}

# Initialize WebSocket server for real-time updates
try:
    realtime_server = init_realtime_server(app, logger)
    logger.info("WebSocket server initialized successfully")
except Exception as e:
    logger.warning(f"Failed to initialize WebSocket server: {str(e)}")
    logger.warning("Dashboard will continue without real-time updates")
    realtime_server = None

# Initialize new analytics services (no heavy/numeric libs at import; lazy in services)
try:
    strategy_analytics = StrategyAnalytics(data_parser)
    market_analytics = MarketAnalytics(data_parser)
    time_analytics = TimeAnalytics(data_parser)
    risk_metrics = RiskMetrics(data_parser)
except Exception as e:
    logger.exception("Dashboard startup: failed to initialize analytics services: %s", e)
    raise

# Initialize database
try:
    init_db()
except Exception as e:
    logger.exception("Dashboard startup: failed to initialize settings database: %s", e)
    raise

# Initialize update system services
try:
    version_manager = VersionManager(BASE_DIR)
    update_service = UpdateService(BASE_DIR)
    process_manager = ProcessManager(BASE_DIR)
except Exception as e:
    logger.exception("Dashboard startup: failed to initialize update/process services: %s", e)
    raise


# ============================================================================
# Security Headers and Middleware
# ============================================================================


@app.after_request
def add_security_headers(response):
    """Add security headers to all responses"""
    # XSS Protection
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"

    # Content Security Policy
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data: https:; "
        "connect-src 'self' ws: wss:;"
    )

    # Prevent MIME-sniffing
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    # HSTS (HTTP Strict Transport Security) - uncomment in production with HTTPS
    # response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

    return response


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return (
        jsonify(
            {
                "error": "Not Found",
                "message": "The requested resource was not found",
                "status": 404,
            }
        ),
        404,
    )


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {error}")
    logger.error(traceback.format_exc())
    return (
        jsonify(
            {
                "error": "Internal Server Error",
                "message": "An unexpected error occurred",
                "status": 500,
            }
        ),
        500,
    )


@app.errorhandler(Exception)
def handle_exception(error):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {error}")
    logger.error(traceback.format_exc())

    # Return JSON response for API calls
    if request.path.startswith("/api/"):
        return (
            jsonify({"error": "Internal Error", "message": str(error), "status": 500}),
            500,
        )

    # Return HTML for regular pages
    return render_template("error.html", error=str(error)), 500


# ============================================================================
# Health and Monitoring Endpoints
# ============================================================================


@core_bp.route("/health", endpoint="core_health")
@core_bp.route("/api/health", endpoint="core_health_api")
def health_check():
    """
    Comprehensive health check endpoint.
    Returns detailed health status of all system components.
    """
    try:
        # Get comprehensive health check
        health_status = health_service.check_all()

        # Add application-specific health checks
        health_status["application"] = {
            "status": "healthy",
            "version": (
                version_manager.get_current_version() if version_manager else "unknown"
            ),
            "uptime_seconds": (
                metrics_collector.get_system_stats()["uptime_seconds"]
                if metrics_collector
                else 0
            ),
        }

        # Engine health (from state/engine_health.json, no heavy imports)
        try:
            engine_health = engine_state_reader.get_engine_health()
            if engine_health:
                health_status["engine"] = engine_health
        except Exception:
            pass

        # Add metrics collector stats if available
        if metrics_collector:
            health_status["metrics"] = metrics_collector.get_comprehensive_stats()

        # Determine HTTP status code based on overall health
        status_code = 200
        if health_status.get("overall_status") == "degraded":
            status_code = 503  # Service Unavailable
        elif health_status.get("overall_status") == "down":
            status_code = 503

        return jsonify(health_status), status_code

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return (
            jsonify(
                {
                    "overall_status": "unhealthy",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat(),
                }
            ),
            503,
        )


@core_bp.route("/metrics", endpoint="core_prometheus_metrics")
@core_bp.route("/api/metrics", endpoint="core_prometheus_metrics_api")
def prometheus_metrics():
    """
    Prometheus metrics endpoint.
    Returns metrics in Prometheus exposition format.
    """
    try:
        # Get Prometheus-formatted metrics
        metrics_data = metrics.get_metrics()

        # Return in Prometheus format
        from prometheus_client import CONTENT_TYPE_LATEST

        return Response(metrics_data, mimetype=CONTENT_TYPE_LATEST)

    except Exception as e:
        logger.error(f"Error generating metrics: {e}")
        return jsonify({"error": "Metrics generation failed"}), 500


@core_bp.route("/api/metrics/stats", endpoint="core_metrics_stats")
def metrics_stats():
    """
    Get human-readable metrics statistics.
    Returns JSON format of all collected metrics.
    """
    try:
        if not metrics_collector:
            return jsonify({"error": "Metrics collector not initialized"}), 503

        stats = metrics_collector.get_comprehensive_stats()
        return jsonify(stats)

    except Exception as e:
        logger.error(f"Error getting metrics stats: {e}")
        return jsonify({"error": str(e)}), 500


# Global bot status (will be updated by bot)
bot_status = {
    "running": False,
    "paused": False,
    "uptime": 0,
    "last_restart": None,
    "mode": "paper",
    "connected_symbols": 0,
    "active_strategies": 0,
}


@core_bp.route("/", endpoint="core_index")
def index():
    """Render main dashboard page"""
    return render_template("index.html")


@core_bp.route("/opportunities", endpoint="core_opportunities_page")
def opportunities_page():
    """Render opportunities page"""
    return render_template("opportunities.html")


@core_bp.route("/leaderboard", endpoint="core_leaderboard_page")
def leaderboard_page():
    """Render leaderboard page"""
    return render_template("leaderboard.html")


# Duplicate /health route removed - see line 249 for primary health_check endpoint


# PWA Routes
@core_bp.route("/manifest.json", endpoint="core_manifest")
def manifest():
    """Serve PWA manifest file"""
    return send_file(
        BASE_DIR / "dashboard" / "static" / "manifest.json",
        mimetype="application/manifest+json",
    )


@core_bp.route("/service-worker.js", endpoint="core_service_worker")
def service_worker():
    """Serve service worker file"""
    return send_file(
        BASE_DIR / "dashboard" / "static" / "service-worker.js",
        mimetype="application/javascript",
    )


@core_bp.route("/offline", endpoint="core_offline")
@core_bp.route("/offline.html", endpoint="core_offline_html")
def offline():
    """Serve offline fallback page"""
    return render_template("offline.html")


@core_bp.route("/api/overview", endpoint="core_get_overview")
def get_overview():
    """
    Get overview dashboard summary statistics.

    Prefers engine state (state/bot_state.json) when available.
    Falls back to analytics (CSV data) when engine not running.
    Never uses mock/sample data.
    """
    try:
        # Prefer engine state when available
        engine_overview = engine_state_reader.get_overview_from_engine()
        if engine_overview is not None:
            final_stats = {**DEFAULT_OVERVIEW_STATS, **engine_overview}
            return jsonify(final_stats)

        # No engine state: return zeros (no mock/sample data)
        return jsonify(
            {**DEFAULT_OVERVIEW_STATS, "message": "Engine not running (start python main.py)"}
        )
    except FileNotFoundError as e:
        # No data files exist yet - return defaults with message
        logger.warning(f"No trade data found: {str(e)}")
        return jsonify(
            {**DEFAULT_OVERVIEW_STATS, "message": "No trading data available yet"}
        )
    except Exception as e:
        # Log error and return defaults - frontend can still render
        logger.error(f"Error getting overview: {str(e)}")
        return jsonify(
            {**DEFAULT_OVERVIEW_STATS, "message": f"Error loading data: {str(e)}"}
        )


@core_bp.route("/api/trades", endpoint="core_get_trades")
def get_trades():
    """Get filtered trades data"""
    try:
        # Parse query parameters
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")
        symbol = request.args.get("symbol")
        strategy = request.args.get("strategy")
        outcome = request.args.get("outcome")
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 25))

        trades = data_parser.get_trades(
            start_date=start_date,
            end_date=end_date,
            symbol=symbol,
            strategy=strategy,
            outcome=outcome,
            page=page,
            per_page=per_page,
        )

        return jsonify(trades)
    except Exception as e:
        logger.error(f"Error getting trades: {str(e)}")
        return jsonify({"error": str(e)}), 500


@core_bp.route("/api/opportunities", endpoint="core_get_opportunities")
def get_opportunities():
    """Get opportunities data with filters"""
    try:
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")
        symbol = request.args.get("symbol")
        strategy = request.args.get("strategy")
        status = request.args.get("status")

        opportunities = data_parser.get_opportunities(
            start_date=start_date,
            end_date=end_date,
            symbol=symbol,
            strategy=strategy,
            status=status,
        )

        return jsonify(opportunities)
    except Exception as e:
        logger.error(f"Error getting opportunities: {str(e)}")
        return jsonify({"error": str(e)}), 500


@core_bp.route("/api/charts/cumulative-pnl", endpoint="core_get_cumulative_pnl")
def get_cumulative_pnl():
    """Get cumulative P&L chart data"""
    try:
        time_range = request.args.get("range", "1M")
        data = chart_data.get_cumulative_pnl(time_range)
        return jsonify(data)
    except Exception as e:
        logger.error(f"Error getting cumulative P&L: {str(e)}")
        return jsonify({"error": str(e)}), 500


@core_bp.route("/api/charts/daily-pnl", endpoint="core_get_daily_pnl")
def get_daily_pnl():
    """Get daily P&L chart data"""
    try:
        data = chart_data.get_daily_pnl()
        return jsonify(data)
    except Exception as e:
        logger.error(f"Error getting daily P&L: {str(e)}")
        return jsonify({"error": str(e)}), 500


@core_bp.route("/api/charts/strategy-performance", endpoint="core_get_strategy_performance")
def get_strategy_performance():
    """Get strategy performance comparison data"""
    try:
        data = chart_data.get_strategy_performance()
        return jsonify(data)
    except Exception as e:
        logger.error(f"Error getting strategy performance: {str(e)}")
        return jsonify({"error": str(e)}), 500


@core_bp.route("/api/strategies", endpoint="core_get_strategies")
def get_strategies():
    """Get list of all strategy names"""
    try:
        strategies = data_parser.get_all_strategy_names()
        return jsonify({"strategies": strategies})
    except Exception as e:
        logger.error(f"Error getting strategies: {str(e)}")
        return jsonify({"error": str(e)}), 500


@core_bp.route("/api/strategies/<strategy_name>/performance", endpoint="core_get_strategy_details")
def get_strategy_details(strategy_name):
    """Get detailed performance for a specific strategy"""
    try:
        performance = data_parser.get_strategy_performance()
        if strategy_name in performance:
            return jsonify(performance[strategy_name])
        else:
            return jsonify({"error": "Strategy not found"}), 404
    except Exception as e:
        logger.error(f"Error getting strategy details: {str(e)}")
        return jsonify({"error": str(e)}), 500


@core_bp.route("/api/settings", methods=["GET"], endpoint="core_get_settings")
def get_settings():
    """Get all settings from config.yaml"""
    try:
        settings = config_manager.get_all_settings()
        return jsonify(settings)
    except Exception as e:
        logger.error(f"Error getting settings: {str(e)}")
        return jsonify({"error": str(e)}), 500


@core_bp.route("/api/settings/notifications", methods=["GET", "PUT"], endpoint="core_handle_notification_settings")
def handle_notification_settings():
    """Get or update notification settings"""
    if request.method == "GET":
        try:
            settings = config_manager.get_all_settings()
            notifications = settings.get(
                "notifications",
                {
                    "discord": {"enabled": False, "webhook_url": ""},
                    "slack": {"enabled": False, "webhook_url": ""},
                    "email": {
                        "enabled": False,
                        "smtp_server": "",
                        "smtp_port": 587,
                        "email_from": "",
                        "email_to": "",
                    },
                    "telegram": {"enabled": False, "bot_token": "", "chat_id": ""},
                    "webhook": {"enabled": False, "url": ""},
                },
            )
            return jsonify(notifications)
        except Exception as e:
            logger.error(f"Error getting notification settings: {str(e)}")
            return jsonify({"error": str(e)}), 500
    else:  # PUT
        try:
            data = request.json
            config_manager.update_notification_settings(data)
            return jsonify(
                {"success": True, "message": "Notification settings updated"}
            )
        except Exception as e:
            logger.error(f"Error updating notification settings: {str(e)}")
            return jsonify({"error": str(e)}), 500


@core_bp.route("/api/settings/strategies", methods=["PUT"], endpoint="core_update_strategy_settings")
def update_strategy_settings():
    """Update strategy configuration"""
    try:
        data = request.json
        config_manager.update_strategy_settings(data)
        return jsonify({"success": True, "message": "Strategy settings updated"})
    except Exception as e:
        logger.error(f"Error updating strategy settings: {str(e)}")
        return jsonify({"error": str(e)}), 500


@core_bp.route("/api/analytics/overview", endpoint="core_analytics_overview")
def analytics_overview():
    """
    Get dashboard overview analytics statistics

    Returns comprehensive statistics including:
    - Total opportunities found
    - Total trades executed
    - Profit/loss trends
    - Success rate by strategy
    """
    try:
        # Get date range from query params
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")

        # Get trades and opportunities
        trades = data_parser.get_trades(
            start_date=start_date, end_date=end_date, page=1, per_page=10000
        )
        opportunities = data_parser.get_opportunities(
            start_date=start_date, end_date=end_date
        )

        # Calculate statistics
        total_opportunities = len(opportunities) if opportunities else 0
        total_trades = trades.get("total", 0) if isinstance(trades, dict) else 0
        trade_list = trades.get("trades", []) if isinstance(trades, dict) else []

        # Calculate P&L
        total_pnl = sum(t.get("profit", 0) for t in trade_list)
        winning_trades = len([t for t in trade_list if t.get("profit", 0) > 0])
        losing_trades = len([t for t in trade_list if t.get("profit", 0) < 0])
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

        # Success rate by strategy
        strategy_stats = {}
        for trade in trade_list:
            strategy = trade.get("strategy", "unknown")
            if strategy not in strategy_stats:
                strategy_stats[strategy] = {"total": 0, "wins": 0, "profit": 0}
            strategy_stats[strategy]["total"] += 1
            if trade.get("profit", 0) > 0:
                strategy_stats[strategy]["wins"] += 1
            strategy_stats[strategy]["profit"] += trade.get("profit", 0)

        # Calculate win rate per strategy
        for strategy in strategy_stats:
            total = strategy_stats[strategy]["total"]
            wins = strategy_stats[strategy]["wins"]
            strategy_stats[strategy]["win_rate"] = (
                (wins / total * 100) if total > 0 else 0
            )

        return jsonify(
            {
                "total_opportunities": total_opportunities,
                "total_trades": total_trades,
                "winning_trades": winning_trades,
                "losing_trades": losing_trades,
                "win_rate": round(win_rate, 2),
                "total_pnl": round(total_pnl, 2),
                "average_profit_per_trade": (
                    round(total_pnl / total_trades, 2) if total_trades > 0 else 0
                ),
                "strategy_performance": strategy_stats,
            }
        )
    except Exception as e:
        logger.error(f"Error getting analytics overview: {str(e)}")
        return jsonify({"error": str(e)}), 500


@core_bp.route("/api/analytics/charts", endpoint="core_analytics_charts")
def analytics_charts():
    """
    Get chart data for visualizations

    Returns data for:
    - Cumulative P&L over time
    - Daily opportunity count
    - Profit distribution by market
    """
    try:
        # Get date range from query params
        time_range = request.args.get("range", "1M")

        # Get existing chart data
        cumulative_pnl = chart_data.get_cumulative_pnl(time_range)
        daily_pnl = chart_data.get_daily_pnl()
        strategy_performance = chart_data.get_strategy_performance()

        # Get opportunity count data
        opportunities = data_parser.get_opportunities()

        # Group opportunities by date
        from collections import defaultdict
        from datetime import datetime

        daily_opportunities = defaultdict(int)
        if opportunities:
            for opp in opportunities:
                date_str = opp.get("timestamp", "")[:10] if opp.get("timestamp") else ""
                if date_str:
                    daily_opportunities[date_str] += 1

        # Convert to sorted list
        opportunity_timeline = [
            {"date": date, "count": count}
            for date, count in sorted(daily_opportunities.items())
        ]

        return jsonify(
            {
                "cumulative_pnl": cumulative_pnl,
                "daily_pnl": daily_pnl,
                "strategy_performance": strategy_performance,
                "opportunity_timeline": opportunity_timeline,
            }
        )
    except Exception as e:
        logger.error(f"Error getting analytics charts: {str(e)}")
        return jsonify({"error": str(e)}), 500


@core_bp.route("/api/export/trades", methods=["POST"], endpoint="core_export_trades")
def export_trades():
    """
    Export trades to CSV for external analysis

    Accepts filters in request body:
    - start_date: Filter trades after this date
    - end_date: Filter trades before this date
    - market: Filter by specific market
    - strategy: Filter by strategy name
    """
    try:
        import csv
        import io
        from flask import make_response

        # Get filters from request
        data = request.json or {}
        start_date = data.get("start_date")
        end_date = data.get("end_date")
        market = data.get("market")
        strategy = data.get("strategy")

        # Get all trades matching filters
        trades_data = data_parser.get_trades(
            start_date=start_date,
            end_date=end_date,
            symbol=market,
            strategy=strategy,
            page=1,
            per_page=10000,  # Get all trades
        )

        trade_list = (
            trades_data.get("trades", []) if isinstance(trades_data, dict) else []
        )

        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow(
            [
                "Timestamp",
                "Market",
                "Strategy",
                "Entry Price",
                "Exit Price",
                "Size",
                "Profit/Loss",
                "Status",
                "Notes",
            ]
        )

        # Write data rows
        for trade in trade_list:
            writer.writerow(
                [
                    trade.get("timestamp", ""),
                    trade.get("market", ""),
                    trade.get("strategy", ""),
                    trade.get("entry_price", ""),
                    trade.get("exit_price", ""),
                    trade.get("size", ""),
                    trade.get("profit", 0),
                    trade.get("status", ""),
                    trade.get("notes", ""),
                ]
            )

        # Create response
        output.seek(0)
        response = make_response(output.getvalue())
        response.headers["Content-Type"] = "text/csv"
        response.headers["Content-Disposition"] = (
            f'attachment; filename=trades_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )

        return response
    except Exception as e:
        logger.error(f"Error exporting trades: {str(e)}")
        return jsonify({"error": str(e)}), 500


@core_bp.route("/api/notifications/test", methods=["POST"], endpoint="core_test_notification")
def test_notification():
    """Send test notification"""
    try:
        data = request.json
        notification_type = data.get("type", "desktop")

        # Import and create notifier
        from notifier import Notifier

        config = config_manager.get_all_settings()
        notifier = Notifier(config)

        result = False
        if notification_type == "desktop":
            result = notifier.send_desktop_notification(
                "Test Notification", "This is a test from the web dashboard"
            )
        elif notification_type == "email":
            result = notifier.send_email("Test email from web dashboard")
        elif notification_type == "telegram":
            result = notifier.send_push(
                "Test Notification", "This is a test from the web dashboard"
            )

        return jsonify(
            {
                "success": result,
                "message": (
                    "Test notification sent" if result else "Test notification failed"
                ),
            }
        )
    except Exception as e:
        logger.error(f"Error sending test notification: {str(e)}")
        return jsonify({"error": str(e)}), 500


@core_bp.route("/api/notifications/history", endpoint="core_get_notification_history")
def get_notification_history():
    """Get notification history"""
    try:
        # This would read from a notification log file
        # For now, return empty array
        return jsonify([])
    except Exception as e:
        logger.error(f"Error getting notification history: {str(e)}")
        return jsonify({"error": str(e)}), 500


@core_bp.route("/api/bot/status", endpoint="core_get_bot_status")
def get_bot_status():
    """Get current engine status. Prefers engine state (state/bot_state.json). Phase 7B: Engine = main.py only."""
    try:
        # Prefer engine state when available (written by run_bot.py)
        engine_status = engine_state_reader.get_bot_status_from_engine()
        if engine_status is not None:
            result = {**bot_status, **engine_status}
            result["control_disabled"] = False
            result["control_note"] = "Engine status from state. Start/Stop below control the engine (main.py)."
            return jsonify(result)

        # Fallback: process_manager tracks engine (main.py) started by dashboard; or scan for main.py/run_bot.py
        bot_running = process_manager.is_bot_running()
        bot_pid = process_manager.get_bot_pid()
        bot_uptime = 0
        if bot_pid and bot_running:
            try:
                proc = psutil.Process(bot_pid)
                bot_uptime = int(datetime.now().timestamp() - proc.create_time())
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        if not bot_running and bot_pid is None:
            for proc in psutil.process_iter(["pid", "name", "cmdline", "create_time"]):
                try:
                    cmdline = proc.info.get("cmdline", [])
                    if cmdline:
                        c = " ".join(str(c) for c in cmdline)
                        if "main.py" in c or "run_bot.py" in c:
                            bot_running = True
                            bot_pid = proc.info["pid"]
                            bot_uptime = int(
                                datetime.now().timestamp() - proc.info["create_time"]
                            )
                            break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

        result = {
            **bot_status,
            "running": bot_running,
            "pid": bot_pid,
            "uptime": bot_uptime,
            "control_disabled": False,
            "control_note": "Start engine: python main.py (or use Start Engine below).",
        }
        if bot_running:
            result["status_emoji"] = "🟢"
            result["status_text"] = "Running"
        else:
            result["status_emoji"] = "🔴"
            result["status_text"] = "Stopped"
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting bot status: {str(e)}")
        # Return default status on error
        return (
            jsonify(
                {
                    "running": False,
                    "status_emoji": "🟡",
                    "status_text": "Error",
                    "error": str(e),
                }
            ),
            200,
        )  # Return 200 even on error to avoid breaking frontend


@core_bp.route("/api/bot/start", methods=["POST"], endpoint="core_start_bot")
def start_bot():
    """Start the engine (main.py). Phase 7B: Actually starts process."""
    try:
        success, pid = process_manager.start_bot()
        if success:
            bot_status["running"] = True
            bot_status["paused"] = False
            bot_status["last_restart"] = datetime.now().isoformat()
            return jsonify({"success": True, "message": "Engine started", "pid": pid})
        return jsonify({"success": False, "message": "Engine already running or failed to start"}), 400
    except Exception as e:
        logger.error(f"Error starting engine: {str(e)}")
        return jsonify({"error": str(e)}), 500


@core_bp.route("/api/bot/stop", methods=["POST"], endpoint="core_stop_bot")
def stop_bot():
    """Stop the engine (main.py). Phase 7B: Actually stops process."""
    try:
        success = process_manager.stop_bot()
        if success:
            bot_status["running"] = False
        return jsonify({"success": True, "message": "Engine stopped"})
    except Exception as e:
        logger.error(f"Error stopping engine: {str(e)}")
        return jsonify({"error": str(e)}), 500


@core_bp.route("/api/bot/restart", methods=["POST"], endpoint="core_restart_bot")
def restart_bot():
    """Restart the engine (main.py). Phase 7B: Actually restarts process."""
    try:
        success, pid = process_manager.restart_bot()
        if success:
            bot_status["running"] = True
            bot_status["last_restart"] = datetime.now().isoformat()
            return jsonify({"success": True, "message": "Engine restarted", "pid": pid})
        return jsonify({"success": False, "message": "Restart failed"}), 400
    except Exception as e:
        logger.error(f"Error restarting engine: {str(e)}")
        return jsonify({"error": str(e)}), 500


@core_bp.route("/api/logs/recent", endpoint="core_get_recent_logs")
def get_recent_logs():
    """Get recent log entries"""
    try:
        limit = int(request.args.get("limit", 100))
        level = request.args.get("level", "all")

        # Read from bot.log file if it exists
        logs = []
        log_file = LOGS_DIR / "bot.log"

        if log_file.exists():
            try:
                with open(log_file, "r") as f:
                    lines = f.readlines()
                    # Get last 'limit' lines
                    recent_lines = lines[-limit:] if len(lines) > limit else lines

                    for line in recent_lines:
                        line = line.strip()
                        if line:
                            # Parse log line (basic parsing)
                            logs.append(
                                {
                                    "timestamp": datetime.now().isoformat(),  # Would parse from log
                                    "level": "INFO",  # Would parse from log
                                    "message": line,
                                }
                            )
            except Exception as e:
                logger.error(f"Error reading log file: {str(e)}")

        return jsonify(logs)
    except Exception as e:
        logger.error(f"Error getting logs: {str(e)}")
        return jsonify({"error": str(e)}), 500


def update_bot_status_from_instance(status_dict):
    """
    Update bot status from running bot instance

    Args:
        status_dict: Dictionary with bot status info
    """
    bot_status.update(status_dict)


@core_bp.route("/api/tax/summary", endpoint="core_get_tax_summary")
def get_tax_summary():
    """Get tax summary data from tax_exporter"""
    try:
        year = request.args.get("year", None)
        if year:
            year = int(year)

        # Import and initialize tax exporter
        from tax_exporter import TaxExporter

        config = config_manager.get_all_settings()
        tax_exporter = TaxExporter(config, str(LOGS_DIR))

        # Generate summary
        summary = tax_exporter.generate_summary(year)

        return jsonify(summary)
    except Exception as e:
        logger.error(f"Error getting tax summary: {str(e)}")
        return jsonify({"error": str(e)}), 500


@core_bp.route("/api/tax/positions", endpoint="core_get_tax_positions")
def get_tax_positions():
    """Get detailed tax positions for Form 8949"""
    try:
        year = request.args.get("year", None)
        if year:
            year = int(year)

        # Import and initialize tax exporter
        from tax_exporter import TaxExporter

        config = config_manager.get_all_settings()
        tax_exporter = TaxExporter(config, str(LOGS_DIR))

        # Load trades and process
        trades = tax_exporter.load_trades_from_logs(year)
        if not trades:
            return jsonify([])

        positions = tax_exporter.process_trades_fifo(trades)

        # Convert to dictionaries
        positions_data = [pos.to_dict() for pos in positions]

        return jsonify(positions_data)
    except Exception as e:
        logger.error(f"Error getting tax positions: {str(e)}")
        return jsonify({"error": str(e)}), 500


@core_bp.route("/api/tax/export/<format>", endpoint="core_export_tax_report")
def export_tax_report(format):
    """Export tax report in various formats"""
    try:
        year = request.args.get("year", datetime.now().year)
        if isinstance(year, str):
            year = int(year)

        # Import and initialize tax exporter
        from tax_exporter import TaxExporter

        config = config_manager.get_all_settings()
        tax_exporter = TaxExporter(config, str(LOGS_DIR))

        if format == "csv":
            # Export to CSV
            output_path = tax_exporter.export_to_csv(year, str(LOGS_DIR))
            if output_path and os.path.exists(output_path):
                return send_file(
                    output_path,
                    as_attachment=True,
                    download_name=f"tax_report_{year}.csv",
                )
            else:
                return jsonify({"error": "Failed to generate CSV"}), 500

        elif format == "turbotax":
            # TurboTax TXF format (simplified - would need full implementation)
            return jsonify({"error": "TurboTax format not yet implemented"}), 501

        elif format == "hrblock":
            # H&R Block CSV format (similar to standard CSV)
            output_path = tax_exporter.export_to_csv(year, str(LOGS_DIR))
            if output_path and os.path.exists(output_path):
                return send_file(
                    output_path,
                    as_attachment=True,
                    download_name=f"hrblock_report_{year}.csv",
                )
            else:
                return jsonify({"error": "Failed to generate CSV"}), 500

        elif format == "form8949":
            # IRS Form 8949 format (simplified - would need full implementation)
            return jsonify({"error": "Form 8949 format not yet implemented"}), 501

        else:
            return jsonify({"error": "Unknown format"}), 400

    except Exception as e:
        logger.error(f"Error exporting tax report: {str(e)}")
        return jsonify({"error": str(e)}), 500


@core_bp.route("/api/analytics/risk", endpoint="core_get_risk_analytics")
def get_risk_analytics():
    """Get risk analytics metrics"""
    try:
        # Get trades data
        trades_data = data_parser.get_trades(page=1, per_page=10000)
        trade_list = (
            trades_data.get("trades", []) if isinstance(trades_data, dict) else []
        )

        if not trade_list:
            return jsonify(
                {
                    "sharpe_ratio": 0,
                    "sortino_ratio": 0,
                    "max_drawdown": 0,
                    "volatility": 0,
                    "var_95": 0,
                    "beta": 0,
                }
            )

        # Calculate basic risk metrics
        # Note: These are simplified calculations - full implementation would need more sophisticated algorithms
        import numpy as np

        # Get P&L series
        pnl_series = [t.get("profit", 0) for t in trade_list]

        if not pnl_series:
            return jsonify(
                {
                    "sharpe_ratio": 0,
                    "sortino_ratio": 0,
                    "max_drawdown": 0,
                    "volatility": 0,
                    "var_95": 0,
                    "beta": 0,
                }
            )

        # Calculate metrics
        returns = np.array(pnl_series)
        mean_return = np.mean(returns)
        std_return = np.std(returns)

        # Sharpe Ratio (simplified - assuming risk-free rate of 0)
        sharpe_ratio = (mean_return / std_return) if std_return > 0 else 0

        # Sortino Ratio (using downside deviation)
        downside_returns = returns[returns < 0]
        downside_std = (
            np.std(downside_returns) if len(downside_returns) > 0 else std_return
        )
        sortino_ratio = (mean_return / downside_std) if downside_std > 0 else 0

        # Max Drawdown
        cumulative = np.cumsum(returns)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = cumulative - running_max
        max_drawdown = np.min(drawdown) if len(drawdown) > 0 else 0

        # Volatility
        volatility = std_return

        # Value at Risk (95% confidence)
        var_95 = np.percentile(returns, 5) if len(returns) > 0 else 0

        # Beta (simplified - would need market data for proper calculation)
        beta = 1.0  # Placeholder

        return jsonify(
            {
                "sharpe_ratio": round(float(sharpe_ratio), 2),
                "sortino_ratio": round(float(sortino_ratio), 2),
                "max_drawdown": round(float(max_drawdown), 2),
                "volatility": round(float(volatility), 2),
                "var_95": round(float(var_95), 2),
                "beta": round(float(beta), 2),
            }
        )
    except Exception as e:
        logger.error(f"Error calculating risk analytics: {str(e)}")
        return jsonify({"error": str(e)}), 500


@core_bp.route("/api/analytics/strategy-breakdown", endpoint="core_get_strategy_breakdown")
def get_strategy_breakdown():
    """Get detailed per-strategy performance breakdown"""
    try:
        # Get trades data
        trades_data = data_parser.get_trades(page=1, per_page=10000)
        trade_list = (
            trades_data.get("trades", []) if isinstance(trades_data, dict) else []
        )

        # Group by strategy
        strategy_stats = {}
        for trade in trade_list:
            strategy = trade.get("strategy", "unknown")
            if strategy not in strategy_stats:
                strategy_stats[strategy] = {
                    "strategy": strategy,
                    "total_trades": 0,
                    "winning_trades": 0,
                    "losing_trades": 0,
                    "total_pnl": 0,
                    "avg_win": 0,
                    "avg_loss": 0,
                    "win_rate": 0,
                    "profit_factor": 0,
                    "max_drawdown": 0,
                }

            profit = trade.get("profit", 0)
            strategy_stats[strategy]["total_trades"] += 1
            strategy_stats[strategy]["total_pnl"] += profit

            if profit > 0:
                strategy_stats[strategy]["winning_trades"] += 1
            else:
                strategy_stats[strategy]["losing_trades"] += 1

        # Calculate derived metrics
        for strategy in strategy_stats:
            stats = strategy_stats[strategy]
            total = stats["total_trades"]
            wins = stats["winning_trades"]
            losses = stats["losing_trades"]

            if total > 0:
                stats["win_rate"] = round((wins / total) * 100, 2)

            # Get wins and losses for averages
            strategy_trades = [t for t in trade_list if t.get("strategy") == strategy]
            win_amounts = [
                t.get("profit", 0) for t in strategy_trades if t.get("profit", 0) > 0
            ]
            loss_amounts = [
                abs(t.get("profit", 0))
                for t in strategy_trades
                if t.get("profit", 0) < 0
            ]

            stats["avg_win"] = (
                round(sum(win_amounts) / len(win_amounts), 2) if win_amounts else 0
            )
            stats["avg_loss"] = (
                round(sum(loss_amounts) / len(loss_amounts), 2) if loss_amounts else 0
            )

            # Profit factor
            total_wins = sum(win_amounts)
            total_losses = sum(loss_amounts)
            stats["profit_factor"] = (
                round(total_wins / total_losses, 2) if total_losses > 0 else 0
            )

        # Convert to list and sort by P&L
        breakdown = list(strategy_stats.values())
        breakdown.sort(key=lambda x: x["total_pnl"], reverse=True)

        return jsonify(breakdown)
    except Exception as e:
        logger.error(f"Error getting strategy breakdown: {str(e)}")
        return jsonify({"error": str(e)}), 500


@core_bp.route("/api/data/verify", endpoint="core_verify_data_quality")
def verify_data_quality():
    """
    Run comprehensive data quality checks

    Note: Always returns 200 status. The 'status' field in the response
    indicates data health ('healthy', 'warning', 'error'). Returning 200
    allows the frontend to display partial results even when issues exist.

    Returns health status, issues, and check results
    """
    try:
        from dashboard.services.data_validator import CsvDataValidator

        validator = CsvDataValidator()
        results = {
            "status": "healthy",  # or 'warning' or 'error'
            "checks": {},
            "issues": [],
        }

        # Check 1: CSV file exists
        trades_csv = LOGS_DIR / "trades.csv"
        if not trades_csv.exists():
            results["status"] = "warning"
            results["issues"].append("trades.csv not found - using sample data")
            return jsonify(results)

        # Check 2: Validate CSV structure
        csv_validation = validator.validate_csv_data(trades_csv)
        results["checks"]["csv_validation"] = csv_validation

        if not csv_validation["valid"]:
            results["status"] = "error"
            results["issues"].extend(csv_validation["issues"])

        # Check 3: Calculate total P&L and verify integrity
        trades = data_parser.get_all_trades()
        if trades:
            calculated_pnl = data_parser.calculate_total_pnl(trades)
            results["checks"]["total_pnl"] = calculated_pnl

            # Check 4: Win rate in valid range
            win_rate = data_parser.calculate_win_rate(trades)
            results["checks"]["win_rate"] = win_rate

            if win_rate == 100.0 and len(trades) > 10:
                results["status"] = "warning"
                results["issues"].append(
                    f"Win rate is exactly 100% with {len(trades)} trades - suspicious"
                )

            # Check 5: No outlier trades
            pnls = [t["pnl_usd"] for t in trades]
            if pnls and len(pnls) > 1:
                mean = sum(pnls) / len(pnls)
                variance = sum((x - mean) ** 2 for x in pnls) / len(pnls)
                std = variance**0.5

                outliers = [p for p in pnls if abs(p - mean) > 3 * std]
                if outliers:
                    results["status"] = "warning"
                    results["issues"].append(f"Found {len(outliers)} outlier trades")

            # Check 6: No future timestamps
            future_trades = [
                t
                for t in trades
                if datetime.fromisoformat(t["entry_time"]) > datetime.now()
            ]
            if future_trades:
                results["status"] = "error"
                results["issues"].append(
                    f"{len(future_trades)} trades have future timestamps"
                )

        return jsonify(results)
    except FileNotFoundError as e:
        # No data files - return warning status
        logger.warning(f"Data files not found: {str(e)}")
        return (
            jsonify(
                {
                    "status": "warning",
                    "checks": {},
                    "issues": ["No trading data files found yet"],
                    "message": "Bot hasn't generated any trades yet",
                }
            ),
            200,
        )
    except Exception as e:
        # Return safe error response instead of 500
        logger.error(f"Error verifying data quality: {str(e)}", exc_info=True)
        return (
            jsonify(
                {
                    "status": "error",
                    "checks": {},
                    "issues": [f"Verification failed: {str(e)}"],
                    "message": "Could not verify data quality",
                }
            ),
            200,
        )  # Return 200 instead of 500


@core_bp.route("/api/recent_activity", endpoint="core_get_recent_activity")
def get_recent_activity():
    """
    Get recent activity from logs/activity.json (engine-written).

    Returns last 100 activities sorted by timestamp.
    Tolerates missing or malformed file; returns [] on error.
    No mock/sample data.
    """
    try:
        activities = engine_state_reader.get_activity()
        activities.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return jsonify(activities[:100])
    except Exception as e:
        logger.error(f"Error getting recent activity: {str(e)}")
        return jsonify([])


# ============================================================================
# Phase 9: Authoritative Dashboard API (read-only)
# ============================================================================


@core_bp.route("/api/dashboard/system", endpoint="core_api_dashboard_system")
def api_dashboard_system():
    """
    Global system overview for mission control header.
    Engine status, paper mode, execution gate, last heartbeat, error state.
    """
    try:
        state = engine_state_reader.get_bot_state()
        bot_status_info = engine_state_reader.get_bot_status_from_engine()
        config = config_manager.get_config()
        gate = execution_gate_status(config or {})

        status = "unknown"
        if isinstance(state, dict) and state.get("status"):
            status = state.get("status", "unknown")
        elif bot_status_info:
            status = "running" if bot_status_info.get("running") else ("paused" if bot_status_info.get("paused") else "stopped")

        paper_trading = bool((config or {}).get("paper_trading", True))
        last_update = (state or {}).get("last_update") or (bot_status_info or {}).get("last_update") or ""

        return jsonify({
            "engine_status": status,
            "engine_status_label": (
                "Running" if status == "running" else
                "Paused" if status == "paused" else
                "Stopped" if status == "stopped" else str(status)
            ),
            "paper_trading": paper_trading,
            "paper_trading_label": "Paper trading" if paper_trading else "Live (config override)",
            "execution_gate": {
                "allowed": gate.get("allowed", False),
                "reason": gate.get("reason", ""),
                "paused": gate.get("paused", False),
                "kill_switch": gate.get("kill_switch", False),
                "emergency_kill": gate.get("emergency_kill", False),
            },
            "last_heartbeat": last_update,
            "runtime_seconds": (state or {}).get("runtime_seconds"),
            "error_state": None,
            "source": "engine" if engine_state_reader.has_engine_state() else "none",
        })
    except Exception as e:
        logger.error(f"Dashboard system API: {e}", exc_info=True)
        return jsonify({
            "engine_status": "unknown",
            "engine_status_label": "Unknown",
            "paper_trading": True,
            "paper_trading_label": "Unknown",
            "execution_gate": {"allowed": False, "reason": str(e), "paused": False, "kill_switch": False, "emergency_kill": False},
            "last_heartbeat": "",
            "runtime_seconds": None,
            "error_state": str(e),
            "source": "error",
        })


@core_bp.route("/api/dashboard/trades", endpoint="core_api_dashboard_trades")
def api_dashboard_trades():
    """Normalized trades for dashboard: OPEN (engine) + CLOSED (CSV). Lifecycle: OPEN, CLOSED, CANCELLED, ERROR."""
    try:
        data = get_normalized_trades(data_parser, engine_state_reader)
        return jsonify(data)
    except Exception as e:
        logger.error(f"Dashboard trades API: {e}", exc_info=True)
        return jsonify({"open": [], "closed": [], "all": [], "count_open": 0, "count_closed": 0, "error": str(e)})


@core_bp.route("/api/dashboard/strategies", endpoint="core_api_dashboard_strategies")
def api_dashboard_strategies():
    """Strategy status for dashboard: names, health (from performance), open count, last signal (from activity)."""
    try:
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
        logger.error(f"Dashboard strategies API: {e}", exc_info=True)
        return jsonify({"strategies": [], "error": str(e)})


@core_bp.route("/api/dashboard/diagnostics", endpoint="core_api_dashboard_diagnostics")
def api_dashboard_diagnostics():
    """
    Phase 9B: Read-only diagnostics for validation without terminal.
    Returns: connected data sources, last successful read per source, row counts,
    engine heartbeat age, execution gate state.
    """
    try:
        state = engine_state_reader.get_bot_state()
        config = config_manager.get_config()
        gate = execution_gate_status(config or {})
        last_update = (state or {}).get("last_update") or ""

        # Data sources with last read time (file mtime where applicable) and row counts
        sources = []

        # Engine state (bot_state.json)
        state_path = BASE_DIR / "state" / "bot_state.json"
        state_mtime = None
        if state_path.exists():
            try:
                state_mtime = datetime.fromtimestamp(state_path.stat().st_mtime, tz=timezone.utc).isoformat()
            except OSError:
                pass
        sources.append({
            "id": "engine_state",
            "name": "Engine state (bot_state.json)",
            "last_success_read": state_mtime,
            "row_count": 1 if state and isinstance(state, dict) else 0,
            "ok": engine_state_reader.has_engine_state(),
        })

        # Trades (normalized from CSV + engine)
        try:
            trades_data = get_normalized_trades(data_parser, engine_state_reader)
            open_count = trades_data.get("count_open", 0) or len(trades_data.get("open", []))
            closed_count = trades_data.get("count_closed", 0) or len(trades_data.get("closed", []))
            sources.append({
                "id": "trades",
                "name": "Trades (CSV + engine)",
                "last_success_read": last_update or None,
                "row_count": open_count + closed_count,
                "ok": True,
            })
        except Exception as e:
            sources.append({
                "id": "trades",
                "name": "Trades (CSV + engine)",
                "last_success_read": None,
                "row_count": 0,
                "ok": False,
                "error": str(e),
            })

        # Strategies
        try:
            names = data_parser.get_all_strategy_names()
            sources.append({
                "id": "strategies",
                "name": "Strategies",
                "last_success_read": last_update or None,
                "row_count": len(names),
                "ok": True,
            })
        except Exception as e:
            sources.append({
                "id": "strategies",
                "name": "Strategies",
                "last_success_read": None,
                "row_count": 0,
                "ok": False,
                "error": str(e),
            })

        # Activity log
        activity_path = BASE_DIR / "logs" / "activity.json"
        activity_mtime = None
        activity_count = 0
        if activity_path.exists():
            try:
                activity_mtime = datetime.fromtimestamp(activity_path.stat().st_mtime, tz=timezone.utc).isoformat()
                activity = engine_state_reader.get_activity()
                activity_count = len(activity) if isinstance(activity, list) else 0
            except (OSError, TypeError):
                pass
        sources.append({
            "id": "activity",
            "name": "Activity log",
            "last_success_read": activity_mtime,
            "row_count": activity_count,
            "ok": True,
        })

        # Heartbeat age in seconds
        heartbeat_age_seconds = None
        if last_update:
            try:
                dt = datetime.fromisoformat(last_update.replace("Z", "+00:00"))
                heartbeat_age_seconds = (datetime.now(timezone.utc) - dt).total_seconds()
            except (ValueError, TypeError):
                pass

        return jsonify({
            "data_sources": sources,
            "engine_heartbeat": last_update or None,
            "engine_heartbeat_age_seconds": round(heartbeat_age_seconds, 1) if heartbeat_age_seconds is not None else None,
            "execution_gate": {
                "allowed": gate.get("allowed", False),
                "reason": gate.get("reason", ""),
                "paused": gate.get("paused", False),
                "kill_switch": gate.get("kill_switch", False),
                "emergency_kill": gate.get("emergency_kill", False),
            },
            "engine_status": (state or {}).get("status") if isinstance(state, dict) else None,
        })
    except Exception as e:
        logger.error(f"Dashboard diagnostics API: {e}", exc_info=True)
        return jsonify({
            "data_sources": [],
            "engine_heartbeat": None,
            "engine_heartbeat_age_seconds": None,
            "execution_gate": {"allowed": False, "reason": str(e), "paused": False, "kill_switch": False, "emergency_kill": False},
            "engine_status": None,
            "error": str(e),
        })


# ============================================================================
# CRYPTO PRICE API ENDPOINTS
# ============================================================================


@core_bp.route("/api/crypto/current_prices", endpoint="core_get_crypto_current_prices")
def get_crypto_current_prices():
    """Get current prices for all tracked crypto symbols"""
    try:
        from services.crypto_price_manager import CryptoPriceManager

        # Load config
        config = config_manager.get_config()
        symbols = config.get("crypto_symbols", ["BTC", "ETH", "SOL", "XRP"])

        # Get prices
        price_manager = CryptoPriceManager(logger=logger, config=config)
        prices = price_manager.get_current_prices(symbols)

        # Convert Decimal to float for JSON serialization
        result = {}
        for symbol, data in prices.items():
            result[symbol] = {
                "symbol": data["symbol"],
                "name": data["name"],
                "price": float(data["price_usd"]),
                "change_24h": float(data.get("change_24h_pct", 0)),
                "sources": data["sources"],
                "sources_count": data["sources_count"],
                "last_updated": data["last_updated"],
            }

        return jsonify({"prices": result})
    except Exception as e:
        logger.error(f"Error getting crypto prices: {str(e)}")
        return jsonify({"error": str(e)}), 500


@core_bp.route("/api/crypto/price_history", endpoint="core_get_crypto_price_history")
def get_crypto_price_history():
    """Get historical prices for a specific symbol"""
    try:
        from services.crypto_price_manager import CryptoPriceManager

        symbol = request.args.get("symbol", "BTC")
        timeframe = request.args.get("timeframe", "24h")

        # Parse timeframe to hours
        timeframe_map = {"1h": 1, "24h": 24, "7d": 168, "30d": 720}
        hours = timeframe_map.get(timeframe, 24)

        # Load config and get history
        config = config_manager.get_config()
        price_manager = CryptoPriceManager(logger=logger, config=config)
        history = price_manager.get_price_history(symbol, hours)

        # Convert to format for Chart.js
        history_data = []

        for record in history:
            history_data.append(
                {"timestamp": record["timestamp"], "price": float(record["price_usd"])}
            )

        # Calculate change percentage
        change_percent = 0
        if len(history_data) >= 2:
            first_price = history_data[0]["price"]
            last_price = history_data[-1]["price"]
            if first_price > 0:
                change_percent = ((last_price - first_price) / first_price) * 100

        return jsonify(
            {
                "symbol": symbol,
                "timeframe": timeframe,
                "history": history_data,
                "change_percent": change_percent,
            }
        )
    except Exception as e:
        logger.error(f"Error getting price history: {str(e)}")
        return jsonify({"error": str(e)}), 500


@core_bp.route("/api/crypto/alerts", endpoint="core_get_crypto_alerts")
def get_crypto_alerts():
    """Get recently triggered price alerts"""
    try:
        from services.price_alert_manager import PriceAlertManager

        # Load config
        config = config_manager.get_config()
        alert_manager = PriceAlertManager(logger=logger, config=config)

        # Get active alerts
        active_alerts = alert_manager.get_active_alerts()

        return jsonify(
            {"active_alerts": active_alerts, "enabled": alert_manager.enabled}
        )
    except Exception as e:
        logger.error(f"Error getting alerts: {str(e)}")
        return jsonify({"error": str(e)}), 500


@core_bp.route("/api/market_reality/status", endpoint="core_get_market_reality_status")
def get_market_reality_status():
    """Get validation status of all crypto prediction markets"""
    try:
        from services.market_validator import MarketValidator
        from services.crypto_price_manager import CryptoPriceManager

        # Load config
        config = config_manager.get_config()

        # Get current crypto prices
        symbols = config.get("crypto_symbols", ["BTC", "ETH", "SOL", "XRP"])
        price_manager = CryptoPriceManager(logger=logger, config=config)
        current_prices = price_manager.get_current_prices(symbols)

        # Get markets from opportunities log (last 100)
        opportunities = data_parser.parse_opportunities()

        # Extract unique markets
        markets = []
        seen_markets = set()
        for opp in opportunities[:100]:
            market_name = opp.get("market", "")
            if market_name and market_name not in seen_markets:
                seen_markets.add(market_name)
                markets.append(
                    {
                        "market_name": market_name,
                        "yes_price": opp.get("yes_price", 0.5),
                        "no_price": opp.get("no_price", 0.5),
                    }
                )

        # Validate each market
        validator = MarketValidator(logger=logger)
        validations = []

        for market in markets:
            validation = validator.validate_market_against_reality(
                market, current_prices
            )
            if validation:  # Only include crypto markets
                # Convert confidence string to numeric value
                confidence_map = {
                    "none": 0.0,
                    "low": 0.3,
                    "medium": 0.5,
                    "high": 0.7,
                    "very_high": 0.9,
                }
                confidence_numeric = confidence_map.get(validation["confidence"], 0.5)

                validations.append(
                    {
                        "market_name": market["market_name"],
                        "symbol": validation["symbol"],
                        "current_price": validation["current_price"],
                        "threshold": validation["threshold"],
                        "direction": validation["direction"],
                        "reality_met": validation["reality_met"],
                        "market_yes_price": validation["market_yes_price"],
                        "expected_yes_price": validation["expected_yes_price"],
                        "discrepancy": validation["discrepancy"],
                        "valid": validation["valid"],
                        "opportunity": validation.get("opportunity"),
                        "profit_potential_pct": validation.get(
                            "profit_potential_pct", 0
                        ),
                        "confidence": confidence_numeric,
                    }
                )

        return jsonify(
            {
                "markets": validations,
                "total_markets": len(validations),
                "mispriced_count": sum(1 for v in validations if not v["valid"]),
                "timestamp": datetime.now().isoformat(),
            }
        )
    except Exception as e:
        logger.error(f"Error getting market reality status: {str(e)}")
        return jsonify({"error": str(e)}), 500


@core_bp.route("/api/crypto/price_check", endpoint="core_check_specific_price")
def check_specific_price():
    """Check if a specific price threshold has been crossed"""
    try:
        from services.crypto_price_manager import CryptoPriceManager
        from decimal import Decimal

        symbol = request.args.get("symbol", "BTC")
        threshold = float(request.args.get("threshold", 100000))
        direction = request.args.get("direction", "above")

        # Load config and check
        config = config_manager.get_config()
        price_manager = CryptoPriceManager(logger=logger, config=config)

        is_crossed = price_manager.check_price_alert(
            symbol, Decimal(str(threshold)), direction
        )

        # Get current price
        prices = price_manager.get_current_prices([symbol])
        current_price = float(prices[symbol]["price_usd"]) if symbol in prices else None

        return jsonify(
            {
                "symbol": symbol,
                "threshold": threshold,
                "direction": direction,
                "current_price": current_price,
                "threshold_crossed": is_crossed,
                "timestamp": datetime.now().isoformat(),
            }
        )
    except Exception as e:
        logger.error(f"Error checking price: {str(e)}")
        return jsonify({"error": str(e)}), 500


@core_bp.route("/analytics", endpoint="core_analytics_page")
def analytics_page():
    """Render analytics page"""
    return render_template("analytics.html")


# ========================
# Analytics API Endpoints
# ========================


@core_bp.route("/api/analytics/strategy_performance", endpoint="core_get_strategy_performance_analytics")
def get_strategy_performance_analytics():
    """Get comprehensive strategy performance metrics (Phase 7E: regime slicing)."""
    try:
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")
        volatility_regime = request.args.get("volatility_regime")
        event_window_start = request.args.get("event_window_start")
        event_window_end = request.args.get("event_window_end")

        from services.research_service import filter_trades_by_regime
        trades_data = data_parser.get_trades(
            start_date=start_date, end_date=end_date, per_page=10000
        )
        trades = trades_data.get("trades", [])
        trades = filter_trades_by_regime(
            trades,
            start_date=start_date,
            end_date=end_date,
            volatility_regime=volatility_regime,
            event_window_start=event_window_start,
            event_window_end=event_window_end,
        )
        strategies = strategy_analytics.get_all_strategies_performance_from_trades(
            trades
        )
        return jsonify({"strategies": strategies})
    except Exception as e:
        logger.error(f"Error getting strategy performance: {str(e)}")
        return jsonify({"error": str(e)}), 500


@core_bp.route("/api/analytics/market_performance", endpoint="core_get_market_performance_analytics")
def get_market_performance_analytics():
    """Get market performance analysis"""
    try:
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")
        min_trades = int(request.args.get("min_trades", 3))
        sort_by = request.args.get("sort", "total_pnl")

        markets = market_analytics.get_market_performance(
            start_date=start_date, end_date=end_date, min_trades=min_trades
        )

        # Sort by requested metric
        if sort_by in [
            "total_pnl",
            "win_rate",
            "total_trades",
            "frequency",
            "success_score",
        ]:
            markets.sort(key=lambda x: x.get(sort_by, 0), reverse=True)

        return jsonify({"markets": markets})
    except Exception as e:
        logger.error(f"Error getting market performance: {str(e)}")
        return jsonify({"error": str(e)}), 500


@core_bp.route("/api/analytics/market_performance/top", endpoint="core_get_top_markets")
def get_top_markets():
    """Get top N markets by specified metric"""
    try:
        n = int(request.args.get("n", 10))
        metric = request.args.get("metric", "total_pnl")
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")

        markets = market_analytics.get_top_markets(
            n=n, metric=metric, start_date=start_date, end_date=end_date
        )

        return jsonify({"markets": markets})
    except Exception as e:
        logger.error(f"Error getting top markets: {str(e)}")
        return jsonify({"error": str(e)}), 500


@core_bp.route("/api/analytics/market_performance/worst", endpoint="core_get_worst_markets")
def get_worst_markets():
    """Get worst N markets by specified metric"""
    try:
        n = int(request.args.get("n", 10))
        metric = request.args.get("metric", "total_pnl")
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")

        markets = market_analytics.get_worst_markets(
            n=n, metric=metric, start_date=start_date, end_date=end_date
        )

        return jsonify({"markets": markets})
    except Exception as e:
        logger.error(f"Error getting worst markets: {str(e)}")
        return jsonify({"error": str(e)}), 500


@core_bp.route("/api/analytics/time/hour_analysis", endpoint="core_get_hour_analysis")
def get_hour_analysis():
    """Get hour of day analysis"""
    try:
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")

        analysis = time_analytics.get_hour_of_day_analysis(start_date, end_date)

        return jsonify(analysis)
    except Exception as e:
        logger.error(f"Error getting hour analysis: {str(e)}")
        return jsonify({"error": str(e)}), 500


@core_bp.route("/api/analytics/time/day_analysis", endpoint="core_get_day_analysis")
def get_day_analysis():
    """Get day of week analysis"""
    try:
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")

        analysis = time_analytics.get_day_of_week_analysis(start_date, end_date)

        return jsonify(analysis)
    except Exception as e:
        logger.error(f"Error getting day analysis: {str(e)}")
        return jsonify({"error": str(e)}), 500


@core_bp.route("/api/analytics/time/monthly", endpoint="core_get_monthly_performance")
def get_monthly_performance():
    """Get monthly performance"""
    try:
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")

        months = time_analytics.get_monthly_performance(start_date, end_date)

        return jsonify({"months": months})
    except Exception as e:
        logger.error(f"Error getting monthly performance: {str(e)}")
        return jsonify({"error": str(e)}), 500


@core_bp.route("/api/analytics/time/best_times", endpoint="core_get_best_trading_times")
def get_best_trading_times():
    """Get best trading times"""
    try:
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")

        best_times = time_analytics.get_best_trading_times(start_date, end_date)

        return jsonify(best_times)
    except Exception as e:
        logger.error(f"Error getting best trading times: {str(e)}")
        return jsonify({"error": str(e)}), 500


@core_bp.route("/api/analytics/risk_metrics", endpoint="core_get_risk_metrics_analytics")
def get_risk_metrics_analytics():
    """Get comprehensive risk metrics"""
    try:
        strategy = request.args.get("strategy")
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")

        metrics = risk_metrics.calculate_all_risk_metrics(
            strategy_name=strategy, start_date=start_date, end_date=end_date
        )

        return jsonify(metrics)
    except Exception as e:
        logger.error(f"Error getting risk metrics: {str(e)}")
        return jsonify({"error": str(e)}), 500


@core_bp.route("/api/analytics/drawdown_history", endpoint="core_get_drawdown_history")
def get_drawdown_history():
    """Get drawdown history for visualization"""
    try:
        strategy = request.args.get("strategy")
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")

        history = risk_metrics.calculate_drawdown_history(
            strategy_name=strategy, start_date=start_date, end_date=end_date
        )

        return jsonify(history)
    except Exception as e:
        logger.error(f"Error getting drawdown history: {str(e)}")
        return jsonify({"error": str(e)}), 500


@core_bp.route("/api/analytics/export", endpoint="core_export_analytics")
def export_analytics():
    """Export analytics data to CSV or JSON (Phase 7E: regime params supported)."""
    try:
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")
        fmt = request.args.get("format", "csv").lower()
        volatility_regime = request.args.get("volatility_regime")
        event_window_start = request.args.get("event_window_start")
        event_window_end = request.args.get("event_window_end")

        from services.research_service import filter_trades_by_regime
        trades_data = data_parser.get_trades(
            start_date=start_date, end_date=end_date, per_page=10000
        )
        trades = trades_data.get("trades", [])
        trades = filter_trades_by_regime(
            trades,
            start_date=start_date,
            end_date=end_date,
            volatility_regime=volatility_regime,
            event_window_start=event_window_start,
            event_window_end=event_window_end,
        )
        strategies = strategy_analytics.get_all_strategies_performance_from_trades(
            trades
        )

        if not strategies:
            return jsonify({"error": "No data to export"}), 404

        if fmt == "json":
            return Response(
                json.dumps({"strategies": strategies}, indent=2),
                mimetype="application/json",
                headers={
                    "Content-Disposition": "attachment; filename=analytics_export.json"
                },
            )
        output = io.StringIO()
        fieldnames = strategies[0].keys()
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(strategies)
        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=analytics_export.csv"
            },
        )
    except Exception as e:
        logger.error(f"Error exporting analytics: {str(e)}")
        return jsonify({"error": str(e)}), 500


# ==================== SETTINGS & NOTIFICATIONS API ====================


@settings_bp.route("/settings", endpoint="settings_settings_page")
def settings_page():
    """Render settings page"""
    return render_template("settings.html")


@settings_bp.route("/system-settings", endpoint="settings_system_settings_page")
def system_settings_page():
    """Phase 6B: Centralized System & Settings (trading mode, API keys, updates)."""
    return render_template("system_settings.html")


@settings_bp.route("/settings/advanced", endpoint="settings_advanced_settings_page")
def advanced_settings_page():
    """Render advanced settings page"""
    return render_template("advanced_settings.html")


@settings_bp.route("/api/settings", methods=["GET", "POST"], endpoint="settings_manage_settings")
def manage_settings():
    """
    Manage user settings.

    GET: Return current settings
    POST: Save new settings
    """
    try:
        user_id = 1  # Default user

        if request.method == "GET":
            # Get current settings
            settings = UserSettings.get(user_id)

            # Get notification channels
            channels = NotificationChannel.get_all(user_id)

            # Get notification preferences
            preferences = NotificationPreference.get_all(user_id)

            return jsonify(
                {
                    "success": True,
                    "settings": settings,
                    "channels": channels,
                    "preferences": preferences,
                }
            )

        elif request.method == "POST":
            # Save settings
            data = request.get_json()

            if not data:
                return jsonify({"success": False, "error": "No data provided"}), 400

            # Update user settings
            if "settings" in data:
                UserSettings.update(user_id, data["settings"])

            # Update notification channels
            if "channels" in data:
                for channel_data in data["channels"]:
                    NotificationChannel.create_or_update(
                        user_id, channel_data["channel_type"], channel_data
                    )

            # Update notification preferences
            if "preferences" in data:
                NotificationPreference.bulk_update(user_id, data["preferences"])

            return jsonify({"success": True, "message": "Settings saved successfully"})

    except Exception as e:
        logger.error(f"Error managing settings: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@settings_bp.route("/api/settings/reset", methods=["POST"], endpoint="settings_reset_settings")
def reset_settings():
    """Reset user settings to defaults"""
    try:
        user_id = 1  # Default user

        # Reset user settings
        UserSettings.reset(user_id)

        return jsonify({"success": True, "message": "Settings reset to defaults"})

    except Exception as e:
        logger.error(f"Error resetting settings: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@core_bp.route("/api/notifications/test/<channel_type>", methods=["POST"], endpoint="core_test_notification_channel")
def test_notification_channel(channel_type):
    """
    Send a test notification to a specific channel.

    Args:
        channel_type: Type of channel (discord, slack, email, telegram, webhook)
    """
    try:
        data = request.get_json()

        if not data:
            return (
                jsonify({"success": False, "error": "No configuration provided"}),
                400,
            )

        # Test the channel
        result = notification_service.test_channel(channel_type, data)

        return jsonify(result)

    except Exception as e:
        logger.error(f"Error testing notification channel: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# ========================================
# NEW API ENDPOINTS FOR UX FEATURES
# ========================================


@core_bp.route("/api/workspaces", methods=["GET", "POST"], endpoint="core_manage_workspaces")
def manage_workspaces():
    """Manage user workspaces"""
    try:
        if request.method == "GET":
            # Get workspaces from database or default
            workspaces = [
                {"id": 1, "name": "Overview", "icon": "📊", "layout": {}},
                {"id": 2, "name": "Analytics", "icon": "📈", "layout": {}},
                {"id": 3, "name": "Trading", "icon": "💼", "layout": {}},
            ]
            return jsonify(workspaces)

        elif request.method == "POST":
            # Create new workspace
            data = request.json
            # Would save to database in production
            return jsonify({"success": True, "workspace": data})

    except Exception as e:
        logger.error(f"Error managing workspaces: {str(e)}")
        return jsonify({"error": str(e)}), 500


@core_bp.route("/api/workspaces/<int:workspace_id>/layout", methods=["GET", "POST"], endpoint="core_workspace_layout")
def workspace_layout(workspace_id):
    """Get or update workspace layout"""
    try:
        if request.method == "GET":
            # Get layout from database
            return jsonify({"workspace_id": workspace_id, "layout": {}})

        elif request.method == "POST":
            # Save layout
            layout = request.json
            # Would save to database in production
            return jsonify({"success": True})

    except Exception as e:
        logger.error(f"Error managing workspace layout: {str(e)}")
        return jsonify({"error": str(e)}), 500


@core_bp.route("/api/tax/report", endpoint="core_generate_tax_report")
def generate_tax_report():
    """Generate IRS Form 8949 tax report"""
    try:
        from services.tax_reporter import TaxReporter

        year = int(request.args.get("year", datetime.now().year))
        method = request.args.get("method", "FIFO")

        # Get trades from data parser
        trades = []  # Would get real trades from database/logs

        reporter = TaxReporter()
        report_csv = reporter.generate_form_8949(trades, year, method)

        # Create CSV file response
        output = io.BytesIO()
        output.write(report_csv.encode("utf-8"))
        output.seek(0)

        return send_file(
            output,
            mimetype="text/csv",
            as_attachment=True,
            download_name=f"form_8949_{year}_{method}.csv",
        )

    except Exception as e:
        logger.error(f"Error generating tax report: {str(e)}")
        return jsonify({"error": str(e)}), 500


@core_bp.route("/api/tax/summary", endpoint="core_tax_summary")
def tax_summary():
    """Get tax summary without generating full report"""
    try:
        from services.tax_reporter import TaxReporter

        year = int(request.args.get("year", datetime.now().year))
        method = request.args.get("method", "FIFO")

        trades = []  # Would get real trades

        reporter = TaxReporter()
        summary = reporter.calculate_tax_summary(trades, year, method)

        return jsonify(summary)

    except Exception as e:
        logger.error(f"Error calculating tax summary: {str(e)}")
        return jsonify({"error": str(e)}), 500


@core_bp.route("/api/smart-alerts/analyze", methods=["POST"], endpoint="core_analyze_patterns")
def analyze_patterns():
    """Analyze trading patterns and suggest alerts"""
    try:
        from services.smart_alerts import SmartAlerts

        trades = request.json.get("trades", [])

        alerts = SmartAlerts()
        patterns = alerts.analyze_time_patterns(trades)
        suggestions = alerts.generate_alert_suggestions(patterns)

        return jsonify({"patterns": patterns, "suggestions": suggestions})

    except Exception as e:
        logger.error(f"Error analyzing patterns: {str(e)}")
        return jsonify({"error": str(e)}), 500


@core_bp.route("/api/health/debug", endpoint="core_api_health")
def api_health():
    """Comprehensive health check for debug panel"""
    try:
        health = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "api": "online",
                "database": "online",
                "data_parser": "ready",
                "analytics": "ready",
            },
            "system": {
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage("/").percent,
            },
        }
        return jsonify(health)
    except Exception as e:
        logger.error(f"Error in health check: {str(e)}")
        return jsonify({"status": "error", "error": str(e)}), 500


# Debug health endpoint moved to /api/health/debug - see line 2165


@settings_bp.route("/api/settings/export", methods=["GET"], endpoint="settings_export_settings_get")
def export_settings():
    """
    Export all settings, channels, and preferences as JSON.
    Returns as a downloadable file.
    """
    try:
        user_id = int(request.args.get("user_id", 1))

        # Gather all settings
        settings_data = {
            "export_version": "1.0",
            "export_timestamp": datetime.utcnow().isoformat(),
            "user_settings": UserSettings.get(user_id),
            "notification_channels": NotificationChannel.get_all(user_id),
            "notification_preferences": NotificationPreference.get_all(user_id),
        }

        # Remove sensitive data
        for channel in settings_data["notification_channels"]:
            if "api_key" in channel:
                channel["api_key"] = "***REDACTED***"
            if "config_json" in channel:
                try:
                    config = json.loads(channel["config_json"])
                    if "smtp_password" in config:
                        config["smtp_password"] = "***REDACTED***"
                    if "bot_token" in config:
                        config["bot_token"] = "***REDACTED***"
                    channel["config_json"] = json.dumps(config)
                except:
                    pass

        # Create response
        filename = f"settings_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        json_data = json.dumps(settings_data, indent=2)

        response = Response(json_data, mimetype="application/json")
        response.headers["Content-Disposition"] = f"attachment; filename={filename}"
        return response

    except Exception as e:
        logger.error(f"Error exporting settings: {str(e)}")
        return jsonify({"error": str(e)}), 500


@settings_bp.route("/api/settings/import", methods=["POST"], endpoint="settings_import_settings")
def import_settings():
    """
    Import settings from JSON file.
    Validates and applies the settings.
    """
    try:
        # Get JSON data from request
        if "file" in request.files:
            file = request.files["file"]
            data = json.loads(file.read().decode("utf-8"))
        else:
            data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Validate import version
        if data.get("export_version") != "1.0":
            return jsonify({"error": "Unsupported export version"}), 400

        user_id = int(request.args.get("user_id", 1))
        results = {
            "user_settings": False,
            "notification_channels": 0,
            "notification_preferences": 0,
            "errors": [],
        }

        # Import user settings
        if "user_settings" in data:
            try:
                settings = data["user_settings"]
                # Remove read-only fields
                settings.pop("created_at", None)
                settings.pop("updated_at", None)
                UserSettings.update(user_id, settings)
                results["user_settings"] = True
            except Exception as e:
                results["errors"].append(f"User settings: {str(e)}")

        # Import notification channels
        if "notification_channels" in data:
            for channel in data["notification_channels"]:
                try:
                    # Remove ID and timestamps
                    channel.pop("id", None)
                    channel.pop("created_at", None)
                    channel.pop("updated_at", None)

                    channel_type = channel.pop("channel_type")
                    NotificationChannel.create_or_update(user_id, channel_type, channel)
                    results["notification_channels"] += 1
                except Exception as e:
                    results["errors"].append(
                        f"Channel {channel.get('channel_type', 'unknown')}: {str(e)}"
                    )

        # Import notification preferences
        if "notification_preferences" in data:
            for pref in data["notification_preferences"]:
                try:
                    # Remove ID and timestamps
                    pref.pop("id", None)
                    pref.pop("created_at", None)
                    pref.pop("updated_at", None)

                    notification_type = pref.pop("notification_type")
                    channel_id = pref.pop("channel_id", None)
                    NotificationPreference.create_or_update(
                        user_id, notification_type, channel_id, pref
                    )
                    results["notification_preferences"] += 1
                except Exception as e:
                    results["errors"].append(
                        f"Preference {pref.get('notification_type', 'unknown')}: {str(e)}"
                    )

        return jsonify({"success": True, "results": results}), 200

    except Exception as e:
        logger.error(f"Error importing settings: {str(e)}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    try:
        # Check if config exists
        if not CONFIG_PATH.exists():
            logger.error("Config file not found: %s. Copy config.example.yaml to config.yaml.", CONFIG_PATH)
            sys.exit(1)

        # Create logs directory if it doesn't exist
        LOGS_DIR.mkdir(exist_ok=True)

        # Get debug mode from environment (default to False for security)
        debug_mode = os.environ.get("FLASK_DEBUG", "False").lower() == "true"

        logger.info("Market Strategy Testing Bot - Web Dashboard starting")
        logger.info("Dashboard URL: http://localhost:5000 | Config: %s | Logs: %s", CONFIG_PATH, LOGS_DIR)
        if debug_mode:
            logger.warning("DEBUG MODE ENABLED - For development only")

        # Run Flask app
        # Debug mode is disabled by default for security
        # Set FLASK_DEBUG=true environment variable to enable it
        app.run(host="0.0.0.0", port=5000, debug=debug_mode, use_reloader=debug_mode)

    except KeyboardInterrupt:
        logger.info("Dashboard stopped by user (Ctrl+C)")
        sys.exit(0)
    except Exception as e:
        logger.exception("Failed to start dashboard: %s", e)
        sys.exit(1)


# Production readiness endpoints


# Duplicate /metrics route removed - see line 300 for primary prometheus_metrics endpoint


@core_bp.route("/api/feature-flags", endpoint="core_get_feature_flags")
def get_feature_flags():
    """Get all feature flags"""
    try:
        from services.feature_flags import feature_flags

        return jsonify(
            {
                "feature_flags": feature_flags.get_all(),
                "enabled_count": len(feature_flags.get_enabled()),
                "disabled_count": len(feature_flags.get_disabled()),
            }
        )
    except Exception as e:
        logger.error(f"Error getting feature flags: {str(e)}")
        return jsonify({"error": str(e)}), 500


@core_bp.route("/api/feature-flags/<flag>", methods=["POST"], endpoint="core_toggle_feature_flag")
def toggle_feature_flag(flag):
    """Toggle a feature flag"""
    try:
        from services.feature_flags import feature_flags
        from services.audit_logger import audit_logger

        action = request.json.get("action", "toggle")

        if action == "enable":
            success = feature_flags.enable(flag)
        elif action == "disable":
            success = feature_flags.disable(flag)
        else:
            return jsonify({"error": "Invalid action"}), 400

        if success:
            # Log audit entry
            audit_logger.log_settings_change(
                user_id="system",
                setting_name=f"feature_flag_{flag}",
                old_value=not feature_flags.is_enabled(flag),
                new_value=feature_flags.is_enabled(flag),
                ip_address=request.remote_addr,
            )

            return jsonify(
                {
                    "success": True,
                    "flag": flag,
                    "enabled": feature_flags.is_enabled(flag),
                }
            )
        else:
            return jsonify({"error": "Failed to toggle flag"}), 400

    except Exception as e:
        logger.error(f"Error toggling feature flag: {str(e)}")
        return jsonify({"error": str(e)}), 500


@core_bp.route("/api/positions", endpoint="core_get_positions")
def get_positions():
    """Get all positions. Prefers engine state (state/bot_state.json)."""
    try:
        # Prefer engine state when available
        engine_positions = engine_state_reader.get_positions_from_engine()
        if engine_state_reader.has_engine_state():
            status_filter = request.args.get("status", "all")
            if status_filter == "open":
                positions = [p for p in engine_positions if p.get("quantity", 0)]
            else:
                positions = engine_positions
            return jsonify(
                {"positions": positions, "count": len(positions), "stats": {}, "source": "engine"}
            )

        # Fallback: position_tracker (legacy)
        from services.position_tracker import position_tracker

        status_filter = request.args.get("status", "all")
        if status_filter == "open":
            positions = position_tracker.get_open_positions()
        elif status_filter == "closed":
            positions = position_tracker.get_closed_positions()
        else:
            positions = position_tracker.get_all_positions()

        return jsonify(
            {
                "positions": [p.to_dict() for p in positions],
                "count": len(positions),
                "stats": position_tracker.get_position_stats(),
            }
        )
    except Exception as e:
        logger.error(f"Error getting positions: {str(e)}")
        return jsonify({"error": str(e)}), 500


@core_bp.route("/api/portfolio", endpoint="core_get_portfolio")
def get_portfolio():
    """Get portfolio information. Prefers engine state (state/bot_state.json)."""
    try:
        # Prefer engine state when available
        engine_portfolio = engine_state_reader.get_portfolio_from_engine()
        if engine_portfolio is not None:
            return jsonify(engine_portfolio)

        # Fallback: portfolio_manager (legacy)
        from services.portfolio_manager import portfolio_manager

        return jsonify(portfolio_manager.export_to_dict())
    except Exception as e:
        logger.error(f"Error getting portfolio: {str(e)}")
        return jsonify({"error": str(e)}), 500


@core_bp.route("/api/realtime/status", endpoint="core_get_realtime_status")
def get_realtime_status():
    """Get WebSocket server status and statistics"""
    try:
        if realtime_server:
            stats = realtime_server.get_connection_stats()
            return jsonify({"enabled": True, "stats": stats})
        else:
            return jsonify(
                {"enabled": False, "message": "WebSocket server not initialized"}
            )
    except Exception as e:
        logger.error(f"Error getting realtime status: {str(e)}")
        return jsonify({"error": str(e)}), 500


# ============================================================================
# Lazy imports for PR#20K - Backtesting, Risk, UX Features
# These are imported inside route handlers to avoid heavy/numeric libs at import time
# (prevents FPE crashes in some environments). init_trading_db() is called on first use.
# ============================================================================

_trading_db_initialized = False


def _ensure_trading_db():
    """Call init_trading_db() once. Used by routes that need TradeJournal/Alert/APIKey."""
    global _trading_db_initialized
    if not _trading_db_initialized:
        try:
            from database.models import init_trading_db
            init_trading_db()
            _trading_db_initialized = True
        except Exception as e:
            logger.exception("Failed to initialize trading database: %s", e)
            raise


@core_bp.route("/api_keys", endpoint="core_api_keys_page")
def api_keys_page():
    """Render API key management page"""
    return render_template("api_keys.html")


@strategies_bp.route("/strategy_comparison", endpoint="strategies_comparison_page")
def comparison_page():
    """Render strategy comparison page"""
    return render_template("strategy_comparison.html")


@journal_bp.route("/trade_journal", endpoint="journal_journal_page")
def journal_page():
    """Render trade journal page"""
    return render_template("trade_journal.html")


@core_bp.route("/alerts", endpoint="core_alerts_page")
def alerts_page():
    """Render alerts management page"""
    return render_template("alerts.html")


# Phase 7C: Canonical credential system is SecureConfigManager. All writes go to POST /api/settings/data-sources.
# DB api_keys is deprecated for writes; list/save/test below return 410 and point to System Settings.

def _mask_secret(value: str, visible_tail: int = 4) -> str:
    """Mask a secret for UI display. Never log or expose the original."""
    if not value or not isinstance(value, str):
        return "••••"
    if len(value) <= visible_tail:
        return "••••"
    return "••••••••" + value[-visible_tail:]


@core_bp.route("/api/keys/list", endpoint="core_list_api_keys")
def list_api_keys():
    """Deprecated. Use GET /api/settings/integrations. Credentials are in SecureConfigManager only."""
    return (
        jsonify({
            "deprecated": True,
            "message": "Use System & Settings for API keys. Canonical list: GET /api/settings/integrations",
            "redirect": "/system-settings",
        }),
        410,
    )


@core_bp.route("/api/keys/test", methods=["POST"], endpoint="core_test_api_key_deprecated")
def test_api_key_deprecated():
    """Deprecated. Use POST /api/settings/test-connection. Canonical test is in System Settings."""
    return (
        jsonify({
            "deprecated": True,
            "message": "Use System & Settings to test connections. Canonical: POST /api/settings/test-connection",
            "redirect": "/system-settings",
        }),
        410,
    )


@core_bp.route("/api/keys/save", methods=["POST"], endpoint="core_save_api_key_deprecated")
def save_api_key_deprecated():
    """Deprecated. All credential writes go to SecureConfigManager via POST /api/settings/data-sources."""
    return (
        jsonify({
            "deprecated": True,
            "message": "Save API keys in System & Settings. Canonical write: POST /api/settings/data-sources",
            "redirect": "/system-settings",
        }),
        410,
    )


# API Routes for Strategy Comparison
@strategies_bp.route("/api/strategies/list", endpoint="strategies_list_strategies")
def list_strategies():
    """List available strategies"""
    try:
        strategies = [
            "polymarket_arbitrage",
            "crypto_momentum",
            "mean_reversion",
            "volatility_breakout",
        ]
        return jsonify({"success": True, "strategies": strategies})
    except Exception as e:
        logger.error(f"Error listing strategies: {e}")
        return jsonify({"success": False, "error": str(e)})


@strategies_bp.route("/api/strategies/compare", methods=["POST"], endpoint="strategies_compare_strategies")
def compare_strategies():
    """Compare multiple strategies: by saved run_ids or by running backtests (Phase 7E)."""
    try:
        from services.research_service import get_run_ids_for_comparison
        data = request.get_json() or {}
        run_ids = data.get("run_ids", [])
        strategies = data.get("strategies", [])
        start_date_str = data.get("start_date")
        end_date_str = data.get("end_date")

        comparison = {}
        equity_curves = {}
        labels = []

        if run_ids:
            runs = get_run_ids_for_comparison(run_ids)
            for r in runs:
                name = r.get("strategy", "unknown") + " (" + r.get("run_id", "") + ")"
                labels.append(name)
                m = r.get("metrics", {})
                comparison[name] = {
                    "total_return": m.get("return_pct", 0),
                    "win_rate": m.get("win_rate", 0),
                    "sharpe_ratio": m.get("sharpe_ratio", 0),
                    "max_drawdown": m.get("max_drawdown", 0),
                    "total_trades": m.get("total_trades", 0),
                }
                equity_curves[name] = r.get("equity_curve", [])
        elif strategies and start_date_str and end_date_str:
            from services.backtesting_engine import backtesting_engine
            start_date = datetime.fromisoformat(start_date_str)
            end_date = datetime.fromisoformat(end_date_str)
            for strategy_name in strategies:
                class PlaceholderStrategy:
                    __name__ = strategy_name
                result = backtesting_engine.run_backtest(
                    PlaceholderStrategy(), start_date, end_date
                )
                if result.get("success"):
                    m = result.get("metrics", {})
                    comparison[strategy_name] = {
                        "total_return": m.get("return_pct", 0),
                        "win_rate": m.get("win_rate", 0),
                        "sharpe_ratio": m.get("sharpe_ratio", 0),
                        "max_drawdown": m.get("max_drawdown", 0),
                        "total_trades": m.get("total_trades", 0),
                    }
                    equity_curves[strategy_name] = result.get("equity_curve", [])
        else:
            return jsonify({
                "success": False,
                "error": "Provide run_ids or (strategies + start_date + end_date)",
            }), 400

        return jsonify({
            "success": True,
            "comparison": comparison,
            "equity_curves": equity_curves,
        })
    except Exception as e:
        logger.error(f"Error comparing strategies: {e}")
        return jsonify({"success": False, "error": str(e)})


# API Routes for Trade Journal
@journal_bp.route("/api/trade_journal/list", endpoint="journal_list_journal_entries")
def list_journal_entries():
    """List all trade journal entries"""
    try:
        _ensure_trading_db()
        from database.models import TradeJournal
        entries = TradeJournal.get_all()
        return jsonify({"success": True, "entries": entries})
    except Exception as e:
        logger.error(f"Error listing journal entries: {e}")
        return jsonify({"success": False, "error": str(e)})


@journal_bp.route("/api/trade_journal/save", methods=["POST"], endpoint="journal_save_journal_entry_legacy")
def save_journal_entry():
    """Save trade journal entry"""
    try:
        _ensure_trading_db()
        from database.models import TradeJournal
        data = request.get_json()

        entry_id = TradeJournal.create(
            entry_reason=data.get("entry_reason"),
            confidence_level=data.get("confidence_level"),
        )

        if data.get("exit_reason") or data.get("lessons_learned") or data.get("rating"):
            TradeJournal.update(
                entry_id,
                exit_reason=data.get("exit_reason"),
                lessons_learned=data.get("lessons_learned"),
                rating=data.get("rating"),
            )

        return jsonify({"success": True, "entry_id": entry_id})
    except Exception as e:
        logger.error(f"Error saving journal entry: {e}")
        return jsonify({"success": False, "error": str(e)})


# API Routes for Alerts
@core_bp.route("/api/alerts/list", endpoint="core_list_alerts")
def list_alerts():
    """List all alerts"""
    try:
        from services.alert_manager import alert_manager
        alerts = alert_manager.get_all_alerts()
        return jsonify({"success": True, "alerts": alerts})
    except Exception as e:
        logger.error(f"Error listing alerts: {e}")
        return jsonify({"success": False, "error": str(e)})


@core_bp.route("/api/alerts/create", methods=["POST"], endpoint="core_create_alert")
def create_alert():
    """Create new alert"""
    try:
        from services.alert_manager import alert_manager
        data = request.get_json()
        alert_id = alert_manager.create_alert(
            data.get("alert_type"),
            data.get("condition"),
            enabled=data.get("enabled", True),
        )
        return jsonify({"success": True, "alert_id": alert_id})
    except Exception as e:
        logger.error(f"Error creating alert: {e}")
        return jsonify({"success": False, "error": str(e)})


@core_bp.route("/api/alerts/<int:alert_id>/toggle", methods=["POST"], endpoint="core_toggle_alert")
def toggle_alert(alert_id):
    """Toggle alert enabled/disabled"""
    try:
        from services.alert_manager import alert_manager
        data = request.get_json()
        alert_manager.update_alert(alert_id, enabled=data.get("enabled"))
        return jsonify({"success": True})
    except Exception as e:
        logger.error(f"Error toggling alert: {e}")
        return jsonify({"success": False, "error": str(e)})


@core_bp.route("/api/alerts/<int:alert_id>/delete", methods=["DELETE"], endpoint="core_delete_alert")
def delete_alert(alert_id):
    """Delete alert"""
    try:
        from services.alert_manager import alert_manager
        alert_manager.delete_alert(alert_id)
        return jsonify({"success": True})
    except Exception as e:
        logger.error(f"Error deleting alert: {e}")
        return jsonify({"success": False, "error": str(e)})


# API Routes for Backtesting (Phase 7E: research-grade; no execution impact)
@core_bp.route("/api/backtest/run", methods=["POST"], endpoint="core_run_backtest")
def run_backtest():
    """Run backtest for a strategy; result is stored for comparison/export."""
    try:
        from services.backtesting_engine import backtesting_engine
        from services.research_service import store_backtest_run
        data = request.get_json()
        strategy_name = data.get("strategy")
        start_date = datetime.fromisoformat(data.get("start_date"))
        end_date = datetime.fromisoformat(data.get("end_date"))

        class PlaceholderStrategy:
            __name__ = strategy_name

        result = backtesting_engine.run_backtest(
            PlaceholderStrategy(), start_date, end_date
        )
        if result.get("success"):
            run_id = store_backtest_run(result)
            result["run_id"] = run_id
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error running backtest: {e}")
        return jsonify({"success": False, "error": str(e)})


@core_bp.route("/api/backtest/runs", endpoint="core_list_backtest_runs")
def list_backtest_runs():
    """List recent backtest runs for comparison/export (Phase 7E)."""
    try:
        from services.research_service import get_backtest_runs
        limit = request.args.get("limit", 20, type=int)
        runs = get_backtest_runs(limit=min(limit, 50))
        return jsonify({"success": True, "runs": runs})
    except Exception as e:
        logger.error(f"Error listing backtest runs: {e}")
        return jsonify({"success": False, "error": str(e)})


@core_bp.route("/api/backtest/runs/<run_id>", endpoint="core_get_backtest_run_by_id")
def get_backtest_run_by_id(run_id):
    """Get a single backtest run by id (Phase 7E)."""
    try:
        from services.research_service import get_backtest_run
        run = get_backtest_run(run_id)
        if not run:
            return jsonify({"success": False, "error": "Run not found"}), 404
        return jsonify({"success": True, "run": run})
    except Exception as e:
        logger.error(f"Error getting backtest run: {e}")
        return jsonify({"success": False, "error": str(e)})


# Parameter sweep / optimizer (Phase 7E — read-only research)
@core_bp.route("/api/optimizer/run", methods=["POST"], endpoint="core_run_optimizer")
def run_optimizer():
    """Run parameter sweep for a strategy; returns all results for visualization."""
    try:
        from services.strategy_optimizer import strategy_optimizer
        data = request.get_json() or {}
        strategy_name = data.get("strategy_name")
        param_ranges = data.get("param_ranges", {})
        optimization_metric = data.get("optimization_metric", "sharpe_ratio")
        start_date_str = data.get("start_date")
        end_date_str = data.get("end_date")

        if not strategy_name or not param_ranges:
            return jsonify({
                "success": False,
                "error": "strategy_name and param_ranges required",
            }), 400

        end_date = datetime.fromisoformat(end_date_str) if end_date_str else datetime.utcnow()
        start_date = (
            datetime.fromisoformat(start_date_str)
            if start_date_str
            else end_date - timedelta(days=90)
        )

        result = strategy_optimizer.optimize_strategy(
            strategy_name,
            param_ranges,
            start_date=start_date,
            end_date=end_date,
            optimization_metric=optimization_metric,
        )
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error running optimizer: {e}")
        return jsonify({"success": False, "error": str(e)})


@core_bp.route("/api/optimizer/history", endpoint="core_get_optimizer_history")
def get_optimizer_history():
    """Get optimization history for parameter sweep visualization (Phase 7E)."""
    try:
        from services.strategy_optimizer import strategy_optimizer
        history = strategy_optimizer.get_optimization_history()
        return jsonify({"success": True, "history": history})
    except Exception as e:
        logger.error(f"Error getting optimizer history: {e}")
        return jsonify({"success": False, "error": str(e)})


# Strategy evaluation (research-only; no live execution impact)
@core_bp.route("/api/evaluation/run", methods=["POST"], endpoint="core_evaluation_run")
def evaluation_run():
    """Run strategy evaluation: metrics, friction, walk-forward, Monte Carlo, overfitting guard. Uses trade data only."""
    try:
        data = request.get_json() or {}
        strategies = data.get("strategies", [])
        start_date = data.get("start_date")
        end_date = data.get("end_date")
        if not strategies:
            return jsonify({"success": False, "error": "Provide at least one strategy name"}), 400
        strategy_trades = {}
        for name in strategies:
            trades_data = data_parser.get_trades(
                strategy=name,
                start_date=start_date,
                end_date=end_date,
                per_page=10000,
            )
            trades = trades_data.get("trades", [])
            strategy_trades[name] = trades
        # Ensure project root on path (evaluation package is research-only, isolated)
        import sys
        from pathlib import Path
        _root = Path(__file__).resolve().parent.parent
        if str(_root) not in sys.path:
            sys.path.insert(0, str(_root))
        from evaluation.evaluator import run_evaluation
        from evaluation.config import EvaluationConfig
        cfg = EvaluationConfig()
        if data.get("monte_carlo_sims"):
            cfg.monte_carlo_simulations = min(int(data["monte_carlo_sims"]), 1000)
        if data.get("oos_sharpe_drop_threshold") is not None:
            cfg.oos_sharpe_drop_threshold = float(data["oos_sharpe_drop_threshold"])
        report = run_evaluation(
            strategy_trades,
            config=cfg,
            initial_capital=10000.0,
            run_walk_forward_flag=True,
            run_monte_carlo_flag=True,
            run_comparison=(len(strategies) > 1),
        )
        return jsonify({"success": True, "report": report.to_dict()})
    except Exception as e:
        logger.error(f"Error running evaluation: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# Research export: CSV/JSON for analytics, comparison, sweep (Phase 7E)
@core_bp.route("/api/research/export", endpoint="core_research_export")
def research_export():
    """Export research data: analytics, backtest comparison, or parameter sweep (CSV/JSON)."""
    try:
        export_type = request.args.get("type", "analytics")
        fmt = request.args.get("format", "csv").lower()
        if fmt not in ("csv", "json"):
            fmt = "csv"

        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")
        volatility_regime = request.args.get("volatility_regime")
        event_window_start = request.args.get("event_window_start")
        event_window_end = request.args.get("event_window_end")

        if export_type == "analytics":
            from services.research_service import filter_trades_by_regime
            trades_data = data_parser.get_trades(
                start_date=start_date, end_date=end_date, per_page=10000
            )
            trades = trades_data.get("trades", [])
            trades = filter_trades_by_regime(
                trades,
                start_date=start_date,
                end_date=end_date,
                volatility_regime=volatility_regime,
                event_window_start=event_window_start,
                event_window_end=event_window_end,
            )
            strategies = strategy_analytics.get_all_strategies_performance_from_trades(
                trades
            )
            if not strategies:
                return jsonify({"error": "No data to export"}), 404
            data = strategies
        elif export_type == "comparison":
            from services.research_service import get_run_ids_for_comparison
            run_ids = request.args.getlist("run_ids") or request.args.get("run_ids", "")
            if isinstance(run_ids, str):
                run_ids = [r.strip() for r in run_ids.split(",") if r.strip()]
            runs = get_run_ids_for_comparison(run_ids)
            data = [
                {
                    "run_id": r.get("run_id"),
                    "strategy": r.get("strategy"),
                    "stored_at": r.get("stored_at"),
                    **r.get("metrics", {}),
                }
                for r in runs
            ]
            if not data:
                return jsonify({"error": "No comparison data; provide run_ids"}), 404
        elif export_type == "sweep":
            from services.strategy_optimizer import strategy_optimizer
            history = strategy_optimizer.get_optimization_history()
            data = []
            for h in history:
                opt_metrics = h.get("optimal_metrics") or {}
                data.append({
                    "strategy_name": h.get("strategy_name"),
                    "timestamp": h.get("timestamp"),
                    "optimization_metric": h.get("optimization_metric"),
                    "combinations_tested": h.get("combinations_tested"),
                    "optimal_parameters": json.dumps(h.get("optimal_parameters") or {}),
                    "optimal_return_pct": opt_metrics.get("return_pct"),
                    "optimal_sharpe_ratio": opt_metrics.get("sharpe_ratio"),
                    "optimal_win_rate": opt_metrics.get("win_rate"),
                })
            if not data:
                return jsonify({"error": "No sweep data; run optimizer first"}), 404
        else:
            return jsonify({"error": "type must be analytics|comparison|sweep"}), 400

        if fmt == "json":
            filename = f"research_{export_type}_{datetime.utcnow().strftime('%Y%m%d_%H%M')}.json"
            return Response(
                json.dumps({"data": data}, indent=2),
                mimetype="application/json",
                headers={"Content-Disposition": f"attachment; filename={filename}"},
            )
        output = io.StringIO()
        if data:
            writer = csv.DictWriter(output, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        filename = f"research_{export_type}_{datetime.utcnow().strftime('%Y%m%d_%H%M')}.csv"
        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except Exception as e:
        logger.error(f"Error exporting research: {e}")
        return jsonify({"error": str(e)}), 500


# ============================================================================
# UPDATE SYSTEM API ENDPOINTS
# ============================================================================


@system_bp.route("/api/update/check", methods=["GET"], endpoint="system_check_for_updates")
def check_for_updates():
    """Check if updates are available"""
    try:
        update_info = version_manager.check_for_updates()
        return jsonify(update_info)
    except Exception as e:
        logger.error(f"Error checking for updates: {e}")
        return jsonify({"error": str(e)}), 500


@system_bp.route("/api/update/history", methods=["GET"], endpoint="system_get_update_history")
def get_update_history():
    """Get past updates"""
    try:
        history = version_manager.get_update_history()
        return jsonify({"history": history})
    except Exception as e:
        logger.error(f"Error getting update history: {e}")
        return jsonify({"error": str(e)}), 500


@system_bp.route("/api/update/start", methods=["POST"], endpoint="system_start_update")
def start_update():
    """Start update process"""
    try:
        # Run pre-flight checks
        checks_passed, checks = update_service.pre_flight_checks()

        if not checks_passed:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Pre-flight checks failed",
                        "checks": checks,
                    }
                ),
                400,
            )

        # Generate update ID
        import uuid

        update_id = str(uuid.uuid4())

        # Start update in background thread
        import threading

        def run_update():
            result = update_service.perform_update()
            logger.log_info(f"Update completed: {result}")

        thread = threading.Thread(target=run_update, daemon=True)
        thread.start()

        return jsonify(
            {
                "status": "started",
                "update_id": update_service.current_update_id or update_id,
                "message": "Update started successfully",
            }
        )

    except Exception as e:
        logger.error(f"Error starting update: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@system_bp.route("/api/update/progress", methods=["GET"], endpoint="system_get_update_progress")
def get_update_progress():
    """Get real-time update progress"""
    try:
        progress = update_service.get_progress()
        if progress is None:
            return jsonify(
                {
                    "status": "idle",
                    "progress": 0,
                    "message": "No update in progress",
                    "logs": [],
                }
            )
        return jsonify(progress)
    except Exception as e:
        logger.error(f"Error getting update progress: {e}")
        return jsonify({"error": str(e)}), 500


@system_bp.route("/api/update/cancel", methods=["POST"], endpoint="system_cancel_update")
def cancel_update():
    """Cancel in-progress update"""
    try:
        # For now, just unlock - actual cancellation is complex
        success = update_service.unlock_update(force=True)

        if success:
            return jsonify(
                {"success": True, "message": "Update cancelled, lock removed"}
            )
        else:
            return jsonify({"success": False, "error": "Failed to cancel update"}), 500

    except Exception as e:
        logger.error(f"Error cancelling update: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@system_bp.route("/api/update/rollback", methods=["POST"], endpoint="system_manual_rollback")
def manual_rollback():
    """Manual rollback to previous version"""
    try:
        data = request.get_json() or {}
        backup_name = data.get("backup_name")

        success = update_service.rollback(backup_name)

        if success:
            return jsonify(
                {
                    "success": True,
                    "message": f"Rolled back to {backup_name or 'latest backup'}",
                }
            )
        else:
            return jsonify({"success": False, "error": "Rollback failed"}), 500

    except Exception as e:
        logger.error(f"Error during rollback: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================================
# SYSTEM HEALTH & RECOVERY API ENDPOINTS
# ============================================================================


@system_bp.route("/api/system/health", methods=["GET"], endpoint="system_get_system_health")
def get_system_health():
    """System health check"""
    try:
        # Run pre-flight checks (they're comprehensive)
        checks_passed, checks = update_service.pre_flight_checks()

        # Additional checks
        bot_running = process_manager.is_bot_running()
        dashboard_running = process_manager.is_dashboard_running()

        # Get disk space
        stat = shutil.disk_usage(BASE_DIR)
        free_gb = stat.free / (1024**3)

        # Count backups
        backups_dir = BASE_DIR / "backups"
        backup_count = (
            len([d for d in backups_dir.iterdir() if d.is_dir()])
            if backups_dir.exists()
            else 0
        )

        # Get last update
        history = version_manager.get_update_history()
        last_update = history[0] if history else None

        return jsonify(
            {
                "status": "healthy" if checks_passed else "warning",
                "bot_running": bot_running,
                "dashboard_running": dashboard_running,
                "disk_space_gb": round(free_gb, 1),
                "backup_count": backup_count,
                "last_update": last_update,
                "checks": checks,
            }
        )

    except Exception as e:
        logger.error(f"Error getting system health: {e}")
        return jsonify({"error": str(e)}), 500


@system_bp.route("/api/backups/list", methods=["GET"], endpoint="system_list_backups")
def list_backups():
    """List all backups"""
    try:
        backups_dir = BASE_DIR / "backups"

        if not backups_dir.exists():
            return jsonify({"backups": []})

        backups = []
        for backup_dir in backups_dir.iterdir():
            if backup_dir.is_dir():
                # Get backup info
                stat = backup_dir.stat()
                size_mb = sum(
                    f.stat().st_size for f in backup_dir.rglob("*") if f.is_file()
                ) / (1024 * 1024)

                # Try to read version from backup
                version_file = backup_dir / "VERSION"
                version = (
                    version_file.read_text().strip()
                    if version_file.exists()
                    else "unknown"
                )

                backups.append(
                    {
                        "name": backup_dir.name,
                        "date": datetime.fromtimestamp(
                            stat.st_mtime, tz=timezone.utc
                        ).isoformat(),
                        "version": version,
                        "size_mb": round(size_mb, 1),
                    }
                )

        # Sort by date, most recent first
        backups.sort(key=lambda x: x["date"], reverse=True)

        return jsonify({"backups": backups})

    except Exception as e:
        logger.error(f"Error listing backups: {e}")
        return jsonify({"error": str(e)}), 500


@system_bp.route("/api/backups/restore", methods=["POST"], endpoint="system_restore_backup")
def restore_backup():
    """Restore specific backup"""
    try:
        data = request.get_json()
        backup_id = data.get("backup_id")

        if not backup_id:
            return jsonify({"success": False, "error": "backup_id required"}), 400

        success = update_service.rollback(backup_id)

        if success:
            return jsonify(
                {"success": True, "message": f"Restored backup: {backup_id}"}
            )
        else:
            return jsonify({"success": False, "error": "Restore failed"}), 500

    except Exception as e:
        logger.error(f"Error restoring backup: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@system_bp.route("/api/system/force-stop", methods=["POST"], endpoint="system_force_stop_all")
def force_stop_all():
    """Emergency stop all processes"""
    try:
        success = process_manager.force_stop_all()

        if success:
            return jsonify({"success": True, "message": "All processes stopped"})
        else:
            return jsonify({"success": False, "error": "Force stop failed"}), 500

    except Exception as e:
        logger.error(f"Error force stopping: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@system_bp.route("/api/system/unlock-update", methods=["POST"], endpoint="system_unlock_update_system")
def unlock_update_system():
    """Clear stuck update locks"""
    try:
        data = request.get_json() or {}
        force = data.get("force", False)

        success = update_service.unlock_update(force=force)

        if success:
            return jsonify({"success": True, "message": "Update system unlocked"})
        else:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Failed to unlock (update may be in progress)",
                    }
                ),
                400,
            )

    except Exception as e:
        logger.error(f"Error unlocking update: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# ===== Integration & Connectivity Routes =====
# Added as part of PR to connect frontend/backend components


@core_bp.route("/api/chart/pnl", endpoint="core_get_pnl_chart_data")
def get_pnl_chart_data():
    """Return P&L data formatted for Chart.js"""
    try:
        pnl_data = chart_data.get_pnl_over_time()
        return jsonify(pnl_data)
    except Exception as e:
        logger.error(f"Error getting P&L chart data: {e}")
        return jsonify({"labels": [], "values": [], "error": str(e)}), 500


# Phase 7C: POST /api/keys removed (no set_api_key on SecureConfigManager). Writes: POST /api/settings/data-sources only.


@core_bp.route("/api/keys", methods=["GET"], endpoint="core_get_api_keys")
def get_api_keys():
    """Read-only proxy to canonical credential list (SecureConfigManager). Never exposes secrets."""
    try:
        from services.secure_config_manager import SecureConfigManager

        config = SecureConfigManager()
        services = config.list_services() if hasattr(config, "list_services") else []
        keys = []
        for svc in services:
            masked = config.get_masked_credentials(svc) if hasattr(config, "get_masked_credentials") else {}
            keys.append({"service": svc, "masked": masked})
        return jsonify(keys)
    except Exception as e:
        logger.error(f"Error getting API keys: {e}")
        return jsonify({"error": str(e)}), 500


# Phase 6B: Which strategies/integrations rely on which keys (for UI dependency visibility)
API_KEY_DEPENDENCIES = {
    "binance": ["crypto_momentum", "mean_reversion", "volatility_breakout", "data_sources.crypto_prices"],
    "polymarket": ["polymarket_arbitrage", "arbitrage_executor", "data_sources.polymarket"],
    "coinbase": ["data_sources.crypto_prices"],
    "kraken": ["data_sources.crypto_prices"],
    "coingecko": ["crypto_momentum", "data_sources.crypto_prices"],
    "telegram": ["notifications.telegram"],
    "email": ["notifications.email"],
}


@core_bp.route("/api/keys/dependencies", endpoint="core_get_key_dependencies")
def get_key_dependencies():
    """Return which strategies/integrations use which API keys. Read-only."""
    return jsonify({"dependencies": API_KEY_DEPENDENCIES})


@core_bp.route("/api/leaderboard", endpoint="core_get_leaderboard_data")
def get_leaderboard_data():
    """Get strategy comparison data"""
    try:
        from services.strategy_competition import StrategyCompetition

        monitor = StrategyCompetition()
        leaderboard = monitor.get_leaderboard()
        return jsonify(leaderboard)
    except Exception as e:
        logger.error(f"Error getting leaderboard data: {e}")
        # Return empty leaderboard on error
        return jsonify({"strategies": [], "error": str(e)}), 500


@core_bp.route("/api/trades/<trade_id>", endpoint="core_get_trade_details")
def get_trade_details(trade_id):
    """Get detailed trade information"""
    try:
        trade = data_parser.get_trade_by_id(trade_id)
        if trade:
            return jsonify(trade)
        else:
            return jsonify({"error": "Trade not found"}), 404
    except Exception as e:
        logger.error(f"Error getting trade details: {e}")
        return jsonify({"error": str(e)}), 500


@core_bp.route("/api/reports/tax", endpoint="core_download_tax_report")
def download_tax_report():
    """Generate and download tax report CSV"""
    try:
        from services.tax_reporter import TaxReporter

        generator = TaxReporter()
        report_data = generator.generate_report()

        # Create CSV
        si = io.StringIO()
        writer = csv.writer(si)
        writer.writerow(["Date", "Type", "Amount", "Symbol", "Realized P&L"])

        for trade in report_data:
            writer.writerow(
                [
                    trade.get("date", ""),
                    trade.get("type", ""),
                    trade.get("amount", ""),
                    trade.get("symbol", ""),
                    trade.get("realized_pnl", ""),
                ]
            )

        output = make_response(si.getvalue())
        output.headers["Content-Disposition"] = "attachment; filename=tax_report.csv"
        output.headers["Content-type"] = "text/csv"
        return output
    except Exception as e:
        logger.error(f"Error generating tax report: {e}")
        return jsonify({"error": str(e)}), 500


@core_bp.route("/api/dashboard/refresh", endpoint="core_refresh_dashboard_data")
def refresh_dashboard_data():
    """Get latest dashboard data for auto-refresh. Prefers engine state."""
    try:
        # Prefer engine state when available
        engine_overview = engine_state_reader.get_overview_from_engine()
        if engine_overview is not None:
            summary = {**DEFAULT_OVERVIEW_STATS, **engine_overview}
            activities = engine_state_reader.get_activity()[:10]
            return jsonify(
                {
                    "summary": summary,
                    "recent_trades": [],
                    "recent_activity": activities,
                    "pnl_chart": [],
                    "last_updated": engine_overview.get("last_update", datetime.now(timezone.utc).isoformat()),
                    "source": "engine",
                }
            )

        # Fallback to analytics
        summary = analytics.get_overview_stats()
        trades_response = data_parser.get_trades(page=1, per_page=10)
        recent_trades = (
            trades_response.get("trades", [])
            if isinstance(trades_response, dict)
            else []
        )
        pnl_chart = chart_data.get_pnl_over_time()
        return jsonify(
            {
                "summary": summary,
                "recent_trades": recent_trades,
                "pnl_chart": pnl_chart,
                "last_updated": datetime.now(timezone.utc).isoformat(),
            }
        )
    except Exception as e:
        logger.error(f"Error refreshing dashboard data: {e}")
        return jsonify({"error": str(e)}), 500


@core_bp.route("/api/metrics/realized-gains", endpoint="core_get_realized_gains")
def get_realized_gains():
    """Calculate actual realized gains"""
    try:
        trades_response = data_parser.get_trades(page=1, per_page=10000)
        trade_list = (
            trades_response.get("trades", [])
            if isinstance(trades_response, dict)
            else []
        )

        realized_gains = sum(
            [
                trade.get("profit", 0)
                for trade in trade_list
                if trade.get("status") == "closed" and trade.get("profit") is not None
            ]
        )

        closed_count = len([t for t in trade_list if t.get("status") == "closed"])

        return jsonify({"realized_gains": realized_gains, "trade_count": closed_count})
    except Exception as e:
        logger.error(f"Error calculating realized gains: {e}")
        return jsonify({"error": str(e)}), 500


@core_bp.route("/api/settings/trading-mode", methods=["GET"], endpoint="core_get_trading_mode")
def get_trading_mode():
    """Get current trading mode. Paper is default. Read-only."""
    try:
        config_file = BASE_DIR / "config.yaml"
        config = {}
        if config_file.exists():
            with open(config_file, "r") as f:
                config = yaml.safe_load(f) or {}
        paper = config.get("paper_trading", True)
        mode = "paper" if paper else "live"
        return jsonify({
            "mode": mode,
            "paper_trading": paper,
            "requires_restart": True,
            "warning": None if paper else "Live trading is enabled. Real money may be at risk.",
        })
    except Exception as e:
        logger.error(f"Error getting trading mode: {e}")
        return jsonify({"mode": "paper", "paper_trading": True, "error": str(e)}), 200


@core_bp.route("/api/settings/set-trading-mode", methods=["POST"], endpoint="core_set_trading_mode")
def set_trading_mode():
    """Set trading mode. Live requires explicit confirmation (confirm_phrase='LIVE')."""
    try:
        data = request.get_json() or {}
        want = (data.get("mode") or "paper").strip().lower()
        confirm_phrase = (data.get("confirm_phrase") or "").strip().upper()
        config_file = BASE_DIR / "config.yaml"

        if want not in ("paper", "live"):
            return jsonify({"success": False, "error": "mode must be 'paper' or 'live'"}), 400

        if want == "live":
            if confirm_phrase != "LIVE":
                return jsonify({
                    "success": False,
                    "error": "To enable live trading you must set confirm_phrase to 'LIVE'.",
                    "requires_confirm": True,
                }), 400
            # Backend may not support live execution; we only flip config here
            # UI should show: "Changing to live requires engine restart. No real execution until backend supports it."

        config = {}
        if config_file.exists():
            with open(config_file, "r") as f:
                config = yaml.safe_load(f) or {}
        config["paper_trading"] = want == "paper"
        with open(config_file, "w") as f:
            yaml.dump(config, f, default_flow_style=False)

        return jsonify({
            "success": True,
            "mode": want,
            "requires_restart": True,
            "message": "Restart the engine (run_bot.py) for the change to take effect.",
        })
    except Exception as e:
        logger.error(f"Error setting trading mode: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# Phase 7C: Legacy toggle removed. Use GET /api/settings/trading-mode and POST /api/settings/set-trading-mode (with confirm_phrase for live) only.


# ============================================================================
# NEW API ENDPOINTS FOR PR #50: Strategy Execution Engine
# ============================================================================


@core_bp.route("/api/chart/allocation", endpoint="core_get_allocation_chart")
def get_allocation_chart():
    """Portfolio allocation pie chart"""
    try:
        # Read-only dashboard view.
        # ExecutionEngine is the source of truth when available.
        data_flow = DataFlowManager()
        positions = data_flow.portfolio_tracker.get_positions()

        return jsonify(
            {
                "labels": [p["symbol"] for p in positions],
                "data": [p["value"] for p in positions],
            }
        )
    except Exception as e:
        logger.error(f"Error getting allocation chart: {e}")
        return jsonify({"labels": [], "data": []}), 200


@core_bp.route("/api/chart/distribution", endpoint="core_get_distribution_chart")
def get_distribution_chart():
    """Trade win/loss distribution. Phase 7B: Single source logs/trades.csv via data_parser."""
    try:
        trades = data_parser.get_all_trades() or []
        pnl_key = "pnl_usd" if trades and "pnl_usd" in trades[0] else "pnl"
        wins = len([t for t in trades[-1000:] if float(t.get(pnl_key, 0) or 0) > 0])
        losses = min(len(trades), 1000) - wins

        return jsonify({"labels": ["Wins", "Losses"], "data": [wins, losses]})
    except Exception as e:
        logger.error(f"Error getting distribution chart: {e}")
        return jsonify({"labels": ["Wins", "Losses"], "data": [0, 0]}), 200


@core_bp.route("/api/chart/cumulative", endpoint="core_get_cumulative_chart")
def get_cumulative_chart():
    """Cumulative returns over time. Phase 7B: Single source logs/trades.csv via data_parser."""
    try:
        trades = data_parser.get_all_trades() or []
        pnl_key = "pnl_usd" if trades and "pnl_usd" in trades[0] else "pnl"
        cumulative = []
        total = 0.0
        for trade in trades:
            total += float(trade.get(pnl_key, 0) or 0)
            cumulative.append(
                {
                    "date": trade.get(
                        "timestamp", datetime.now(timezone.utc).isoformat()
                    ),
                    "value": total,
                }
            )

        return jsonify(cumulative)
    except Exception as e:
        logger.error(f"Error getting cumulative chart: {e}")
        return jsonify([]), 200


@journal_bp.route("/api/journal/entry", methods=["POST"], endpoint="journal_save_journal_entry")
def save_journal_entry_file():
    """Save trade journal entry (file-based)"""
    try:
        data = request.json

        # Save to journal file
        journal_file = Path("data/trade_journal.json")
        journal_file.parent.mkdir(exist_ok=True)

        # Load existing entries
        entries = []
        if journal_file.exists():
            with open(journal_file, "r") as f:
                try:
                    entries = json.load(f)
                except json.JSONDecodeError:
                    entries = []

        # Add timestamp
        data["timestamp"] = datetime.now(timezone.utc).isoformat()
        entries.append(data)

        # Save
        with open(journal_file, "w") as f:
            json.dump(entries, f, indent=2)

        return jsonify({"success": True})
    except Exception as e:
        logger.error(f"Error saving journal entry: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@journal_bp.route("/api/journal/entries", endpoint="journal_get_journal_entries")
def get_journal_entries():
    """Get all journal entries"""
    try:
        journal_file = Path("data/trade_journal.json")

        if journal_file.exists():
            with open(journal_file, "r") as f:
                try:
                    entries = json.load(f)
                    return jsonify(entries)
                except json.JSONDecodeError:
                    return jsonify([])

        return jsonify([])
    except Exception as e:
        logger.error(f"Error getting journal entries: {e}")
        return jsonify([]), 200


# ============================================================================
# Phase 8: Strategy Intelligence API (read-only, no auto-apply)
# ============================================================================


@core_bp.route("/api/intelligence/diagnostics", endpoint="core_api_intelligence_diagnostics")
def api_intelligence_diagnostics():
    """Get diagnostics (cached or run now). Read-only."""
    try:
        strategy = request.args.get("strategy")
        if request.args.get("refresh"):
            strategy_intelligence_run(data_parser, strategy_name=strategy or None)
        diag = get_cached_diagnostics()
        if not diag and not request.args.get("refresh"):
            strategy_intelligence_run(data_parser, strategy_name=strategy or None)
            diag = get_cached_diagnostics()
        return jsonify(diag if diag else {"sample_size": 0, "message": "No trade data"})
    except Exception as e:
        logger.error(f"Strategy intelligence diagnostics: {e}", exc_info=True)
        return jsonify({"error": str(e), "sample_size": 0}), 200


@core_bp.route("/api/intelligence/suggestions", endpoint="core_api_intelligence_suggestions")
def api_intelligence_suggestions():
    """Get ranked suggestions (cached or run now). Read-only. No apply."""
    try:
        strategy = request.args.get("strategy")
        if request.args.get("refresh"):
            strategy_intelligence_run(data_parser, strategy_name=strategy or None)
        suggestions = get_cached_suggestions()
        if not suggestions and request.args.get("refresh") is None:
            strategy_intelligence_run(data_parser, strategy_name=strategy or None)
            suggestions = get_cached_suggestions()
        return jsonify({
            "suggestions": suggestions,
            "generated_at": strategy_intelligence_last_run_at(),
            "disclaimer": "Suggestion only. No automatic changes.",
        })
    except Exception as e:
        logger.error(f"Strategy intelligence suggestions: {e}", exc_info=True)
        return jsonify({"suggestions": [], "error": str(e)}), 200


@core_bp.route("/api/intelligence/run", methods=["POST", "GET"], endpoint="core_api_intelligence_run")
def api_intelligence_run():
    """Trigger analysis run (batch). Read-only; no strategy/config changes."""
    try:
        data = request.get_json(silent=True) or {}
        strategy_name = data.get("strategy") or request.args.get("strategy")
        result = strategy_intelligence_run(data_parser, strategy_name=strategy_name or None)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Strategy intelligence run: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 200


@core_bp.route("/api/intelligence/export", endpoint="core_api_intelligence_export")
def api_intelligence_export():
    """Export last diagnostics + suggestions as JSON. Read-only download."""
    try:
        diag = get_cached_diagnostics()
        suggestions = get_cached_suggestions()
        path = export_to_reports_dir(BASE_DIR, diag, suggestions)
        if path and path.exists():
            return send_file(
                path,
                mimetype="application/json",
                as_attachment=True,
                download_name=path.name,
            )
        payload = {
            "generated_at": strategy_intelligence_last_run_at(),
            "diagnostics": diag,
            "suggestions": suggestions,
            "disclaimer": "Read-only. No automatic changes.",
        }
        return jsonify(payload)
    except Exception as e:
        logger.error(f"Strategy intelligence export: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 200


@core_bp.route("/intelligence", endpoint="core_page_intelligence")
def page_intelligence():
    """Strategy Intelligence page (Phase 8E). Suggestion only; no apply buttons."""
    return render_template("strategy_intelligence.html")


@core_bp.route("/api/export/trades", endpoint="core_export_trades_csv")
def export_trades_csv():
    """Export trades to CSV. Uses data_parser (bounded last N) when available."""
    try:
        trades = data_parser.get_all_trades() or []
        if trades:
            si = io.StringIO()
            w = csv.writer(si)
            w.writerow(
                [
                    "timestamp",
                    "market",
                    "yes_price",
                    "no_price",
                    "sum",
                    "profit_pct",
                    "profit_usd",
                    "status",
                    "strategy",
                    "arbitrage_type",
                ]
            )
            for t in trades:
                ts = t.get("timestamp") or t.get("entry_time") or ""
                sym = t.get("symbol") or ""
                ep = float(t.get("entry_price") or 0)
                xp = float(t.get("exit_price") or 0)
                w.writerow(
                    [
                        ts,
                        sym,
                        f"{ep:.3f}",
                        f"{xp:.3f}",
                        f"{ep + xp:.3f}",
                        f"{float(t.get('pnl_pct') or 0):.1f}",
                        f"{float(t.get('pnl_usd') or 0):.2f}",
                        t.get("status", "closed"),
                        t.get("strategy", "Unknown"),
                        t.get("arbitrage_type", "Unknown"),
                    ]
                )
            csv_data = si.getvalue()
        else:
            trades_file = LOGS_DIR / "trades.csv"
            if trades_file.exists():
                csv_data = trades_file.read_text(encoding="utf-8")
            else:
                csv_data = (
                    "timestamp,market,yes_price,no_price,sum,profit_pct,profit_usd,status,strategy,arbitrage_type\n"
                )
        return Response(
            csv_data,
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment;filename=trades.csv"},
        )
    except Exception as e:
        logger.error(f"Error exporting trades: {e}")
        return jsonify({"error": str(e)}), 500


@core_bp.route("/api/export/portfolio", endpoint="core_export_portfolio_csv")
def export_portfolio_csv():
    """Export portfolio to CSV"""
    try:
        # Read-only dashboard view.
        # ExecutionEngine is the source of truth when available.
        data_flow = DataFlowManager()
        positions = data_flow.portfolio_tracker.get_positions()

        # Create CSV
        si = io.StringIO()
        writer = csv.DictWriter(
            si,
            fieldnames=[
                "symbol",
                "quantity",
                "avg_price",
                "current_price",
                "value",
                "pnl",
                "pnl_pct",
            ],
        )
        writer.writeheader()
        writer.writerows(positions)

        return Response(
            si.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment;filename=portfolio.csv"},
        )
    except Exception as e:
        logger.error(f"Error exporting portfolio: {e}")
        return jsonify({"error": str(e)}), 500


@core_bp.route("/api/notifications/send", methods=["POST"], endpoint="core_send_notification")
def send_notification():
    """Send notification (email/telegram)"""
    try:
        data = request.json
        message = data.get("message", "")
        notification_type = data.get("type", "info")

        # Use existing notification service
        notification_service.send_alert(
            title=data.get("title", "Bot Notification"),
            message=message,
            priority=notification_type,
        )

        return jsonify({"success": True})
    except Exception as e:
        logger.error(f"Error sending notification: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@core_bp.route("/api/market/live", endpoint="core_get_live_market_data")
def get_live_market_data():
    """Live market data stream"""
    try:
        # Get market data from clients
        from clients import get_market_client

        try:
            client = get_market_client()
            markets = client.get_markets(limit=20)

            return jsonify(
                {
                    "markets": markets,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "source": "live" if hasattr(client, "api_key") else "mock",
                }
            )
        except Exception as e:
            logger.error(f"Error fetching market data: {e}")
            return (
                jsonify(
                    {
                        "markets": [],
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "source": "mock",
                        "error": str(e),
                    }
                ),
                200,
            )
    except Exception as e:
        logger.error(f"Error in live market data endpoint: {e}")
        return jsonify({"error": str(e)}), 500


@core_bp.route("/api/portfolio", endpoint="core_get_portfolio_api")
def get_portfolio_api():
    """Get current portfolio summary"""
    try:
        # Read-only dashboard view.
        # ExecutionEngine is the source of truth when available.
        data_flow = DataFlowManager()
        summary = data_flow.get_portfolio_summary()
        positions = data_flow.portfolio_tracker.get_positions()

        return jsonify(
            {
                "summary": summary,
                "positions": positions,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
    except Exception as e:
        logger.error(f"Error getting portfolio: {e}")
        return jsonify({"error": str(e)}), 500


@strategies_bp.route("/api/strategies/performance", endpoint="strategies_get_strategies_performance")
def get_strategies_performance():
    """Get performance data for all strategies. Phase 7B: Single source logs/trades.csv."""
    try:
        all_trades = data_parser.get_all_trades() or []
        strategy_names = set(t.get("strategy", "unknown") for t in all_trades)

        strategies = []
        for name in strategy_names:
            strat_trades = [t for t in all_trades if t.get("strategy") == name]
            pnl_key = "pnl_usd" if strat_trades and "pnl_usd" in strat_trades[0] else "pnl"
            total_pnl = sum(float(t.get(pnl_key, 0) or 0) for t in strat_trades)
            wins = len([t for t in strat_trades if float(t.get(pnl_key, 0) or 0) > 0])
            stats = {
                "total_trades": len(strat_trades),
                "total_pnl": total_pnl,
                "win_rate": (wins / len(strat_trades) * 100) if strat_trades else 0,
                "avg_pnl": (total_pnl / len(strat_trades)) if strat_trades else 0,
            }
            strategies.append(
                {
                    "name": name,
                    "total_trades": stats.get("total_trades", 0),
                    "total_pnl": stats.get("total_pnl", 0),
                    "win_rate": stats.get("win_rate", 0),
                    "avg_pnl": stats.get("avg_pnl", 0),
                }
            )

        return jsonify({"strategies": strategies})
    except Exception as e:
        logger.error(f"Error getting strategy performance: {e}")
        return jsonify({"strategies": []}), 200


# ============================================================================
# ALERT SYSTEM API ENDPOINTS
# ============================================================================


@core_bp.route("/api/alerts/config", methods=["GET"], endpoint="core_get_alerts_config")
def get_alerts():
    """Get all configured alerts"""
    try:
        from services.alert_system import get_alert_system

        alert_system = get_alert_system(config_loader._config if config_loader else {})
        alerts = alert_system.get_all_alerts()
        return jsonify({"alerts": alerts})
    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        return jsonify({"error": str(e)}), 500


@core_bp.route("/api/alerts/config", methods=["POST"], endpoint="core_create_alert_config")
def create_alert():
    """Create a new alert"""
    try:
        from services.alert_system import get_alert_system

        alert_system = get_alert_system(config_loader._config if config_loader else {})

        data = request.get_json()
        alert = alert_system.create_alert(
            alert_type=data.get("type"),
            name=data.get("name"),
            condition=data.get("condition"),
            value=float(data.get("value", 0)),
            enabled=data.get("enabled", True),
            notification_channels=data.get("notification_channels"),
            metadata=data.get("metadata", {}),
        )

        return jsonify({"success": True, "alert": alert})
    except Exception as e:
        logger.error(f"Error creating alert: {e}")
        return jsonify({"error": str(e)}), 500


@core_bp.route("/api/alerts/config/<alert_id>", methods=["PUT"], endpoint="core_update_alert")
def update_alert(alert_id):
    """Update an alert"""
    try:
        from services.alert_system import get_alert_system

        alert_system = get_alert_system(config_loader._config if config_loader else {})

        data = request.get_json()
        alert = alert_system.update_alert(alert_id, data)

        if alert:
            return jsonify({"success": True, "alert": alert})
        else:
            return jsonify({"error": "Alert not found"}), 404
    except Exception as e:
        logger.error(f"Error updating alert: {e}")
        return jsonify({"error": str(e)}), 500


@core_bp.route("/api/alerts/config/<alert_id>", methods=["DELETE"], endpoint="core_delete_alert_config")
def delete_alert(alert_id):
    """Delete an alert"""
    try:
        from services.alert_system import get_alert_system

        alert_system = get_alert_system(config_loader._config if config_loader else {})

        success = alert_system.delete_alert(alert_id)

        if success:
            return jsonify({"success": True})
        else:
            return jsonify({"error": "Alert not found"}), 404
    except Exception as e:
        logger.error(f"Error deleting alert: {e}")
        return jsonify({"error": str(e)}), 500


@core_bp.route("/api/alerts/test", methods=["POST"], endpoint="core_test_alert")
def test_alert():
    """Test an alert configuration"""
    try:
        from services.alert_system import get_alert_system

        alert_system = get_alert_system(config_loader._config if config_loader else {})

        data = request.get_json()
        result = alert_system.test_alert(data)

        return jsonify(result)
    except Exception as e:
        logger.error(f"Error testing alert: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================================
# SETTINGS MANAGEMENT API ENDPOINTS
# ============================================================================


@core_bp.route("/api/settings/config", methods=["GET"], endpoint="core_get_config_settings")
def get_config_settings():
    """Get current configuration settings"""
    try:
        from services.settings_manager import get_settings_manager

        settings_mgr = get_settings_manager()
        settings = settings_mgr.load_settings()
        return jsonify({"settings": settings})
    except Exception as e:
        logger.error(f"Error getting settings: {e}")
        return jsonify({"error": str(e)}), 500


@core_bp.route("/api/settings/config", methods=["POST"], endpoint="core_update_config_settings")
def update_config_settings():
    """Update configuration settings"""
    try:
        from services.settings_manager import get_settings_manager

        settings_mgr = get_settings_manager()

        data = request.get_json()
        success = settings_mgr.update_settings(data)

        if success:
            return jsonify(
                {"success": True, "message": "Settings updated successfully"}
            )
        else:
            return jsonify({"error": "Failed to update settings"}), 500
    except Exception as e:
        logger.error(f"Error updating settings: {e}")
        return jsonify({"error": str(e)}), 500


@core_bp.route("/api/settings/reset", methods=["POST"], endpoint="core_reset_settings_mgr")
def reset_settings():
    """Reset settings to defaults"""
    try:
        from services.settings_manager import get_settings_manager

        settings_mgr = get_settings_manager()

        success = settings_mgr.reset_to_defaults()

        if success:
            return jsonify({"success": True, "message": "Settings reset to defaults"})
        else:
            return jsonify({"error": "Failed to reset settings"}), 500
    except Exception as e:
        logger.error(f"Error resetting settings: {e}")
        return jsonify({"error": str(e)}), 500


@core_bp.route("/api/settings/export", methods=["POST"], endpoint="core_export_settings_mgr")
def export_settings_mgr():
    """Export settings to file"""
    try:
        from services.settings_manager import get_settings_manager

        settings_mgr = get_settings_manager()

        export_path = settings_mgr.export_settings()

        if export_path:
            return jsonify({"success": True, "path": export_path})
        else:
            return jsonify({"error": "Failed to export settings"}), 500
    except Exception as e:
        logger.error(f"Error exporting settings: {e}")
        return jsonify({"error": str(e)}), 500


@settings_bp.route("/api/settings/import", methods=["POST"], endpoint="settings_import_settings_from_path")
def import_settings_from_path():
    """Import settings from file"""
    try:
        from services.settings_manager import get_settings_manager

        settings_mgr = get_settings_manager()

        data = request.get_json()
        import_path = data.get("path")

        if not import_path:
            return jsonify({"error": "Import path required"}), 400

        success = settings_mgr.import_settings(import_path)

        if success:
            return jsonify(
                {"success": True, "message": "Settings imported successfully"}
            )
        else:
            return jsonify({"error": "Failed to import settings"}), 500
    except Exception as e:
        logger.error(f"Error importing settings: {e}")
        return jsonify({"error": str(e)}), 500


# Phase 7C: Canonical test is POST /api/settings/test-connection (data_sources_api). No duplicate /api/keys/test here.


# ============================================================================
# PERFORMANCE METRICS API ENDPOINTS
# ============================================================================


@core_bp.route("/api/analytics/performance", methods=["GET"], endpoint="core_get_performance_metrics")
def get_performance_metrics():
    """Get calculated performance metrics. Phase 7B: Single source logs/trades.csv."""
    try:
        from services.performance_calculator import get_performance_calculator

        trades = data_parser.get_all_trades() or []
        calculator = get_performance_calculator()
        metrics = calculator.calculate_all_metrics(trades)

        return jsonify({"metrics": metrics})
    except Exception as e:
        logger.error(f"Error calculating performance metrics: {e}")
        return jsonify({"error": str(e)}), 500


# ============================================================================
# TAX REPORT API ENDPOINTS
# ============================================================================


@core_bp.route("/api/tax-report/irs-8949", methods=["GET"], endpoint="core_get_irs_8949_report")
def get_irs_8949_report():
    """Generate IRS Form 8949 CSV report. Phase 7B: Single source logs/trades.csv."""
    try:
        from services.tax_report_generator import get_tax_report_generator

        trades = data_parser.get_all_trades() or []
        closed_trades = [t for t in trades if t.get("exit_price") or t.get("closed_at") or t.get("status") == "filled"]

        # Generate report
        generator = get_tax_report_generator()
        csv_data = generator.generate_irs_8949_csv(closed_trades)

        # Create response
        response = Response(csv_data, mimetype="text/csv")
        response.headers["Content-Disposition"] = (
            f"attachment; filename=irs_8949_{datetime.now().year}.csv"
        )

        return response
    except Exception as e:
        logger.error(f"Error generating IRS 8949 report: {e}")
        return jsonify({"error": str(e)}), 500


@core_bp.route("/api/tax-report/turbotax", methods=["GET"], endpoint="core_get_turbotax_report")
def get_turbotax_report():
    """Generate TurboTax import CSV report. Phase 7B: Single source logs/trades.csv."""
    try:
        from services.tax_report_generator import get_tax_report_generator

        trades = data_parser.get_all_trades() or []
        closed_trades = [t for t in trades if t.get("exit_price") or t.get("closed_at") or t.get("status") == "filled"]

        # Generate report
        generator = get_tax_report_generator()
        csv_data = generator.generate_turbotax_csv(closed_trades)

        # Create response
        response = Response(csv_data, mimetype="text/csv")
        response.headers["Content-Disposition"] = (
            f"attachment; filename=turbotax_{datetime.now().year}.csv"
        )

        return response
    except Exception as e:
        logger.error(f"Error generating TurboTax report: {e}")
        return jsonify({"error": str(e)}), 500


@core_bp.route("/api/tax-report/summary", methods=["GET"], endpoint="core_get_tax_report_summary")
def get_tax_summary():
    """Get tax summary with short/long-term gains. Phase 7B: Single source logs/trades.csv."""
    try:
        from services.tax_report_generator import get_tax_report_generator

        trades = data_parser.get_all_trades() or []
        closed_trades = [t for t in trades if t.get("exit_price") or t.get("closed_at") or t.get("status") == "filled"]

        # Generate summary
        generator = get_tax_report_generator()
        summary = generator.generate_tax_summary(closed_trades)

        return jsonify(summary)
    except Exception as e:
        logger.error(f"Error generating tax summary: {e}")
        return jsonify({"error": str(e)}), 500


# ============================================================================
# ALERT SYSTEM API ENDPOINTS
# ============================================================================


@core_bp.route("/api/alerts/config", methods=["GET"], endpoint="core_get_alerts_legacy")
def get_alerts_legacy():
    """Get all configured alerts"""
    try:
        from services.alert_manager import alert_manager

        return jsonify(alert_manager.alerts)
    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        return jsonify({"error": str(e)}), 500


@core_bp.route("/api/alerts/config", methods=["POST"], endpoint="core_create_alert_legacy")
def create_alert_legacy():
    """Create a new alert"""
    try:
        from services.alert_manager import alert_manager

        data = request.json
        alert = alert_manager.add_alert(data)
        return jsonify({"success": True, "alert": alert})
    except Exception as e:
        logger.error(f"Error creating alert: {e}")
        return jsonify({"error": str(e)}), 500


@core_bp.route("/api/alerts/config/<int:alert_id>", methods=["DELETE"], endpoint="core_delete_alert_legacy")
def delete_alert_legacy(alert_id):
    """Delete an alert"""
    try:
        from services.alert_manager import alert_manager

        alert_manager.alerts = [
            a for a in alert_manager.alerts if a.get("id") != alert_id
        ]
        alert_manager.save_alerts()
        return jsonify({"success": True})
    except Exception as e:
        logger.error(f"Error deleting alert: {e}")
        return jsonify({"error": str(e)}), 500


@core_bp.route("/api/alerts/test", methods=["POST"], endpoint="core_test_alert_legacy")
def test_alert_legacy():
    """Test telegram notification"""
    try:
        # Try to send a test notification via telegram
        import os

        telegram_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID", "")

        if telegram_token and telegram_chat_id:
            # Send test message
            import requests

            url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
            response = requests.post(
                url,
                json={
                    "chat_id": telegram_chat_id,
                    "text": "✅ Test alert - notifications working!",
                },
                timeout=10,
            )
            response.raise_for_status()
            return jsonify({"success": True, "message": "Test notification sent!"})
        else:
            return jsonify({"success": False, "error": "Telegram not configured"})
    except Exception as e:
        logger.error(f"Error testing alert: {e}")
        return jsonify({"success": False, "error": str(e)})


# ============================================================================
# SETTINGS API ENDPOINTS
# ============================================================================


@core_bp.route("/api/settings", methods=["GET"], endpoint="core_get_settings_api")
def get_settings_api():
    """Get all settings"""
    try:
        from services.settings_manager import get_settings_manager

        settings_mgr = get_settings_manager()
        return jsonify(settings_mgr.settings)
    except Exception as e:
        logger.error(f"Error getting settings: {e}")
        return jsonify({"error": str(e)}), 500


@core_bp.route("/api/settings", methods=["POST"], endpoint="core_save_settings_api")
def save_settings_api():
    """Save settings"""
    try:
        from services.settings_manager import get_settings_manager

        settings_mgr = get_settings_manager()
        data = request.json
        settings_mgr.save_settings(data)
        return jsonify({"success": True})
    except Exception as e:
        logger.error(f"Error saving settings: {e}")
        return jsonify({"error": str(e)}), 500


@core_bp.route("/api/settings/reset", methods=["POST"], endpoint="core_reset_settings_api")
def reset_settings_api():
    """Reset settings to defaults"""
    try:
        from services.settings_manager import get_settings_manager

        settings_mgr = get_settings_manager()
        settings_mgr.reset_to_defaults()
        return jsonify({"success": True})
    except Exception as e:
        logger.error(f"Error resetting settings: {e}")
        return jsonify({"error": str(e)}), 500


# ============================================================================
# STRATEGY CONTROL API ENDPOINTS
# ============================================================================


@strategies_bp.route("/api/strategies/<name>/start", methods=["POST"], endpoint="strategies_start_strategy")
def start_strategy(name):
    """Start a strategy"""
    try:
        # Strategy control requires IPC mechanism to communicate with running bot
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Strategy control not yet implemented - requires inter-process communication",
                }
            ),
            501,
        )
    except Exception as e:
        logger.error(f"Error starting strategy: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@strategies_bp.route("/api/strategies/<name>/stop", methods=["POST"], endpoint="strategies_stop_strategy")
def stop_strategy(name):
    """Stop a strategy"""
    try:
        # Strategy control requires IPC mechanism to communicate with running bot
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Strategy control not yet implemented - requires inter-process communication",
                }
            ),
            501,
        )
    except Exception as e:
        logger.error(f"Error stopping strategy: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


# Phase 7C: Canonical test is POST /api/settings/test-connection. No duplicate /api/keys/test.


# ============================================================================
# PERFORMANCE METRICS API ENDPOINTS
# ============================================================================


@core_bp.route("/api/analytics/performance", endpoint="core_get_performance_metrics_alt")
def get_performance_metrics_alt():
    """Get performance metrics (Sharpe, Drawdown, Win Rate)"""
    try:
        from services.performance_calculator import get_performance_calculator

        # Get trades
        trades_data = data_parser.get_trades(page=1, per_page=10000)
        trade_list = (
            trades_data.get("trades", []) if isinstance(trades_data, dict) else []
        )

        if not trade_list:
            return jsonify({"sharpe_ratio": 0.0, "max_drawdown": 0.0, "win_rate": 0.0})

        # Calculate metrics
        perf_calc = get_performance_calculator()
        metrics = perf_calc.calculate_all_metrics(trade_list)

        return jsonify(
            {
                "sharpe_ratio": metrics.get("sharpe_ratio", 0.0),
                "max_drawdown": metrics.get("max_drawdown_pct", 0.0),
                "win_rate": metrics.get("win_rate", 0.0),
            }
        )

    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        return jsonify({"error": str(e)}), 500


# Register blueprints whose routes are defined in this file (must be after all @bp.route decorators)
app.register_blueprint(core_bp)
app.register_blueprint(journal_bp)
app.register_blueprint(settings_bp)
app.register_blueprint(strategies_bp)
app.register_blueprint(system_bp)

# Fail fast if any duplicate endpoint names (prevents route collisions)
validate_no_duplicate_endpoints(app)


def create_app():
    """App factory - returns the configured Flask application."""
    return app


# ============================================================================
# RUN APPLICATION
# ============================================================================

if __name__ == "__main__":
    # Initialize database
    init_db()

    # Run with SocketIO
    port = int(os.environ.get("DASHBOARD_PORT", 5001))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"

    logger.info(f"Starting dashboard on port {port}")
    socketio.run(app, debug=debug, host="0.0.0.0", port=port)
