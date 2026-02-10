"""
Data Flow Manager - Read-only consumer of execution state

Provides portfolio/trade data to the dashboard. Does NOT execute trades or
mutate portfolio state. When an ExecutionEngine is set (e.g. by BotRunner),
state is read from the engine; otherwise falls back to existing trackers.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

from logger import get_logger
from services.portfolio_tracker import PortfolioTracker
from services.trade_logger import TradeLogger


class DataFlowManager:
    """Read-only data flow: consumes execution state from ExecutionEngine when set."""

    _instance = None  # Singleton instance

    def __new__(cls, *args, **kwargs):
        """Ensure singleton instance"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize data flow manager

        Args:
            config: Configuration dictionary
        """
        # Only initialize once
        if hasattr(self, "_initialized"):
            return

        self.logger = get_logger()
        self.config = config or {}

        # Optional: set by BotRunner so dashboard reads from single execution engine
        self._execution_engine = None

        # Fallback when no engine set (e.g. standalone dashboard, demos)
        initial_balance = self.config.get("initial_capital", 10000.0)
        self.portfolio_tracker = PortfolioTracker(initial_balance=initial_balance)
        self.trade_logger = TradeLogger()

        # Dashboard cache for WebSocket broadcasting
        self.dashboard_cache = {
            "portfolio": {},
            "trades": [],
            "strategies": {},
            "alerts": [],
        }

        self._initialized = True
        self.logger.log_info("DataFlowManager initialized (read-only; no execution)")

    def set_execution_engine(self, engine: Any) -> None:
        """Set the single execution engine; get_* methods will read from it (read-only)."""
        self._execution_engine = engine

    def process_signal(
        self, strategy_name: str, signal: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        No-op: DataFlowManager does not execute trades or mutate portfolio state.
        Execution is done only by the single ExecutionEngine (via StrategyManager).
        Kept for API compatibility; callers should not rely on this to execute.
        """
        return None

    def execute_signal(self, signal: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        No-op: DataFlowManager does not execute. Kept for API compatibility.
        """
        return None

    def refresh_dashboard_cache_from_engine(self) -> None:
        """
        Refresh dashboard cache from ExecutionEngine (read-only).
        Call after bot cycle so dashboard/WebSocket show current state.
        """
        if not self._execution_engine:
            return
        try:
            self.dashboard_cache["portfolio"] = self.get_portfolio_summary()
            self.dashboard_cache["trades"] = self.get_recent_trades(100)
        except Exception as e:
            self.logger.log_error(f"Error refreshing dashboard cache from engine: {e}")

    def update_dashboard_cache(self, strategy_name: str, trade: Dict[str, Any]):
        """
        No-op: no longer mutates cache from new trades.
        Use refresh_dashboard_cache_from_engine() to pull from ExecutionEngine.
        Kept for API compatibility.
        """
        pass

    def _broadcast_update(self, trade: Dict[str, Any]):
        """
        No-op: no longer pushes individual trades (no execution here).
        Use refresh_dashboard_cache_from_engine() then broadcast cache if needed.
        Kept for API compatibility.
        """
        pass

    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get current portfolio summary (from ExecutionEngine when set, else fallback)."""
        if self._execution_engine:
            return self._portfolio_summary_from_engine()
        return self.portfolio_tracker.get_summary()

    def _portfolio_summary_from_engine(self) -> Dict[str, Any]:
        """Build portfolio summary from ExecutionEngine (read-only)."""
        engine = self._execution_engine
        cash = engine.get_balance()
        positions = engine.get_positions({})
        position_value = sum(
            p.get("current_value") or (p.get("quantity", 0) * p.get("avg_price", 0))
            for p in positions
        )
        total_value = cash + position_value
        initial = engine.trading_engine.initial_balance
        total_return = total_value - initial
        total_return_pct = (total_return / initial * 100) if initial else 0
        trades = engine.get_trade_history()
        return {
            "cash": cash,
            "total_value": total_value,
            "initial_balance": initial,
            "total_return": total_return,
            "total_return_pct": total_return_pct,
            "positions_count": len(positions),
            "trades_count": len(trades),
        }

    def get_recent_trades(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent trades (from ExecutionEngine when set, else fallback)."""
        if self._execution_engine:
            return self._execution_engine.get_trade_history()[-limit:]
        return self.trade_logger.get_recent_trades(limit)

    def get_all_trades(self) -> list:
        """Get all trades (from ExecutionEngine when set, else fallback)."""
        if self._execution_engine:
            return self._execution_engine.get_trade_history()
        return self.trade_logger.get_all_trades()

    def get_strategy_stats(self, strategy_name: str) -> Dict[str, Any]:
        """Get stats (from engine trade history when set; strategy name not in engine data)."""
        if self._execution_engine:
            trades = self._execution_engine.get_trade_history()
            if not trades:
                return {"total_trades": 0, "total_pnl": 0, "win_rate": 0}
            pnls = [t.get("realized_pnl", 0) for t in trades]
            total_pnl = sum(pnls)
            winning = sum(1 for p in pnls if p > 0)
            return {
                "total_trades": len(trades),
                "winning_trades": winning,
                "losing_trades": len(trades) - winning,
                "win_rate": (winning / len(trades) * 100) if trades else 0,
                "total_pnl": total_pnl,
                "avg_pnl": total_pnl / len(trades),
            }
        trades = self.trade_logger.get_trades_by_strategy(strategy_name)
        if not trades:
            return {"total_trades": 0, "total_pnl": 0, "win_rate": 0}
        winning = [t for t in trades if t.get("pnl", 0) > 0]
        total_pnl = sum(t.get("pnl", 0) for t in trades)
        return {
            "total_trades": len(trades),
            "winning_trades": len(winning),
            "losing_trades": len(trades) - len(winning),
            "win_rate": len(winning) / len(trades) * 100,
            "total_pnl": total_pnl,
            "avg_pnl": total_pnl / len(trades),
        }
