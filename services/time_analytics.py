"""
Time Analytics Service

Analyze when trades perform best (hour of day, day of week, monthly).
CRITICAL: All money calculations use Decimal for accuracy.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from collections import defaultdict


class TimeAnalytics:
    """Calculate time-based performance analytics"""

    def __init__(self, data_parser):
        """
        Initialize time analytics

        Args:
            data_parser: DataParser instance for accessing trade data
        """
        self.data_parser = data_parser

    def get_hour_of_day_analysis(
        self, start_date: Optional[str] = None, end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze performance by hour of day (0-23)

        Args:
            start_date: Start date filter (ISO format)
            end_date: End date filter (ISO format)

        Returns:
            Dictionary with hourly analysis data
        """
        # Get all trades
        trades_data = self.data_parser.get_trades(
            start_date=start_date, end_date=end_date, per_page=10000  # Get all trades
        )
        trades = trades_data["trades"]

        # Group trades by hour
        hourly_trades = defaultdict(list)
        for trade in trades:
            try:
                entry_time = datetime.fromisoformat(trade["entry_time"])
                hour = entry_time.hour  # 0-23
                hourly_trades[hour].append(trade)
            except (ValueError, KeyError):
                continue

        # Calculate metrics for each hour
        hours = list(range(24))
        trades_per_hour = []
        pnl_per_hour = []
        win_rate_per_hour = []
        avg_profit_per_hour = []

        for hour in hours:
            hour_trades = hourly_trades.get(hour, [])

            if hour_trades:
                # Calculate metrics
                trade_count = len(hour_trades)
                winning_count = len([t for t in hour_trades if t["pnl_usd"] > 0])
                win_rate = float(
                    (
                        Decimal(winning_count) / Decimal(trade_count) * Decimal("100")
                    ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                )

                total_pnl = float(sum(Decimal(str(t["pnl_usd"])) for t in hour_trades))
                avg_profit = float(
                    (Decimal(str(total_pnl)) / Decimal(trade_count)).quantize(
                        Decimal("0.01"), rounding=ROUND_HALF_UP
                    )
                )

                trades_per_hour.append(trade_count)
                pnl_per_hour.append(total_pnl)
                win_rate_per_hour.append(win_rate)
                avg_profit_per_hour.append(avg_profit)
            else:
                trades_per_hour.append(0)
                pnl_per_hour.append(0.0)
                win_rate_per_hour.append(0.0)
                avg_profit_per_hour.append(0.0)

        return {
            "hours": hours,
            "trades_per_hour": trades_per_hour,
            "pnl_per_hour": pnl_per_hour,
            "win_rate_per_hour": win_rate_per_hour,
            "avg_profit_per_hour": avg_profit_per_hour,
        }

    def get_day_of_week_analysis(
        self, start_date: Optional[str] = None, end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze performance by day of week (Monday-Sunday)

        Args:
            start_date: Start date filter (ISO format)
            end_date: End date filter (ISO format)

        Returns:
            Dictionary with daily analysis data
        """
        # Get all trades
        trades_data = self.data_parser.get_trades(
            start_date=start_date, end_date=end_date, per_page=10000  # Get all trades
        )
        trades = trades_data["trades"]

        # Group trades by day of week
        daily_trades = defaultdict(list)
        for trade in trades:
            try:
                entry_time = datetime.fromisoformat(trade["entry_time"])
                day = entry_time.weekday()  # 0=Monday, 6=Sunday
                daily_trades[day].append(trade)
            except (ValueError, KeyError):
                continue

        # Calculate metrics for each day
        days = list(range(7))
        day_names = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]
        trades_per_day = []
        pnl_per_day = []
        win_rate_per_day = []
        avg_profit_per_day = []

        for day in days:
            day_trades = daily_trades.get(day, [])

            if day_trades:
                # Calculate metrics
                trade_count = len(day_trades)
                winning_count = len([t for t in day_trades if t["pnl_usd"] > 0])
                win_rate = float(
                    (
                        Decimal(winning_count) / Decimal(trade_count) * Decimal("100")
                    ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                )

                total_pnl = float(sum(Decimal(str(t["pnl_usd"])) for t in day_trades))
                avg_profit = float(
                    (Decimal(str(total_pnl)) / Decimal(trade_count)).quantize(
                        Decimal("0.01"), rounding=ROUND_HALF_UP
                    )
                )

                trades_per_day.append(trade_count)
                pnl_per_day.append(total_pnl)
                win_rate_per_day.append(win_rate)
                avg_profit_per_day.append(avg_profit)
            else:
                trades_per_day.append(0)
                pnl_per_day.append(0.0)
                win_rate_per_day.append(0.0)
                avg_profit_per_day.append(0.0)

        return {
            "days": days,
            "day_names": day_names,
            "trades_per_day": trades_per_day,
            "pnl_per_day": pnl_per_day,
            "win_rate_per_day": win_rate_per_day,
            "avg_profit_per_day": avg_profit_per_day,
        }

    def get_monthly_performance(
        self, start_date: Optional[str] = None, end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Analyze performance by month

        Args:
            start_date: Start date filter (ISO format)
            end_date: End date filter (ISO format)

        Returns:
            List of monthly performance dictionaries
        """
        # Get all trades
        trades_data = self.data_parser.get_trades(
            start_date=start_date, end_date=end_date, per_page=10000  # Get all trades
        )
        trades = trades_data["trades"]

        # Group trades by month
        monthly_trades = defaultdict(list)
        for trade in trades:
            try:
                entry_time = datetime.fromisoformat(trade["entry_time"])
                month_key = entry_time.strftime("%Y-%m")
                monthly_trades[month_key].append(trade)
            except (ValueError, KeyError):
                continue

        # Calculate metrics for each month
        results = []
        for month_key in sorted(monthly_trades.keys()):
            month_trades = monthly_trades[month_key]

            trade_count = len(month_trades)
            winning_count = len([t for t in month_trades if t["pnl_usd"] > 0])
            win_rate = (
                float(
                    (
                        Decimal(winning_count) / Decimal(trade_count) * Decimal("100")
                    ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                )
                if trade_count > 0
                else 0.0
            )

            total_pnl = float(sum(Decimal(str(t["pnl_usd"])) for t in month_trades))
            avg_profit = (
                float(
                    (Decimal(str(total_pnl)) / Decimal(trade_count)).quantize(
                        Decimal("0.01"), rounding=ROUND_HALF_UP
                    )
                )
                if trade_count > 0
                else 0.0
            )

            results.append(
                {
                    "month": month_key,
                    "total_trades": trade_count,
                    "winning_trades": winning_count,
                    "win_rate": win_rate,
                    "total_pnl": total_pnl,
                    "avg_profit": avg_profit,
                }
            )

        return results

    def get_best_trading_times(
        self, start_date: Optional[str] = None, end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Identify the best trading times by P&L

        Args:
            start_date: Start date filter
            end_date: End date filter

        Returns:
            Dictionary with top 5 hours and top 3 days by P&L
        """
        # Get hour and day analysis
        hour_analysis = self.get_hour_of_day_analysis(start_date, end_date)
        day_analysis = self.get_day_of_week_analysis(start_date, end_date)

        # Find top 5 hours
        hour_pnl_pairs = list(
            zip(hour_analysis["hours"], hour_analysis["pnl_per_hour"])
        )
        top_hours = sorted(hour_pnl_pairs, key=lambda x: x[1], reverse=True)[:5]

        # Find top 3 days
        day_pnl_pairs = list(
            zip(day_analysis["day_names"], day_analysis["pnl_per_day"])
        )
        top_days = sorted(day_pnl_pairs, key=lambda x: x[1], reverse=True)[:3]

        return {
            "top_hours": [
                {"hour": f"{h}:00", "pnl": round(p, 2)} for h, p in top_hours
            ],
            "top_days": [{"day": d, "pnl": round(p, 2)} for d, p in top_days],
        }
