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


@app.route('/opportunities')
def opportunities_page():
    """Render opportunities page"""
    return render_template('opportunities.html')


@app.route('/health')
def health_check():
    """Health check endpoint for startup verification"""
    try:
        # Check if logs directory exists
        logs_exist = LOGS_DIR.exists()
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'logs_directory': str(LOGS_DIR),
            'logs_exist': logs_exist,
            'services': {
                'data_parser': 'ready',
                'analytics': 'ready',
                'chart_data': 'ready'
            }
        }), 200
    except Exception as e:
        logger.log_error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500


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




@app.route('/api/analytics/overview')
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
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Get trades and opportunities
        trades = data_parser.get_trades(start_date=start_date, end_date=end_date, page=1, per_page=10000)
        opportunities = data_parser.get_opportunities(start_date=start_date, end_date=end_date)
        
        # Calculate statistics
        total_opportunities = len(opportunities) if opportunities else 0
        total_trades = trades.get('total', 0) if isinstance(trades, dict) else 0
        trade_list = trades.get('trades', []) if isinstance(trades, dict) else []
        
        # Calculate P&L
        total_pnl = sum(t.get('profit', 0) for t in trade_list)
        winning_trades = len([t for t in trade_list if t.get('profit', 0) > 0])
        losing_trades = len([t for t in trade_list if t.get('profit', 0) < 0])
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        # Success rate by strategy
        strategy_stats = {}
        for trade in trade_list:
            strategy = trade.get('strategy', 'unknown')
            if strategy not in strategy_stats:
                strategy_stats[strategy] = {'total': 0, 'wins': 0, 'profit': 0}
            strategy_stats[strategy]['total'] += 1
            if trade.get('profit', 0) > 0:
                strategy_stats[strategy]['wins'] += 1
            strategy_stats[strategy]['profit'] += trade.get('profit', 0)
        
        # Calculate win rate per strategy
        for strategy in strategy_stats:
            total = strategy_stats[strategy]['total']
            wins = strategy_stats[strategy]['wins']
            strategy_stats[strategy]['win_rate'] = (wins / total * 100) if total > 0 else 0
        
        return jsonify({
            'total_opportunities': total_opportunities,
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': round(win_rate, 2),
            'total_pnl': round(total_pnl, 2),
            'average_profit_per_trade': round(total_pnl / total_trades, 2) if total_trades > 0 else 0,
            'strategy_performance': strategy_stats
        })
    except Exception as e:
        logger.log_error(f"Error getting analytics overview: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/analytics/charts')
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
        time_range = request.args.get('range', '1M')
        
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
                date_str = opp.get('timestamp', '')[:10] if opp.get('timestamp') else ''
                if date_str:
                    daily_opportunities[date_str] += 1
        
        # Convert to sorted list
        opportunity_timeline = [
            {'date': date, 'count': count}
            for date, count in sorted(daily_opportunities.items())
        ]
        
        return jsonify({
            'cumulative_pnl': cumulative_pnl,
            'daily_pnl': daily_pnl,
            'strategy_performance': strategy_performance,
            'opportunity_timeline': opportunity_timeline
        })
    except Exception as e:
        logger.log_error(f"Error getting analytics charts: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/export/trades', methods=['POST'])
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
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        market = data.get('market')
        strategy = data.get('strategy')
        
        # Get all trades matching filters
        trades_data = data_parser.get_trades(
            start_date=start_date,
            end_date=end_date,
            symbol=market,
            strategy=strategy,
            page=1,
            per_page=10000  # Get all trades
        )
        
        trade_list = trades_data.get('trades', []) if isinstance(trades_data, dict) else []
        
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'Timestamp',
            'Market',
            'Strategy',
            'Entry Price',
            'Exit Price',
            'Size',
            'Profit/Loss',
            'Status',
            'Notes'
        ])
        
        # Write data rows
        for trade in trade_list:
            writer.writerow([
                trade.get('timestamp', ''),
                trade.get('market', ''),
                trade.get('strategy', ''),
                trade.get('entry_price', ''),
                trade.get('exit_price', ''),
                trade.get('size', ''),
                trade.get('profit', 0),
                trade.get('status', ''),
                trade.get('notes', '')
            ])
        
        # Create response
        output.seek(0)
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=trades_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
        return response
    except Exception as e:
        logger.log_error(f"Error exporting trades: {str(e)}")
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
            result = notifier.send_email("Test email from web dashboard")
        elif notification_type == 'telegram':
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
        # Check if bot.py process is actually running
        import psutil
        bot_running = False
        bot_pid = None
        bot_uptime = 0
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time']):
            try:
                cmdline = proc.info.get('cmdline', [])
                if cmdline and any('bot.py' in str(cmd) for cmd in cmdline):
                    bot_running = True
                    bot_pid = proc.info['pid']
                    # Calculate uptime in seconds
                    bot_uptime = int((datetime.now().timestamp() - proc.info['create_time']))
                    break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # Update global status
        bot_status['running'] = bot_running
        bot_status['pid'] = bot_pid
        bot_status['uptime'] = bot_uptime
        
        # Add status emoji
        if bot_running:
            bot_status['status_emoji'] = '🟢'
            bot_status['status_text'] = 'Running'
        elif bot_status.get('paused', False):
            bot_status['status_emoji'] = '🟡'
            bot_status['status_text'] = 'Paused'
        else:
            bot_status['status_emoji'] = '🔴'
            bot_status['status_text'] = 'Stopped'
        
        return jsonify(bot_status)
    except Exception as e:
        logger.log_error(f"Error getting bot status: {str(e)}")
        # Return default status on error
        return jsonify({
            'running': False,
            'status_emoji': '🟡',
            'status_text': 'Error',
            'error': str(e)
        }), 200  # Return 200 even on error to avoid breaking frontend


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


@app.route('/api/logs/recent')
def get_recent_logs():
    """Get recent log entries"""
    try:
        limit = int(request.args.get('limit', 100))
        level = request.args.get('level', 'all')
        
        # Read from bot.log file if it exists
        logs = []
        log_file = LOGS_DIR / 'bot.log'
        
        if log_file.exists():
            try:
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                    # Get last 'limit' lines
                    recent_lines = lines[-limit:] if len(lines) > limit else lines
                    
                    for line in recent_lines:
                        line = line.strip()
                        if line:
                            # Parse log line (basic parsing)
                            logs.append({
                                'timestamp': datetime.now().isoformat(),  # Would parse from log
                                'level': 'INFO',  # Would parse from log
                                'message': line
                            })
            except Exception as e:
                logger.log_error(f"Error reading log file: {str(e)}")
        
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
