"""
Dashboard Server - Flask-based Web Dashboard for Market Strategy Testing Bot

Provides real-time monitoring, control, and analytics via web interface
"""

import json
import time
import threading
import csv
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
from collections import defaultdict

from flask import Flask, render_template, jsonify, request, Response
from flask_cors import CORS
import yaml


class DashboardServer:
    """Flask server for the web dashboard"""
    
    def __init__(self, bot_instance=None, config: Dict[str, Any] = None):
        """
        Initialize dashboard server
        
        Args:
            bot_instance: Reference to the main bot instance
            config: Configuration dictionary
        """
        self.bot = bot_instance
        self.config = config or {}
        
        # Flask app setup
        self.app = Flask(__name__)
        CORS(self.app)
        
        # Thread-safe data storage
        self.lock = threading.Lock()
        self.opportunities_log = []
        self.trades_log = []
        self.alerts_log = []
        self.activities_log = []
        
        # Bot control state
        self.bot_status = "stopped"
        self.start_time = None
        self.paused = False
        
        # Setup routes
        self._setup_routes()
        
        # Load historical data
        self._load_historical_data()
    
    def _setup_routes(self):
        """Setup Flask routes"""
        
        # Main dashboard page
        @self.app.route('/')
        def index():
            return render_template('dashboard.html')
        
        # Control endpoints
        @self.app.route('/api/start', methods=['POST'])
        def start_bot():
            with self.lock:
                if self.bot and hasattr(self.bot, 'resume'):
                    self.bot.paused = False
                    self.bot.running = True
                    self.bot_status = "running"
                    if not self.start_time:
                        self.start_time = datetime.now()
                    self._add_alert("info", "Bot started/resumed")
                    return jsonify({"status": "success", "message": "Bot started"})
                return jsonify({"status": "error", "message": "Bot not available"}), 400
        
        @self.app.route('/api/pause', methods=['POST'])
        def pause_bot():
            with self.lock:
                if self.bot:
                    self.bot.paused = True
                    self.bot_status = "paused"
                    self._add_alert("warning", "Bot paused")
                    return jsonify({"status": "success", "message": "Bot paused"})
                return jsonify({"status": "error", "message": "Bot not available"}), 400
        
        @self.app.route('/api/stop', methods=['POST'])
        def stop_bot():
            with self.lock:
                if self.bot:
                    self.bot.running = False
                    self.bot.paused = True
                    self.bot_status = "stopped"
                    self._add_alert("error", "Bot stopped")
                    return jsonify({"status": "success", "message": "Bot stopped"})
                return jsonify({"status": "error", "message": "Bot not available"}), 400
        
        @self.app.route('/api/restart', methods=['POST'])
        def restart_bot():
            with self.lock:
                if self.bot:
                    self.bot.paused = False
                    self.bot.running = True
                    self.bot_status = "running"
                    self.start_time = datetime.now()
                    self._add_alert("info", "Bot restarted")
                    return jsonify({"status": "success", "message": "Bot restarted"})
                return jsonify({"status": "error", "message": "Bot not available"}), 400
        
        # Data endpoints
        @self.app.route('/api/status', methods=['GET'])
        def get_status():
            with self.lock:
                uptime = 0
                if self.start_time and self.bot_status == "running":
                    uptime = int((datetime.now() - self.start_time).total_seconds())
                
                return jsonify({
                    "status": self.bot_status,
                    "paused": self.paused,
                    "uptime": uptime,
                    "last_update": datetime.now().isoformat(),
                    "connection_healthy": self.bot.monitor.connection_healthy if self.bot else True,
                })
        
        @self.app.route('/api/metrics', methods=['GET'])
        def get_metrics():
            with self.lock:
                # Get statistics from bot components
                trade_stats = self.bot.trader.get_statistics() if self.bot else {}
                detect_stats = self.bot.detector.get_statistics() if self.bot else {}
                
                # Calculate additional metrics
                total_trades = len(self.trades_log)
                winning_trades = sum(1 for t in self.trades_log if t.get('expected_profit', 0) > 0)
                win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
                
                # Find best strategy (placeholder - needs strategy tracking)
                best_strategy = "Arbitrage"
                
                # Calculate current balance (paper trading)
                initial_balance = 10000  # Default paper trading balance
                current_balance = initial_balance + trade_stats.get('total_profit', 0)
                
                return jsonify({
                    "total_pnl": trade_stats.get('total_profit', 0),
                    "pnl_percentage": trade_stats.get('return_percentage', 0),
                    "win_rate": win_rate,
                    "total_trades": total_trades,
                    "current_balance": current_balance,
                    "active_opportunities": len([o for o in self.opportunities_log[-20:] if (datetime.now() - datetime.fromisoformat(o.get('detected_at', datetime.now().isoformat()))).seconds < 60]),
                    "best_strategy": best_strategy,
                    "opportunities_found": detect_stats.get('opportunities_found', 0)
                })
        
        @self.app.route('/api/strategies', methods=['GET'])
        def get_strategies():
            with self.lock:
                # Calculate strategy performance
                strategies = self._calculate_strategy_performance()
                return jsonify(strategies)
        
        @self.app.route('/api/trades', methods=['GET'])
        def get_trades():
            with self.lock:
                # Return recent trades
                page = request.args.get('page', 1, type=int)
                per_page = request.args.get('per_page', 50, type=int)
                
                start_idx = (page - 1) * per_page
                end_idx = start_idx + per_page
                
                trades_subset = self.trades_log[start_idx:end_idx]
                
                return jsonify({
                    "trades": trades_subset,
                    "total": len(self.trades_log),
                    "page": page,
                    "per_page": per_page
                })
        
        @self.app.route('/api/opportunities', methods=['GET'])
        def get_opportunities():
            with self.lock:
                # Return recent opportunities (last 50)
                recent_opps = self.opportunities_log[-50:]
                return jsonify({"opportunities": recent_opps})
        
        @self.app.route('/api/alerts', methods=['GET'])
        def get_alerts():
            with self.lock:
                # Return recent alerts (last 50)
                recent_alerts = self.alerts_log[-50:]
                return jsonify({"alerts": recent_alerts})
        
        @self.app.route('/api/config', methods=['GET'])
        def get_config():
            with self.lock:
                # Return relevant config settings
                return jsonify({
                    "min_profit_margin": self.config.get('min_profit_margin', 0.02),
                    "max_trade_size": self.config.get('max_trade_size', 10),
                    "max_trades_per_hour": self.config.get('max_trades_per_hour', 10),
                    "paper_trading": self.config.get('paper_trading', True),
                    "desktop_notifications": self.config.get('desktop_notifications', False),
                    "alert_on_opportunities": self.config.get('alert_on_opportunities', True),
                })
        
        @self.app.route('/api/config/update', methods=['POST'])
        def update_config():
            with self.lock:
                try:
                    data = request.get_json()
                    
                    # Update config
                    for key, value in data.items():
                        if key in ['min_profit_margin', 'max_trade_size', 'max_trades_per_hour',
                                   'desktop_notifications', 'alert_on_opportunities']:
                            self.config[key] = value
                    
                    # Save to file
                    self._save_config()
                    
                    self._add_alert("info", "Configuration updated")
                    return jsonify({"status": "success", "message": "Configuration updated"})
                except Exception as e:
                    return jsonify({"status": "error", "message": str(e)}), 400
        
        @self.app.route('/api/notifications/toggle', methods=['POST'])
        def toggle_notifications():
            with self.lock:
                try:
                    data = request.get_json()
                    notification_type = data.get('type')
                    enabled = data.get('enabled', False)
                    
                    if notification_type == 'desktop':
                        self.config['desktop_notifications'] = enabled
                    elif notification_type == 'email':
                        # Placeholder for email notifications
                        pass
                    elif notification_type == 'telegram':
                        # Placeholder for telegram notifications
                        pass
                    
                    # Save to file
                    self._save_config()
                    
                    self._add_alert("info", f"{notification_type.title()} notifications {'enabled' if enabled else 'disabled'}")
                    return jsonify({"status": "success", "message": "Notification setting updated"})
                except Exception as e:
                    return jsonify({"status": "error", "message": str(e)}), 400
        
        # Server-Sent Events for real-time updates
        @self.app.route('/api/stream')
        def stream():
            def event_stream():
                while True:
                    # Send periodic updates
                    try:
                        data = {
                            "timestamp": datetime.now().isoformat(),
                            "status": self.bot_status,
                            "new_opportunities": len([o for o in self.opportunities_log[-5:]]),
                            "new_trades": len([t for t in self.trades_log[-5:]]),
                        }
                        yield f"data: {json.dumps(data)}\n\n"
                        time.sleep(2)  # Update every 2 seconds
                    except GeneratorExit:
                        break
            
            return Response(event_stream(), mimetype="text/event-stream")
        
        @self.app.route('/api/chart/pnl', methods=['GET'])
        def get_pnl_chart_data():
            with self.lock:
                # Calculate cumulative P&L over time
                pnl_data = []
                cumulative_pnl = 0
                
                for trade in self.trades_log:
                    cumulative_pnl += trade.get('expected_profit', 0)
                    pnl_data.append({
                        "timestamp": trade.get('executed_at', datetime.now().isoformat()),
                        "pnl": cumulative_pnl
                    })
                
                return jsonify({"data": pnl_data})
        
        @self.app.route('/api/chart/strategies', methods=['GET'])
        def get_strategy_chart_data():
            with self.lock:
                strategies = self._calculate_strategy_performance()
                
                chart_data = {
                    "labels": [s['name'] for s in strategies],
                    "pnl": [s['total_pnl'] for s in strategies],
                    "win_rates": [s['win_rate'] for s in strategies]
                }
                
                return jsonify(chart_data)
    
    def _load_historical_data(self):
        """Load historical trades and opportunities from CSV files"""
        # Load trades
        trades_file = Path("logs/trades.csv")
        if trades_file.exists():
            try:
                with open(trades_file, 'r') as f:
                    reader = csv.DictReader(f)
                    self.trades_log = list(reader)
                    # Convert numeric fields
                    for trade in self.trades_log:
                        for key in ['yes_price', 'no_price', 'trade_size', 'total_cost', 
                                    'expected_return', 'expected_profit', 'profit_percentage']:
                            if key in trade:
                                trade[key] = float(trade[key])
            except Exception as e:
                print(f"Error loading trades: {e}")
        
        # Load opportunities
        opps_file = Path("logs/opportunities.csv")
        if opps_file.exists():
            try:
                with open(opps_file, 'r') as f:
                    reader = csv.DictReader(f)
                    self.opportunities_log = list(reader)
                    # Convert numeric fields
                    for opp in self.opportunities_log:
                        for key in ['yes_price', 'no_price', 'price_sum', 'profit_margin']:
                            if key in opp:
                                opp[key] = float(opp[key])
            except Exception as e:
                print(f"Error loading opportunities: {e}")
    
    def _save_config(self):
        """Save config to YAML file"""
        try:
            with open('config.yaml', 'w') as f:
                yaml.dump(self.config, f, default_flow_style=False)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def _calculate_strategy_performance(self) -> List[Dict[str, Any]]:
        """Calculate performance metrics by strategy"""
        # For now, we only have one strategy (Arbitrage)
        # In the future, this can be expanded to track multiple strategies
        
        total_trades = len(self.trades_log)
        winning_trades = sum(1 for t in self.trades_log if t.get('expected_profit', 0) > 0)
        total_pnl = sum(t.get('expected_profit', 0) for t in self.trades_log)
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        avg_profit = total_pnl / total_trades if total_trades > 0 else 0
        
        # Find best and worst trades
        best_trade = max([t.get('expected_profit', 0) for t in self.trades_log], default=0)
        worst_trade = min([t.get('expected_profit', 0) for t in self.trades_log], default=0)
        
        return [{
            "name": "Arbitrage",
            "total_trades": total_trades,
            "win_rate": win_rate,
            "total_pnl": total_pnl,
            "avg_profit": avg_profit,
            "roi": (total_pnl / (total_trades * 10) * 100) if total_trades > 0 else 0,  # Assuming $10 per trade
            "sharpe_ratio": 0,  # Placeholder
            "best_trade": best_trade,
            "worst_trade": worst_trade
        }]
    
    def _add_alert(self, alert_type: str, message: str):
        """Add an alert to the log"""
        alert = {
            "timestamp": datetime.now().isoformat(),
            "type": alert_type,
            "message": message
        }
        self.alerts_log.append(alert)
        
        # Keep only last 100 alerts
        if len(self.alerts_log) > 100:
            self.alerts_log = self.alerts_log[-100:]
    
    def add_opportunity(self, opportunity: Dict[str, Any]):
        """Add a new opportunity to the log (called by bot)"""
        with self.lock:
            self.opportunities_log.append(opportunity)
            
            # Keep only last 200 opportunities
            if len(self.opportunities_log) > 200:
                self.opportunities_log = self.opportunities_log[-200:]
            
            # Save to CSV
            self._save_opportunity_to_csv(opportunity)
    
    def add_trade(self, trade: Dict[str, Any]):
        """Add a new trade to the log (called by bot)"""
        with self.lock:
            self.trades_log.append(trade)
            
            # Save to CSV
            self._save_trade_to_csv(trade)
    
    def _save_opportunity_to_csv(self, opportunity: Dict[str, Any]):
        """Save opportunity to CSV file"""
        try:
            os.makedirs('logs', exist_ok=True)
            file_path = Path("logs/opportunities.csv")
            file_exists = file_path.exists()
            
            with open(file_path, 'a', newline='') as f:
                fieldnames = ['market_id', 'market_name', 'yes_price', 'no_price', 
                              'price_sum', 'profit_margin', 'detected_at']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                
                if not file_exists:
                    writer.writeheader()
                
                writer.writerow(opportunity)
        except Exception as e:
            print(f"Error saving opportunity to CSV: {e}")
    
    def _save_trade_to_csv(self, trade: Dict[str, Any]):
        """Save trade to CSV file"""
        try:
            os.makedirs('logs', exist_ok=True)
            file_path = Path("logs/trades.csv")
            file_exists = file_path.exists()
            
            with open(file_path, 'a', newline='') as f:
                fieldnames = ['market_id', 'market_name', 'yes_price', 'no_price', 
                              'trade_size', 'total_cost', 'expected_return', 
                              'expected_profit', 'profit_percentage', 'executed_at', 'status']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                
                if not file_exists:
                    writer.writeheader()
                
                writer.writerow(trade)
        except Exception as e:
            print(f"Error saving trade to CSV: {e}")
    
    def run(self, host='localhost', port=5000, debug=False):
        """Run the Flask server"""
        self.app.run(host=host, port=port, debug=debug, threaded=True)


def create_dashboard_server(bot_instance=None, config: Dict[str, Any] = None) -> DashboardServer:
    """
    Factory function to create dashboard server
    
    Args:
        bot_instance: Reference to the main bot
        config: Configuration dictionary
        
    Returns:
        DashboardServer instance
    """
    return DashboardServer(bot_instance, config)
