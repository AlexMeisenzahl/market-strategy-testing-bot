"""
DEPRECATED FOR LIVE EXECUTION.

This module is NOT the source of truth for live trading.
Live execution state lives in ExecutionEngine -> PaperTradingEngine.

This module may be used for:
- legacy paths
- reporting
- backtests
- dashboard fallback
"""

"""
Trade Logger - Trade History and Analytics

Logs all trades with timestamps and provides analytics.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from pathlib import Path
import json
import csv
from io import StringIO

from logger import get_logger


class TradeLogger:
    """Logs and manages trade history"""

    def __init__(self):
        """Initialize trade logger"""
        self.logger = get_logger()
        self.data_file = Path("data/trades.json")
        self.data_file.parent.mkdir(exist_ok=True)
        self.trades = []

        # Load existing trades
        self._load_trades()

    def _load_trades(self):
        """Load trades from disk"""
        try:
            if self.data_file.exists():
                with open(self.data_file, "r") as f:
                    self.trades = json.load(f)
                    self.logger.log_info(f"Loaded {len(self.trades)} historical trades")
        except Exception as e:
            self.logger.log_error(f"Failed to load trades: {e}")
            self.trades = []

    def _save_trades(self):
        """Save trades to disk"""
        try:
            with open(self.data_file, "w") as f:
                json.dump(self.trades[-10000:], f, indent=2)  # Keep last 10k trades
        except Exception as e:
            self.logger.log_error(f"Failed to save trades: {e}")

    def log(self, trade: Dict[str, Any]):
        """
        Log a trade

        Args:
            trade: Trade dictionary with required fields
        """
        # Add timestamp if not present
        if "timestamp" not in trade:
            trade["timestamp"] = datetime.now(timezone.utc).isoformat()

        # Add to trades list
        self.trades.append(trade)

        # Save to disk
        self._save_trades()

        self.logger.log_info(
            f"Trade logged: {trade.get('side')} {trade.get('quantity')} "
            f"{trade.get('symbol')} @ {trade.get('price')}"
        )

    def get_recent_trades(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get recent trades

        Args:
            limit: Maximum number of trades to return

        Returns:
            List of trade dictionaries
        """
        return self.trades[-limit:]

    def get_all_trades(self) -> List[Dict[str, Any]]:
        """
        Get all trades

        Returns:
            List of all trade dictionaries
        """
        return self.trades

    def get_trades_by_strategy(self, strategy_name: str) -> List[Dict[str, Any]]:
        """
        Get trades for a specific strategy

        Args:
            strategy_name: Name of strategy

        Returns:
            List of trade dictionaries for strategy
        """
        return [t for t in self.trades if t.get("strategy") == strategy_name]

    def get_trade_stats(self) -> Dict[str, Any]:
        """
        Get trade statistics

        Returns:
            Dictionary with trade stats
        """
        if not self.trades:
            return {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0,
                "total_pnl": 0,
                "avg_pnl": 0,
            }

        winning_trades = [t for t in self.trades if t.get("pnl", 0) > 0]
        losing_trades = [t for t in self.trades if t.get("pnl", 0) < 0]
        total_pnl = sum(t.get("pnl", 0) for t in self.trades)

        return {
            "total_trades": len(self.trades),
            "winning_trades": len(winning_trades),
            "losing_trades": len(losing_trades),
            "win_rate": (
                len(winning_trades) / len(self.trades) * 100 if self.trades else 0
            ),
            "total_pnl": total_pnl,
            "avg_pnl": total_pnl / len(self.trades) if self.trades else 0,
            "avg_win": (
                sum(t.get("pnl", 0) for t in winning_trades) / len(winning_trades)
                if winning_trades
                else 0
            ),
            "avg_loss": (
                sum(t.get("pnl", 0) for t in losing_trades) / len(losing_trades)
                if losing_trades
                else 0
            ),
        }

    def export_to_csv(self) -> str:
        """
        Export trades to CSV format

        Returns:
            CSV string
        """
        if not self.trades:
            return ""

        output = StringIO()

        # Get all unique keys from trades
        fieldnames = set()
        for trade in self.trades:
            fieldnames.update(trade.keys())
        fieldnames = sorted(fieldnames)

        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(self.trades)

        return output.getvalue()
