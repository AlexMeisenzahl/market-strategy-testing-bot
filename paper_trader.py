"""
Paper Trader Module - Simulate trades without real money

Tracks hypothetical trades and calculates P&L
All trades are simulated - NO REAL MONEY IS USED
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from detector import ArbitrageOpportunity
from logger import get_logger


class PaperTrade:
    """Represents a single paper trade"""

    def __init__(self, opportunity: ArbitrageOpportunity, trade_size: float):
        """
        Initialize paper trade

        Args:
            opportunity: Arbitrage opportunity being traded
            trade_size: Size of trade in USD
        """
        self.opportunity = opportunity
        self.trade_size = trade_size
        self.executed_at = datetime.now()

        # Calculate trade details
        self.yes_cost = trade_size * opportunity.yes_price
        self.no_cost = trade_size * opportunity.no_price
        self.total_cost = self.yes_cost + self.no_cost
        self.expected_return = trade_size  # Always pays out full amount
        self.expected_profit = self.expected_return - self.total_cost

        # Status
        self.status = "executed"

    @property
    def profit_percentage(self) -> float:
        """Calculate profit as percentage of investment"""
        if self.total_cost == 0:
            return 0.0
        return (self.expected_profit / self.total_cost) * 100

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging"""
        return {
            "market_id": self.opportunity.market_id,
            "market_name": self.opportunity.market_name,
            "yes_price": self.opportunity.yes_price,
            "no_price": self.opportunity.no_price,
            "trade_size": self.trade_size,
            "total_cost": self.total_cost,
            "expected_return": self.expected_return,
            "expected_profit": self.expected_profit,
            "profit_percentage": self.profit_percentage,
            "executed_at": self.executed_at.isoformat(),
            "status": self.status,
        }


class PaperTrader:
    """Paper trading simulator - NO REAL MONEY"""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize paper trader

        Args:
            config: Configuration dictionary from config.yaml
        """
        self.config = config
        self.logger = get_logger()

        # Trading parameters
        self.max_trade_size = config.get("max_trade_size", 10)
        self.max_trades_per_hour = config.get("max_trades_per_hour", 10)

        # Track trades
        self.trades = []
        self.trades_this_hour = []

        # Track P&L
        self.total_profit = 0.0
        self.total_invested = 0.0
        self.trades_executed = 0

        # Safety check
        if not config.get("paper_trading", True):
            self.logger.log_critical(
                "Paper trading is disabled in config! This should NEVER happen!"
            )
            raise ValueError("Paper trading must be enabled")

    def can_trade(self) -> bool:
        """
        Check if trading is allowed based on rate limits

        Returns:
            True if trade can be executed
        """
        # Clean old trades from hourly counter
        self._clean_hourly_trades()

        # Check hourly limit
        if len(self.trades_this_hour) >= self.max_trades_per_hour:
            return False

        return True

    def execute_paper_trade(
        self, opportunity: ArbitrageOpportunity
    ) -> Optional[PaperTrade]:
        """
        Execute a paper trade (simulated)

        Args:
            opportunity: Arbitrage opportunity to trade

        Returns:
            PaperTrade object if successful, None if failed
        """
        # Check if we can trade
        if not self.can_trade():
            self.logger.log_warning(
                f"Cannot trade - hourly limit reached ({self.max_trades_per_hour})"
            )
            return None

        # Phase 7A: Execution gate (no trade when paused, killed, or not paper-only)
        try:
            from services.execution_gate import may_execute_trade
            allowed, reason = may_execute_trade(self.config)
            if not allowed:
                self.logger.log_warning(f"Execution gate closed: {reason}")
                return None
        except Exception as e:
            self.logger.log_error(f"Execution gate check failed: {e}")
            return None

        # Validate opportunity is still fresh
        if not opportunity.is_valid():
            self.logger.log_warning(
                f"Skipping stale opportunity: {opportunity.market_name}"
            )
            return None

        try:
            # Create paper trade
            trade = PaperTrade(opportunity=opportunity, trade_size=self.max_trade_size)

            # Record the trade
            self.trades.append(trade)
            self.trades_this_hour.append(datetime.now())

            # Update totals
            self.total_profit += trade.expected_profit
            self.total_invested += trade.total_cost
            self.trades_executed += 1

            # Log the trade
            self.logger.log_trade(
                market=opportunity.market_name,
                yes_price=opportunity.yes_price,
                no_price=opportunity.no_price,
                profit_usd=trade.expected_profit,
                status="executed",
            )

            self.logger.log_opportunity(
                market=opportunity.market_name,
                yes_price=opportunity.yes_price,
                no_price=opportunity.no_price,
                action_taken="traded",
            )

            return trade

        except Exception as e:
            self.logger.log_error(f"Error executing paper trade: {str(e)}")
            return None

    def _clean_hourly_trades(self) -> None:
        """Remove trades older than 1 hour from counter"""
        from datetime import timedelta

        cutoff_time = datetime.now() - timedelta(hours=1)
        self.trades_this_hour = [t for t in self.trades_this_hour if t > cutoff_time]

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get trading statistics for dashboard

        Returns:
            Dictionary with trading statistics
        """
        return_pct = 0.0
        if self.total_invested > 0:
            return_pct = (self.total_profit / self.total_invested) * 100

        return {
            "trades_executed": self.trades_executed,
            "total_profit": self.total_profit,
            "total_invested": self.total_invested,
            "return_percentage": return_pct,
            "trades_this_hour": len(self.trades_this_hour),
            "can_trade": self.can_trade(),
        }

    def get_recent_trades(self, count: int = 5) -> List[PaperTrade]:
        """
        Get most recent paper trades

        Args:
            count: Number of trades to return

        Returns:
            List of recent PaperTrade objects
        """
        return self.trades[-count:] if self.trades else []

    def reset_statistics(self) -> None:
        """Reset all statistics (use carefully)"""
        self.trades = []
        self.trades_this_hour = []
        self.total_profit = 0.0
        self.total_invested = 0.0
        self.trades_executed = 0
        self.logger.log_warning("Paper trading statistics reset")
