"""
Market Analytics Service

Analyze performance by individual market.
CRITICAL: All money calculations use Decimal for accuracy.
"""

from typing import Dict, List, Any, Optional
from decimal import Decimal, ROUND_HALF_UP
from collections import defaultdict


class MarketAnalytics:
    """Calculate performance metrics by market (symbol)"""

    def __init__(self, data_parser):
        """
        Initialize market analytics

        Args:
            data_parser: DataParser instance for accessing trade data
        """
        self.data_parser = data_parser

    def get_market_performance(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        min_trades: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        Analyze performance by individual market

        Args:
            start_date: Start date filter (ISO format)
            end_date: End date filter (ISO format)
            min_trades: Minimum number of trades to include a market (default 3)

        Returns:
            List of market performance dictionaries
        """
        # Get all trades
        trades_data = self.data_parser.get_trades(
            start_date=start_date, end_date=end_date, per_page=10000  # Get all trades
        )
        all_trades = trades_data["trades"]
        total_trade_count = len(all_trades)

        # Group trades by market (symbol)
        market_trades = defaultdict(list)
        for trade in all_trades:
            market_trades[trade["symbol"]].append(trade)

        # Calculate metrics for each market
        results = []
        for market_name, trades in market_trades.items():
            # Filter out markets with too few trades
            if len(trades) < min_trades:
                continue

            metrics = self._calculate_market_metrics(
                market_name, trades, total_trade_count
            )
            results.append(metrics)

        return results

    def get_top_markets(
        self,
        n: int = 10,
        metric: str = "total_pnl",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get top N markets by specified metric

        Args:
            n: Number of top markets to return
            metric: Metric to sort by (total_pnl, win_rate, frequency, success_score)
            start_date: Start date filter
            end_date: End date filter

        Returns:
            List of top N market dictionaries
        """
        markets = self.get_market_performance(start_date, end_date)

        # Sort by metric descending
        sorted_markets = sorted(markets, key=lambda x: x[metric], reverse=True)

        return sorted_markets[:n]

    def get_worst_markets(
        self,
        n: int = 10,
        metric: str = "total_pnl",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get worst N markets by specified metric

        Args:
            n: Number of worst markets to return
            metric: Metric to sort by (total_pnl, win_rate, frequency, success_score)
            start_date: Start date filter
            end_date: End date filter

        Returns:
            List of worst N market dictionaries
        """
        markets = self.get_market_performance(start_date, end_date)

        # Sort by metric ascending
        sorted_markets = sorted(markets, key=lambda x: x[metric])

        return sorted_markets[:n]

    def _calculate_market_metrics(
        self, market_name: str, trades: List[Dict], total_trade_count: int
    ) -> Dict[str, Any]:
        """Calculate performance metrics for a single market"""

        # Basic counts
        total_trades = len(trades)
        winning_trades = [t for t in trades if t["pnl_usd"] > 0]
        winning_count = len(winning_trades)

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

        # Best and worst trades
        best_trade = (
            max(Decimal(str(t["pnl_usd"])) for t in trades) if trades else Decimal("0")
        )
        worst_trade = (
            min(Decimal(str(t["pnl_usd"])) for t in trades) if trades else Decimal("0")
        )

        # Frequency: (market_trades / total_trades) × 100
        frequency = (
            (
                Decimal(total_trades) / Decimal(total_trade_count) * Decimal("100")
            ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            if total_trade_count > 0
            else Decimal("0")
        )

        # Success Score: (win_rate/100) × total_pnl × (frequency/100)
        success_score = (
            (win_rate / Decimal("100")) * total_pnl * (frequency / Decimal("100"))
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        return {
            "market": market_name,
            "total_trades": total_trades,
            "win_rate": float(win_rate),
            "total_pnl": float(total_pnl),
            "avg_profit": float(avg_profit),
            "best_trade": float(best_trade),
            "worst_trade": float(worst_trade),
            "frequency": float(frequency),
            "success_score": float(success_score),
        }
