"""
Logger Module - Structured logging for the arbitrage bot

Creates and manages log files:
- logs/trades.csv: Paper trade executions
- logs/opportunities.csv: All arbitrage opportunities found
- logs/errors.log: Error and warning messages
- logs/connection.log: Connection health monitoring

Log level is configurable via environment variable LOG_LEVEL (DEBUG, INFO, WARNING, ERROR, CRITICAL).
Default: INFO.
"""

import csv
import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Dict, Any, Optional
from pathlib import Path

try:
    from database.trades_store import (
        init_db as init_trades_db,
        insert_trade as store_insert_trade,
        insert_opportunity as store_insert_opportunity,
        migrate_csv_to_db as migrate_trades_csv,
        migrate_opportunities_csv_to_db as migrate_opportunities_csv,
        get_opportunities as store_get_opportunities,
    )
except ImportError:
    init_trades_db = None
    store_insert_trade = None
    store_insert_opportunity = None
    migrate_trades_csv = None
    migrate_opportunities_csv = None
    store_get_opportunities = None

# Configurable minimum log level (from env LOG_LEVEL)
_LEVELS = {"DEBUG": 10, "INFO": 20, "WARNING": 30, "ERROR": 40, "CRITICAL": 50}


def _min_level() -> int:
    return _LEVELS.get(
        (os.environ.get("LOG_LEVEL") or "INFO").upper(),
        20,
    )


class Logger:
    """Central logging system for all bot activities"""

    # Rotating log limits (prevent unbounded growth)
    ROTATE_MAX_BYTES = 10 * 1024 * 1024  # 10MB
    ROTATE_BACKUP_COUNT = 5

    def __init__(self, log_dir: str = "logs"):
        """
        Initialize logger with automatic log directory creation.
        errors.log and connection.log use RotatingFileHandler (10MB, 5 backups).
        """
        self.log_dir = Path(log_dir)
        self._ensure_log_directory()
        self._initialize_csv_files()
        self._init_rotating_handlers()

    def _ensure_log_directory(self) -> None:
        """Create logs directory if it doesn't exist"""
        self.log_dir.mkdir(exist_ok=True)

    def _init_rotating_handlers(self) -> None:
        """Set up RotatingFileHandler for errors.log and connection.log."""
        fmt = logging.Formatter(
            "[%(asctime)s] %(levelname)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        errors_file = self.log_dir / "errors.log"
        self._errors_handler = RotatingFileHandler(
            errors_file,
            maxBytes=self.ROTATE_MAX_BYTES,
            backupCount=self.ROTATE_BACKUP_COUNT,
            encoding="utf-8",
        )
        self._errors_handler.setFormatter(fmt)
        conn_file = self.log_dir / "connection.log"
        self._connection_handler = RotatingFileHandler(
            conn_file,
            maxBytes=self.ROTATE_MAX_BYTES,
            backupCount=self.ROTATE_BACKUP_COUNT,
            encoding="utf-8",
        )
        self._connection_handler.setFormatter(fmt)

    def _initialize_csv_files(self) -> None:
        """Initialize SQLite store (primary) and legacy CSV headers if needed for migration."""
        if init_trades_db is not None:
            init_trades_db(self.log_dir)
            if migrate_trades_csv is not None:
                migrate_trades_csv(self.log_dir)
            if migrate_opportunities_csv is not None:
                migrate_opportunities_csv(self.log_dir)
        # Keep CSV headers for backward compatibility (e.g. manual inspection); writes go to SQLite
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
            self._migrate_trades_csv(trades_file)
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
            # If migration fails, log and continue (no logger yet if early in init)
            import sys
            sys.stderr.write(f"Warning: Could not migrate trades.csv: {e}\n")

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
            # If migration fails, log and continue (no logger yet if early in init)
            import sys
            sys.stderr.write(f"Warning: Could not migrate opportunities.csv: {e}\n")

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
        Log a paper trade execution (SQLite primary; no unbounded CSV append).

        Args:
            market: Market identifier
            yes_price: YES contract price
            no_price: NO contract price
            profit_usd: Expected profit in USD
            status: Trade status (executed, failed, etc.)
            strategy: Strategy name (e.g., 'polymarket_arbitrage')
            arbitrage_type: Type of arbitrage (e.g., 'Simple', 'Cross-Exchange')
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        price_sum = yes_price + no_price
        profit_pct = ((1.0 - price_sum) / price_sum) * 100 if price_sum else 0.0
        if store_insert_trade is not None:
            store_insert_trade(
                self.log_dir,
                timestamp=timestamp,
                market=market,
                yes_price=yes_price,
                no_price=no_price,
                profit_pct=profit_pct,
                profit_usd=profit_usd,
                status=status,
                strategy=strategy,
                arbitrage_type=arbitrage_type,
            )
        else:
            trades_file = self.log_dir / "trades.csv"
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
        Log an arbitrage opportunity (SQLite primary; no unbounded CSV append).

        Args:
            market: Market identifier
            yes_price: YES contract price
            no_price: NO contract price
            action_taken: What action was taken (traded, skipped_low_profit, etc.)
            strategy: Strategy name (e.g., 'polymarket_arbitrage')
            arbitrage_type: Type of arbitrage (e.g., 'Simple', 'Cross-Exchange')
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        price_sum = yes_price + no_price
        profit_pct = ((1.0 - price_sum) / price_sum) * 100 if price_sum else 0.0
        if store_insert_opportunity is not None:
            store_insert_opportunity(
                self.log_dir,
                timestamp=timestamp,
                market=market,
                yes_price=yes_price,
                no_price=no_price,
                profit_pct=profit_pct,
                action_taken=action_taken,
                strategy=strategy,
                arbitrage_type=arbitrage_type,
            )
        else:
            opportunities_file = self.log_dir / "opportunities.csv"
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
        Log an error or warning message via RotatingFileHandler (max 10MB, 5 backups).

        Respects LOG_LEVEL environment variable: only writes if level is at or above configured minimum.

        Args:
            message: Error message
            level: Severity level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        level_num = _LEVELS.get(level.upper(), 40)
        if level_num < _min_level():
            return
        record = logging.LogRecord(
            name="market_bot",
            level=level_num,
            pathname="",
            lineno=0,
            msg=message,
            args=(),
            exc_info=None,
        )
        self._errors_handler.emit(record)

    def log_warning(self, message: str) -> None:
        """Log a warning message"""
        self.log_error(message, level="WARNING")

    def log_critical(self, message: str) -> None:
        """Log a critical error message"""
        self.log_error(message, level="CRITICAL")

    def log_info(self, message: str) -> None:
        """Log an informational message"""
        self.log_error(message, level="INFO")

    # Standard Python logging-style method aliases
    def info(self, message: str) -> None:
        """Alias for log_info for compatibility with standard logging"""
        self.log_info(message)

    def error(self, message: str) -> None:
        """Alias for log_error for compatibility with standard logging"""
        self.log_error(message, level="ERROR")

    def warning(self, message: str) -> None:
        """Alias for log_warning for compatibility with standard logging"""
        self.log_warning(message)

    def debug(self, message: str) -> None:
        """Alias for log_info with DEBUG level for compatibility with standard logging"""
        self.log_error(message, level="DEBUG")

    def exception(self, message: str, *args) -> None:
        """Log an error with exception traceback (compatible with standard logging)."""
        import traceback
        full = message % args if args else message
        full += "\n" + traceback.format_exc()
        self.log_error(full, level="ERROR")

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

        record = logging.LogRecord(
            name="market_bot.connection",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg=log_msg,
            args=(),
            exc_info=None,
        )
        self._connection_handler.emit(record)

    def log_logs_disk_usage(self) -> None:
        """
        Log total disk usage of the logs directory (for 6+ month unattended monitoring).
        Call periodically from run_bot or dashboard.
        """
        try:
            total = 0
            for p in self.log_dir.rglob("*"):
                if p.is_file():
                    try:
                        total += p.stat().st_size
                    except OSError:
                        pass
            size_mb = total / (1024 * 1024)
            self.log_info(
                f"Logs dir disk usage: {size_mb:.2f} MB ({self.log_dir})"
            )
        except Exception as e:
            self.log_error(f"Logs disk usage check failed: {e}")

    def get_recent_activities(self, count: int = 5) -> list:
        """
        Get recent activities from SQLite or CSV for dashboard display.

        Args:
            count: Number of recent activities to retrieve

        Returns:
            List of recent activity dicts (timestamp, type, data)
        """
        if store_get_opportunities is not None:
            opps = store_get_opportunities(self.log_dir, limit=count, offset=0)
            return [
                {"timestamp": o.get("timestamp", ""), "type": "opportunity", "data": o}
                for o in opps
            ]
        activities = []
        opportunities_file = self.log_dir / "opportunities.csv"
        if opportunities_file.exists():
            with open(opportunities_file, "r") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                for row in rows[-count:]:
                    activities.append(
                        {
                            "timestamp": row.get("timestamp", ""),
                            "type": "opportunity",
                            "data": row,
                        }
                    )
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
