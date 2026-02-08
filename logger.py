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
            with open(trades_file, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(
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
        else:
            # Check if file needs migration (add new columns if missing)
            self._migrate_trades_csv(trades_file)

        # Initialize opportunities.csv
        opportunities_file = self.log_dir / "opportunities.csv"
        if not opportunities_file.exists():
            with open(opportunities_file, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(
                    [
                        "timestamp",
                        "market",
                        "yes_price",
                        "no_price",
                        "sum",
                        "profit_pct",
                        "action_taken",
                        "strategy",
                        "arbitrage_type",
                    ]
                )
        else:
            # Check if file needs migration
            self._migrate_opportunities_csv(opportunities_file)

    def _migrate_trades_csv(self, trades_file: Path) -> None:
        """Add strategy and arbitrage_type columns to existing trades.csv"""
        try:
            # Read existing data
            with open(trades_file, "r", newline="") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                fieldnames = reader.fieldnames or []

            # Check if migration needed
            if "strategy" in fieldnames and "arbitrage_type" in fieldnames:
                return  # Already migrated

            # Add new columns with default values
            new_fieldnames = list(fieldnames)
            if "strategy" not in new_fieldnames:
                new_fieldnames.append("strategy")
            if "arbitrage_type" not in new_fieldnames:
                new_fieldnames.append("arbitrage_type")

            # Rewrite file with new columns
            with open(trades_file, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=new_fieldnames)
                writer.writeheader()
                for row in rows:
                    if "strategy" not in row:
                        row["strategy"] = "Unknown"
                    if "arbitrage_type" not in row:
                        row["arbitrage_type"] = "Unknown"
                    writer.writerow(row)
        except Exception as e:
            # If migration fails, just log it and continue
            print(f"Warning: Could not migrate trades.csv: {e}")

    def _migrate_opportunities_csv(self, opportunities_file: Path) -> None:
        """Add strategy and arbitrage_type columns to existing opportunities.csv"""
        try:
            # Read existing data
            with open(opportunities_file, "r", newline="") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                fieldnames = reader.fieldnames or []

            # Check if migration needed
            if "strategy" in fieldnames and "arbitrage_type" in fieldnames:
                return  # Already migrated

            # Add new columns with default values
            new_fieldnames = list(fieldnames)
            if "strategy" not in new_fieldnames:
                new_fieldnames.append("strategy")
            if "arbitrage_type" not in new_fieldnames:
                new_fieldnames.append("arbitrage_type")

            # Rewrite file with new columns
            with open(opportunities_file, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=new_fieldnames)
                writer.writeheader()
                for row in rows:
                    if "strategy" not in row:
                        row["strategy"] = "Unknown"
                    if "arbitrage_type" not in row:
                        row["arbitrage_type"] = "Unknown"
                    writer.writerow(row)
        except Exception as e:
            # If migration fails, just log it and continue
            print(f"Warning: Could not migrate opportunities.csv: {e}")

    def log_trade(
        self,
        market: str,
        yes_price: float,
        no_price: float,
        profit_usd: float,
        status: str = "executed",
        strategy: str = "Unknown",
        arbitrage_type: str = "Unknown",
    ) -> None:
        """
        Log a paper trade execution

        Args:
            market: Market identifier
            yes_price: YES contract price
            no_price: NO contract price
            profit_usd: Expected profit in USD
            status: Trade status (executed, failed, etc.)
            strategy: Strategy name (e.g., 'polymarket_arbitrage')
            arbitrage_type: Type of arbitrage (e.g., 'Simple', 'Cross-Exchange')
        """
        trades_file = self.log_dir / "trades.csv"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        price_sum = yes_price + no_price
        profit_pct = ((1.0 - price_sum) / price_sum) * 100

        with open(trades_file, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    timestamp,
                    market,
                    f"{yes_price:.3f}",
                    f"{no_price:.3f}",
                    f"{price_sum:.3f}",
                    f"{profit_pct:.1f}",
                    f"{profit_usd:.2f}",
                    status,
                    strategy,
                    arbitrage_type,
                ]
            )

    def log_opportunity(
        self,
        market: str,
        yes_price: float,
        no_price: float,
        action_taken: str,
        strategy: str = "Unknown",
        arbitrage_type: str = "Unknown",
    ) -> None:
        """
        Log an arbitrage opportunity (traded or skipped)

        Args:
            market: Market identifier
            yes_price: YES contract price
            no_price: NO contract price
            action_taken: What action was taken (traded, skipped_low_profit, etc.)
            strategy: Strategy name (e.g., 'polymarket_arbitrage')
            arbitrage_type: Type of arbitrage (e.g., 'Simple', 'Cross-Exchange')
        """
        opportunities_file = self.log_dir / "opportunities.csv"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        price_sum = yes_price + no_price
        profit_pct = ((1.0 - price_sum) / price_sum) * 100

        with open(opportunities_file, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    timestamp,
                    market,
                    f"{yes_price:.3f}",
                    f"{no_price:.3f}",
                    f"{price_sum:.3f}",
                    f"{profit_pct:.1f}",
                    action_taken,
                    strategy,
                    arbitrage_type,
                ]
            )

    def log_error(self, message: str, level: str = "ERROR") -> None:
        """
        Log an error or warning message

        Args:
            message: Error message
            level: Severity level (ERROR, WARNING, CRITICAL)
        """
        errors_file = self.log_dir / "errors.log"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with open(errors_file, "a") as f:
            f.write(f"[{timestamp}] {level}: {message}\n")

    def log_warning(self, message: str) -> None:
        """Log a warning message"""
        self.log_error(message, level="WARNING")

    def log_critical(self, message: str) -> None:
        """Log a critical error message"""
        self.log_error(message, level="CRITICAL")

    def log_info(self, message: str) -> None:
        """Log an informational message"""
        self.log_error(message, level="INFO")

    def log_connection(
        self, status: str, response_time_ms: Optional[int] = None, message: str = ""
    ) -> None:
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

        with open(connection_file, "a") as f:
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
            with open(opportunities_file, "r") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                # Get last N rows
                for row in rows[-count:]:
                    activities.append(
                        {
                            "timestamp": row["timestamp"],
                            "type": "opportunity",
                            "data": row,
                        }
                    )

        # Sort by timestamp and return most recent
        activities.sort(key=lambda x: x["timestamp"], reverse=True)
        return activities[:count]


# Singleton instance for easy access throughout the application
_logger_instance = None


def get_logger() -> Logger:
    """Get the global logger instance"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = Logger()
    return _logger_instance
