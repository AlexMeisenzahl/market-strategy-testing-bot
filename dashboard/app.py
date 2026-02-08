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
import psutil  # For process monitoring

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


@app.route('/api/tax/summary')
def get_tax_summary():
    """Get tax summary data from tax_exporter"""
    try:
        year = request.args.get('year', None)
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
        logger.log_error(f"Error getting tax summary: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/tax/positions')
def get_tax_positions():
    """Get detailed tax positions for Form 8949"""
    try:
        year = request.args.get('year', None)
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
        logger.log_error(f"Error getting tax positions: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/tax/export/<format>')
def export_tax_report(format):
    """Export tax report in various formats"""
    try:
        year = request.args.get('year', datetime.now().year)
        if isinstance(year, str):
            year = int(year)
        
        # Import and initialize tax exporter
        from tax_exporter import TaxExporter
        config = config_manager.get_all_settings()
        tax_exporter = TaxExporter(config, str(LOGS_DIR))
        
        if format == 'csv':
            # Export to CSV
            output_path = tax_exporter.export_to_csv(year, str(LOGS_DIR))
            if output_path and os.path.exists(output_path):
                return send_file(output_path, as_attachment=True, download_name=f'tax_report_{year}.csv')
            else:
                return jsonify({'error': 'Failed to generate CSV'}), 500
        
        elif format == 'turbotax':
            # TurboTax TXF format (simplified - would need full implementation)
            return jsonify({'error': 'TurboTax format not yet implemented'}), 501
        
        elif format == 'hrblock':
            # H&R Block CSV format (similar to standard CSV)
            output_path = tax_exporter.export_to_csv(year, str(LOGS_DIR))
            if output_path and os.path.exists(output_path):
                return send_file(output_path, as_attachment=True, download_name=f'hrblock_report_{year}.csv')
            else:
                return jsonify({'error': 'Failed to generate CSV'}), 500
        
        elif format == 'form8949':
            # IRS Form 8949 format (simplified - would need full implementation)
            return jsonify({'error': 'Form 8949 format not yet implemented'}), 501
        
        else:
            return jsonify({'error': 'Unknown format'}), 400
            
    except Exception as e:
        logger.log_error(f"Error exporting tax report: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/analytics/risk')
def get_risk_analytics():
    """Get risk analytics metrics"""
    try:
        # Get trades data
        trades_data = data_parser.get_trades(page=1, per_page=10000)
        trade_list = trades_data.get('trades', []) if isinstance(trades_data, dict) else []
        
        if not trade_list:
            return jsonify({
                'sharpe_ratio': 0,
                'sortino_ratio': 0,
                'max_drawdown': 0,
                'volatility': 0,
                'var_95': 0,
                'beta': 0
            })
        
        # Calculate basic risk metrics
        # Note: These are simplified calculations - full implementation would need more sophisticated algorithms
        import numpy as np
        
        # Get P&L series
        pnl_series = [t.get('profit', 0) for t in trade_list]
        
        if not pnl_series:
            return jsonify({
                'sharpe_ratio': 0,
                'sortino_ratio': 0,
                'max_drawdown': 0,
                'volatility': 0,
                'var_95': 0,
                'beta': 0
            })
        
        # Calculate metrics
        returns = np.array(pnl_series)
        mean_return = np.mean(returns)
        std_return = np.std(returns)
        
        # Sharpe Ratio (simplified - assuming risk-free rate of 0)
        sharpe_ratio = (mean_return / std_return) if std_return > 0 else 0
        
        # Sortino Ratio (using downside deviation)
        downside_returns = returns[returns < 0]
        downside_std = np.std(downside_returns) if len(downside_returns) > 0 else std_return
        sortino_ratio = (mean_return / downside_std) if downside_std > 0 else 0
        
        # Max Drawdown
        cumulative = np.cumsum(returns)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - running_max)
        max_drawdown = np.min(drawdown) if len(drawdown) > 0 else 0
        
        # Volatility
        volatility = std_return
        
        # Value at Risk (95% confidence)
        var_95 = np.percentile(returns, 5) if len(returns) > 0 else 0
        
        # Beta (simplified - would need market data for proper calculation)
        beta = 1.0  # Placeholder
        
        return jsonify({
            'sharpe_ratio': round(float(sharpe_ratio), 2),
            'sortino_ratio': round(float(sortino_ratio), 2),
            'max_drawdown': round(float(max_drawdown), 2),
            'volatility': round(float(volatility), 2),
            'var_95': round(float(var_95), 2),
            'beta': round(float(beta), 2)
        })
    except Exception as e:
        logger.log_error(f"Error calculating risk analytics: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/analytics/strategy-breakdown')
def get_strategy_breakdown():
    """Get detailed per-strategy performance breakdown"""
    try:
        # Get trades data
        trades_data = data_parser.get_trades(page=1, per_page=10000)
        trade_list = trades_data.get('trades', []) if isinstance(trades_data, dict) else []
        
        # Group by strategy
        strategy_stats = {}
        for trade in trade_list:
            strategy = trade.get('strategy', 'unknown')
            if strategy not in strategy_stats:
                strategy_stats[strategy] = {
                    'strategy': strategy,
                    'total_trades': 0,
                    'winning_trades': 0,
                    'losing_trades': 0,
                    'total_pnl': 0,
                    'avg_win': 0,
                    'avg_loss': 0,
                    'win_rate': 0,
                    'profit_factor': 0,
                    'max_drawdown': 0
                }
            
            profit = trade.get('profit', 0)
            strategy_stats[strategy]['total_trades'] += 1
            strategy_stats[strategy]['total_pnl'] += profit
            
            if profit > 0:
                strategy_stats[strategy]['winning_trades'] += 1
            else:
                strategy_stats[strategy]['losing_trades'] += 1
        
        # Calculate derived metrics
        for strategy in strategy_stats:
            stats = strategy_stats[strategy]
            total = stats['total_trades']
            wins = stats['winning_trades']
            losses = stats['losing_trades']
            
            if total > 0:
                stats['win_rate'] = round((wins / total) * 100, 2)
            
            # Get wins and losses for averages
            strategy_trades = [t for t in trade_list if t.get('strategy') == strategy]
            win_amounts = [t.get('profit', 0) for t in strategy_trades if t.get('profit', 0) > 0]
            loss_amounts = [abs(t.get('profit', 0)) for t in strategy_trades if t.get('profit', 0) < 0]
            
            stats['avg_win'] = round(sum(win_amounts) / len(win_amounts), 2) if win_amounts else 0
            stats['avg_loss'] = round(sum(loss_amounts) / len(loss_amounts), 2) if loss_amounts else 0
            
            # Profit factor
            total_wins = sum(win_amounts)
            total_losses = sum(loss_amounts)
            stats['profit_factor'] = round(total_wins / total_losses, 2) if total_losses > 0 else 0
        
        # Convert to list and sort by P&L
        breakdown = list(strategy_stats.values())
        breakdown.sort(key=lambda x: x['total_pnl'], reverse=True)
        
        return jsonify(breakdown)
    except Exception as e:
        logger.log_error(f"Error getting strategy breakdown: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/data/verify')
def verify_data_quality():
    """
    Run comprehensive data quality checks
    
    Returns health status, issues, and check results
    """
    try:
        from dashboard.services.data_validator import DataValidator
        
        validator = DataValidator()
        results = {
            'status': 'healthy',  # or 'warning' or 'error'
            'checks': {},
            'issues': []
        }
        
        # Check 1: CSV file exists
        trades_csv = LOGS_DIR / 'trades.csv'
        if not trades_csv.exists():
            results['status'] = 'warning'
            results['issues'].append('trades.csv not found - using sample data')
            return jsonify(results)
        
        # Check 2: Validate CSV structure
        csv_validation = validator.validate_csv_data(trades_csv)
        results['checks']['csv_validation'] = csv_validation
        
        if not csv_validation['valid']:
            results['status'] = 'error'
            results['issues'].extend(csv_validation['issues'])
        
        # Check 3: Calculate total P&L and verify integrity
        trades = data_parser.get_all_trades()
        if trades:
            calculated_pnl = data_parser.calculate_total_pnl(trades)
            results['checks']['total_pnl'] = calculated_pnl
            
            # Check 4: Win rate in valid range
            win_rate = data_parser.calculate_win_rate(trades)
            results['checks']['win_rate'] = win_rate
            
            if win_rate == 100.0 and len(trades) > 10:
                results['status'] = 'warning'
                results['issues'].append(f'Win rate is exactly 100% with {len(trades)} trades - suspicious')
            
            # Check 5: No outlier trades
            pnls = [t['pnl_usd'] for t in trades]
            if pnls and len(pnls) > 1:
                mean = sum(pnls) / len(pnls)
                variance = sum((x - mean) ** 2 for x in pnls) / len(pnls)
                std = variance ** 0.5
                
                outliers = [p for p in pnls if abs(p - mean) > 3 * std]
                if outliers:
                    results['status'] = 'warning'
                    results['issues'].append(f'Found {len(outliers)} outlier trades')
            
            # Check 6: No future timestamps
            future_trades = [t for t in trades if datetime.fromisoformat(t['entry_time']) > datetime.now()]
            if future_trades:
                results['status'] = 'error'
                results['issues'].append(f'{len(future_trades)} trades have future timestamps')
        
        return jsonify(results)
    except Exception as e:
        logger.log_error(f"Error verifying data quality: {str(e)}")
        return jsonify({
            'status': 'error',
            'issues': [f'Verification failed: {str(e)}']
        }), 500


@app.route('/api/recent_activity')
def get_recent_activity():
    """
    Get recent activity feed (trades, opportunities, events)
    
    Returns last 20 activities sorted by timestamp
    """
    try:
        activities = []
        
        # Get recent trades
        trades = data_parser.get_all_trades()
        if trades:
            # Get last 10 trades
            recent_trades = sorted(trades, key=lambda x: x['entry_time'], reverse=True)[:10]
            
            for trade in recent_trades:
                activities.append({
                    'type': 'trade',
                    'message': f"{trade['strategy']}: {trade['symbol']} - ${trade['pnl_usd']:.2f}",
                    'profit': trade['pnl_usd'],
                    'timestamp': trade['entry_time'],
                    'details': trade
                })
        
        # Get recent opportunities
        opportunities = data_parser.get_all_opportunities()
        if opportunities:
            # Get last 10 opportunities
            recent_opps = sorted(opportunities, key=lambda x: x['timestamp'], reverse=True)[:10]
            
            for opp in recent_opps:
                activities.append({
                    'type': 'opportunity',
                    'message': f"{opp['strategy']}: {opp['symbol']} - Confidence: {opp['confidence']:.0%}",
                    'profit': None,
                    'timestamp': opp['timestamp'],
                    'details': opp
                })
        
        # Sort all activities by timestamp (newest first)
        activities.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # Return last 20
        return jsonify(activities[:20])
    except Exception as e:
        logger.log_error(f"Error getting recent activity: {str(e)}")
        return jsonify({'error': str(e)}), 500


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
