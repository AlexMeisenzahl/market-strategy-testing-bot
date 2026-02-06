"""
Logger Module - Structured logging for the arbitrage bot

Creates and manages log files:
- logs/trades.csv: Paper trade executions
- logs/opportunities.csv: All arbitrage opportunities found
- logs/errors.log: Error and warning messages
- logs/connection.log: Connection health monitoring
"""

import csv
import os
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path


class Logger:
    """Central logging system for all bot activities"""
    
    def __init__(self, log_dir: str = "logs"):
        """
        Initialize logger with automatic log directory creation
        
        Args:
            log_dir: Directory to store log files (default: logs/)
        """
        self.log_dir = Path(log_dir)
        self._ensure_log_directory()
        self._initialize_csv_files()
    
    def _ensure_log_directory(self) -> None:
        """Create logs directory if it doesn't exist"""
        self.log_dir.mkdir(exist_ok=True)
    
    def _initialize_csv_files(self) -> None:
        """Initialize CSV files with headers if they don't exist"""
        # Initialize trades.csv
        trades_file = self.log_dir / "trades.csv"
        if not trades_file.exists():
            with open(trades_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'timestamp', 'market', 'yes_price', 'no_price', 
                    'sum', 'profit_pct', 'profit_usd', 'status'
                ])
        
        # Initialize opportunities.csv
        opportunities_file = self.log_dir / "opportunities.csv"
        if not opportunities_file.exists():
            with open(opportunities_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'timestamp', 'market', 'yes_price', 'no_price',
                    'sum', 'profit_pct', 'action_taken'
                ])
    
    def log_trade(self, market: str, yes_price: float, no_price: float, 
                  profit_usd: float, status: str = "executed") -> None:
        """
        Log a paper trade execution
        
        Args:
            market: Market identifier
            yes_price: YES contract price
            no_price: NO contract price
            profit_usd: Expected profit in USD
            status: Trade status (executed, failed, etc.)
        """
        trades_file = self.log_dir / "trades.csv"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        price_sum = yes_price + no_price
        profit_pct = ((1.0 - price_sum) / price_sum) * 100
        
        with open(trades_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                timestamp, market, f"{yes_price:.3f}", f"{no_price:.3f}",
                f"{price_sum:.3f}", f"{profit_pct:.1f}", f"{profit_usd:.2f}", status
            ])
    
    def log_opportunity(self, market: str, yes_price: float, no_price: float,
                       action_taken: str) -> None:
        """
        Log an arbitrage opportunity (traded or skipped)
        
        Args:
            market: Market identifier
            yes_price: YES contract price
            no_price: NO contract price
            action_taken: What action was taken (traded, skipped_low_profit, etc.)
        """
        opportunities_file = self.log_dir / "opportunities.csv"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        price_sum = yes_price + no_price
        profit_pct = ((1.0 - price_sum) / price_sum) * 100
        
        with open(opportunities_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                timestamp, market, f"{yes_price:.3f}", f"{no_price:.3f}",
                f"{price_sum:.3f}", f"{profit_pct:.1f}", action_taken
            ])
    
    def log_error(self, message: str, level: str = "ERROR") -> None:
        """
        Log an error or warning message
        
        Args:
            message: Error message
            level: Severity level (ERROR, WARNING, CRITICAL)
        """
        errors_file = self.log_dir / "errors.log"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        with open(errors_file, 'a') as f:
            f.write(f"[{timestamp}] {level}: {message}\n")
    
    def log_warning(self, message: str) -> None:
        """Log a warning message"""
        self.log_error(message, level="WARNING")
    
    def log_critical(self, message: str) -> None:
        """Log a critical error message"""
        self.log_error(message, level="CRITICAL")
    
    def log_connection(self, status: str, response_time_ms: Optional[int] = None,
                      message: str = "") -> None:
        """
        Log connection health check
        
        Args:
            status: Connection status (healthy, slow, timeout)
            response_time_ms: Response time in milliseconds
            message: Additional message
        """
        connection_file = self.log_dir / "connection.log"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Choose icon based on status
        if status == "healthy":
            icon = "✓"
        elif status == "slow":
            icon = "⚠️"
        else:  # timeout or error
            icon = "🚨"
        
        # Format message
        if response_time_ms is not None:
            log_msg = f"[{timestamp}] {icon} Connection {status} - {response_time_ms}ms"
        else:
            log_msg = f"[{timestamp}] {icon} Connection {status}"
        
        if message:
            log_msg += f" - {message}"
        
        with open(connection_file, 'a') as f:
            f.write(log_msg + "\n")
    
    def get_recent_activities(self, count: int = 5) -> list:
        """
        Get recent activities from logs for dashboard display
        
        Args:
            count: Number of recent activities to retrieve
            
        Returns:
            List of recent activity strings
        """
        activities = []
        
        # Read recent opportunities
        opportunities_file = self.log_dir / "opportunities.csv"
        if opportunities_file.exists():
            with open(opportunities_file, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                # Get last N rows
                for row in rows[-count:]:
                    activities.append({
                        'timestamp': row['timestamp'],
                        'type': 'opportunity',
                        'data': row
                    })
        
        # Sort by timestamp and return most recent
        activities.sort(key=lambda x: x['timestamp'], reverse=True)
        return activities[:count]


# Singleton instance for easy access throughout the application
_logger_instance = None

def get_logger() -> Logger:
    """Get the global logger instance"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = Logger()
    return _logger_instance
