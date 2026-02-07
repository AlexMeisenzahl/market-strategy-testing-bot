"""
Professional Web Dashboard for Market Strategy Testing Bot

A beautiful, responsive web interface for monitoring and controlling
the trading bot with comprehensive analytics and customization.
"""

from flask import Flask, render_template, jsonify, request, send_file
from flask_cors import CORS
import yaml
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
import json

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dashboard.services.data_parser import DataParser
from dashboard.services.analytics import AnalyticsService
from dashboard.services.chart_data import ChartDataService
from dashboard.services.config_manager import ConfigManager
from logger import get_logger

app = Flask(__name__)
CORS(app)  # Enable CORS for API access

# Configuration
BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / 'config.yaml'
LOGS_DIR = BASE_DIR / 'logs'

# Initialize services
logger = get_logger()
config_manager = ConfigManager(CONFIG_PATH)
data_parser = DataParser(LOGS_DIR)
analytics = AnalyticsService(data_parser)
chart_data = ChartDataService(data_parser)

# Global bot status (will be updated by bot)
bot_status = {
    'running': False,
    'paused': False,
    'uptime': 0,
    'last_restart': None,
    'mode': 'paper',
    'connected_symbols': 0,
    'active_strategies': 0
}


@app.route('/')
def index():
    """Render main dashboard page"""
    return render_template('index.html')


@app.route('/api/overview')
def get_overview():
    """Get overview dashboard summary statistics"""
    try:
        stats = analytics.get_overview_stats()
        return jsonify(stats)
    except Exception as e:
        logger.log_error(f"Error getting overview: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/trades')
def get_trades():
    """Get filtered trades data"""
    try:
        # Parse query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        symbol = request.args.get('symbol')
        strategy = request.args.get('strategy')
        outcome = request.args.get('outcome')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 25))
        
        trades = data_parser.get_trades(
            start_date=start_date,
            end_date=end_date,
            symbol=symbol,
            strategy=strategy,
            outcome=outcome,
            page=page,
            per_page=per_page
        )
        
        return jsonify(trades)
    except Exception as e:
        logger.log_error(f"Error getting trades: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/opportunities')
def get_opportunities():
    """Get opportunities data with filters"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        symbol = request.args.get('symbol')
        strategy = request.args.get('strategy')
        status = request.args.get('status')
        
        opportunities = data_parser.get_opportunities(
            start_date=start_date,
            end_date=end_date,
            symbol=symbol,
            strategy=strategy,
            status=status
        )
        
        return jsonify(opportunities)
    except Exception as e:
        logger.log_error(f"Error getting opportunities: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/charts/cumulative-pnl')
def get_cumulative_pnl():
    """Get cumulative P&L chart data"""
    try:
        time_range = request.args.get('range', '1M')
        data = chart_data.get_cumulative_pnl(time_range)
        return jsonify(data)
    except Exception as e:
        logger.log_error(f"Error getting cumulative P&L: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/charts/daily-pnl')
def get_daily_pnl():
    """Get daily P&L chart data"""
    try:
        data = chart_data.get_daily_pnl()
        return jsonify(data)
    except Exception as e:
        logger.log_error(f"Error getting daily P&L: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/charts/strategy-performance')
def get_strategy_performance():
    """Get strategy performance comparison data"""
    try:
        data = chart_data.get_strategy_performance()
        return jsonify(data)
    except Exception as e:
        logger.log_error(f"Error getting strategy performance: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/settings', methods=['GET'])
def get_settings():
    """Get all settings from config.yaml"""
    try:
        settings = config_manager.get_all_settings()
        return jsonify(settings)
    except Exception as e:
        logger.log_error(f"Error getting settings: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/settings/notifications', methods=['PUT'])
def update_notification_settings():
    """Update notification settings"""
    try:
        data = request.json
        config_manager.update_notification_settings(data)
        return jsonify({'success': True, 'message': 'Notification settings updated'})
    except Exception as e:
        logger.log_error(f"Error updating notification settings: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/settings/strategies', methods=['PUT'])
def update_strategy_settings():
    """Update strategy configuration"""
    try:
        data = request.json
        config_manager.update_strategy_settings(data)
        return jsonify({'success': True, 'message': 'Strategy settings updated'})
    except Exception as e:
        logger.log_error(f"Error updating strategy settings: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/notifications/test', methods=['POST'])
def test_notification():
    """Send test notification"""
    try:
        data = request.json
        notification_type = data.get('type', 'desktop')
        
        # Import and create notifier
        from notifier import Notifier
        config = config_manager.get_all_settings()
        notifier = Notifier(config)
        
        result = False
        if notification_type == 'desktop':
            result = notifier.send_desktop_notification(
                "Test Notification",
                "This is a test from the web dashboard"
            )
        elif notification_type == 'email':
            # Email notifications use send_sms method (it's named incorrectly but sends email)
            result = notifier.send_sms("Test email from web dashboard")
        elif notification_type == 'telegram':
            # Telegram uses send_push method
            result = notifier.send_push(
                "Test Notification",
                "This is a test from the web dashboard"
            )
        
        return jsonify({
            'success': result,
            'message': 'Test notification sent' if result else 'Test notification failed'
        })
    except Exception as e:
        logger.log_error(f"Error sending test notification: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/notifications/history')
def get_notification_history():
    """Get notification history"""
    try:
        # This would read from a notification log file
        # For now, return empty array
        return jsonify([])
    except Exception as e:
        logger.log_error(f"Error getting notification history: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/bot/status')
def get_bot_status():
    """Get current bot status"""
    try:
        return jsonify(bot_status)
    except Exception as e:
        logger.log_error(f"Error getting bot status: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/bot/start', methods=['POST'])
def start_bot():
    """Start the bot"""
    try:
        # This would trigger bot start
        # For now, just update status
        bot_status['running'] = True
        bot_status['paused'] = False
        bot_status['last_restart'] = datetime.now().isoformat()
        return jsonify({'success': True, 'message': 'Bot started'})
    except Exception as e:
        logger.log_error(f"Error starting bot: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/bot/stop', methods=['POST'])
def stop_bot():
    """Stop the bot"""
    try:
        # This would trigger bot stop
        bot_status['running'] = False
        return jsonify({'success': True, 'message': 'Bot stopped'})
    except Exception as e:
        logger.log_error(f"Error stopping bot: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/bot/restart', methods=['POST'])
def restart_bot():
    """Restart the bot"""
    try:
        # This would trigger bot restart
        bot_status['last_restart'] = datetime.now().isoformat()
        return jsonify({'success': True, 'message': 'Bot restarted'})
    except Exception as e:
        logger.log_error(f"Error restarting bot: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/export/trades', methods=['POST'])
def export_trades():
    """Export trades to CSV"""
    try:
        data = request.json
        file_format = data.get('format', 'csv')
        
        # This would generate and return CSV file
        # For now, return success
        return jsonify({'success': True, 'message': 'Export complete'})
    except Exception as e:
        logger.log_error(f"Error exporting trades: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/logs/recent')
def get_recent_logs():
    """Get recent log entries"""
    try:
        limit = int(request.args.get('limit', 100))
        level = request.args.get('level', 'all')
        
        # Read from log file
        logs = []
        # TODO: Implement log reading
        
        return jsonify(logs)
    except Exception as e:
        logger.log_error(f"Error getting logs: {str(e)}")
        return jsonify({'error': str(e)}), 500


def update_bot_status_from_instance(status_dict):
    """
    Update bot status from running bot instance
    
    Args:
        status_dict: Dictionary with bot status info
    """
    global bot_status
    bot_status.update(status_dict)


if __name__ == '__main__':
    # Check if config exists
    if not CONFIG_PATH.exists():
        print(f"ERROR: Config file not found: {CONFIG_PATH}")
        print("Please copy config.example.yaml to config.yaml and configure it")
        sys.exit(1)
    
    # Create logs directory if it doesn't exist
    LOGS_DIR.mkdir(exist_ok=True)
    
    # Get debug mode from environment (default to False for security)
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    print("\n" + "="*60)
    print("🚀 Market Strategy Testing Bot - Web Dashboard")
    print("="*60)
    print(f"\n📊 Dashboard URL: http://localhost:5000")
    print(f"📁 Config file: {CONFIG_PATH}")
    print(f"📂 Logs directory: {LOGS_DIR}")
    if debug_mode:
        print("\n⚠️  DEBUG MODE ENABLED - For development only!")
    print("\nPress Ctrl+C to stop the server\n")
    
    # Run Flask app
    # Debug mode is disabled by default for security
    # Set FLASK_DEBUG=true environment variable to enable it
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=debug_mode,
        use_reloader=debug_mode
    )
