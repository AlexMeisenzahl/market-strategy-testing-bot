"""
Strategy Analytics Service

Calculate comprehensive performance metrics for each strategy.
CRITICAL: All money calculations use Decimal for accuracy.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from collections import defaultdict


class StrategyAnalytics:
    """Calculate comprehensive performance metrics for trading strategies"""

    def __init__(self, data_parser):
        """
        Initialize strategy analytics

        Args:
            data_parser: DataParser instance for accessing trade data
        """
        self.data_parser = data_parser

    def get_strategy_performance(
        self,
        strategy_name: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive performance metrics for a single strategy

        Args:
            strategy_name: Name of the strategy
            start_date: Start date filter (ISO format)
            end_date: End date filter (ISO format)

        Returns:
            Dictionary with 14+ performance metrics
        """
        # Get trades for this strategy
        trades_data = self.data_parser.get_trades(
            strategy=strategy_name,
            start_date=start_date,
            end_date=end_date,
            per_page=10000,  # Get all trades
        )
        trades = trades_data["trades"]

        if not trades:
            return self._empty_metrics(strategy_name)

        # Sort trades by entry time
        sorted_trades = sorted(trades, key=lambda t: t["entry_time"])

        # Calculate metrics
        return self._calculate_metrics(strategy_name, sorted_trades)

    def get_all_strategies_performance(
        self, start_date: Optional[str] = None, end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Calculate performance metrics for all strategies

        Args:
            start_date: Start date filter (ISO format)
            end_date: End date filter (ISO format)

        Returns:
            List of strategy performance dictionaries, sorted by total P&L descending
        """
        # Get all trades
        trades_data = self.data_parser.get_trades(
            start_date=start_date, end_date=end_date, per_page=10000  # Get all trades
        )
        all_trades = trades_data["trades"]

        # Group trades by strategy
        strategy_trades = defaultdict(list)
        for trade in all_trades:
            strategy_trades[trade["strategy"]].append(trade)

        # Calculate metrics for each strategy
        results = []
        for strategy_name, trades in strategy_trades.items():
            sorted_trades = sorted(trades, key=lambda t: t["entry_time"])
            metrics = self._calculate_metrics(strategy_name, sorted_trades)
            results.append(metrics)

        # Sort by total P&L descending
        results.sort(key=lambda x: float(x["total_pnl"]), reverse=True)

        return results

    def _calculate_metrics(
        self, strategy_name: str, trades: List[Dict]
    ) -> Dict[str, Any]:
        """Calculate all performance metrics for a strategy"""

        # Basic counts
        total_trades = len(trades)
        winning_trades = [t for t in trades if t["pnl_usd"] > 0]
        losing_trades = [t for t in trades if t["pnl_usd"] < 0]
        winning_count = len(winning_trades)
        losing_count = len(losing_trades)

        # Win rate
        win_rate = (
            (Decimal(winning_count) / Decimal(total_trades) * Decimal("100")).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            if total_trades > 0
            else Decimal("0")
        )

        # P&L calculations using Decimal
        total_pnl = sum(Decimal(str(t["pnl_usd"])) for t in trades)
        avg_profit = (
            (total_pnl / Decimal(total_trades)).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            if total_trades > 0
            else Decimal("0")
        )

        # Average win and loss
        avg_win = (
            (
                sum(Decimal(str(t["pnl_usd"])) for t in winning_trades)
                / Decimal(winning_count)
            ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            if winning_count > 0
            else Decimal("0")
        )

        avg_loss = (
            (
                sum(Decimal(str(t["pnl_usd"])) for t in losing_trades)
                / Decimal(losing_count)
            ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            if losing_count > 0
            else Decimal("0")
        )

        # Profit factor: Gross Profit / Gross Loss
        gross_profit = sum(Decimal(str(t["pnl_usd"])) for t in winning_trades)
        gross_loss = abs(sum(Decimal(str(t["pnl_usd"])) for t in losing_trades))

        if gross_loss == 0:
            profit_factor = float("inf") if gross_profit > 0 else Decimal("0")
        else:
            profit_factor = (gross_profit / gross_loss).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )

        # Largest win and loss
        largest_win = (
            max(Decimal(str(t["pnl_usd"])) for t in trades) if trades else Decimal("0")
        )
        largest_loss = (
            min(Decimal(str(t["pnl_usd"])) for t in trades) if trades else Decimal("0")
        )

        # Average trade duration in hours
        total_duration_minutes = sum(t["duration_minutes"] for t in trades)
        avg_duration_hours = (
            (
                Decimal(str(total_duration_minutes))
                / Decimal("60")
                / Decimal(total_trades)
            ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            if total_trades > 0
            else Decimal("0")
        )

        # Expectancy: (Win% × Avg Win) - (Loss% × Avg Loss)
        win_pct = win_rate / Decimal("100")
        loss_pct = Decimal("1") - win_pct
        expectancy = (win_pct * avg_win - loss_pct * abs(avg_loss)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        # Max consecutive wins and losses
        max_consecutive_wins = self._calculate_max_consecutive(trades, winning=True)
        max_consecutive_losses = self._calculate_max_consecutive(trades, winning=False)

        # Max drawdown
        max_drawdown = self._calculate_max_drawdown(trades)

        # Recovery factor: Net Profit / Max Drawdown
        if max_drawdown > 0:
            recovery_factor = (total_pnl / max_drawdown).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
        else:
            recovery_factor = Decimal("0")

        return {
            "strategy_name": strategy_name,
            "total_trades": total_trades,
            "winning_trades": winning_count,
            "losing_trades": losing_count,
            "win_rate": float(win_rate),
            "total_pnl": float(total_pnl),
            "avg_profit": float(avg_profit),
            "avg_win": float(avg_win),
            "avg_loss": float(avg_loss),
            "profit_factor": (
                float(profit_factor) if profit_factor != float("inf") else 999.99
            ),
            "largest_win": float(largest_win),
            "largest_loss": float(largest_loss),
            "avg_duration_hours": float(avg_duration_hours),
            "expectancy": float(expectancy),
            "max_consecutive_wins": max_consecutive_wins,
            "max_consecutive_losses": max_consecutive_losses,
            "max_drawdown": float(max_drawdown),
            "recovery_factor": float(recovery_factor),
        }

    def _calculate_max_consecutive(
        self, trades: List[Dict], winning: bool = True
    ) -> int:
        """
        Calculate maximum consecutive wins or losses

        Args:
            trades: List of trades sorted by time
            winning: True for consecutive wins, False for consecutive losses

        Returns:
            Maximum consecutive count
        """
        if not trades:
            return 0

        max_consecutive = 0
        current_consecutive = 0

        for trade in trades:
            is_win = trade["pnl_usd"] > 0

            if is_win == winning:
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 0

        return max_consecutive

    def _calculate_max_drawdown(self, trades: List[Dict]) -> Decimal:
        """
        Calculate maximum drawdown in dollar terms

        Args:
            trades: List of trades sorted by time

        Returns:
            Maximum drawdown as Decimal
        """
        if not trades:
            return Decimal("0")

        cumulative_pnl = Decimal("0")
        peak = Decimal("0")
        max_drawdown = Decimal("0")

        for trade in trades:
            cumulative_pnl += Decimal(str(trade["pnl_usd"]))

            # Update peak
            if cumulative_pnl > peak:
                peak = cumulative_pnl

            # Calculate drawdown from peak
            drawdown = peak - cumulative_pnl

            # Update max drawdown
            if drawdown > max_drawdown:
                max_drawdown = drawdown

        return max_drawdown

    def _empty_metrics(self, strategy_name: str) -> Dict[str, Any]:
        """Return empty metrics for a strategy with no trades"""
        return {
            "strategy_name": strategy_name,
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "win_rate": 0.0,
            "total_pnl": 0.0,
            "avg_profit": 0.0,
            "avg_win": 0.0,
            "avg_loss": 0.0,
            "profit_factor": 0.0,
            "largest_win": 0.0,
            "largest_loss": 0.0,
            "avg_duration_hours": 0.0,
            "expectancy": 0.0,
            "max_consecutive_wins": 0,
            "max_consecutive_losses": 0,
            "max_drawdown": 0.0,
            "recovery_factor": 0.0,
        }
