"""
Chart Data Service

Prepares data for charts and visualizations in the dashboard.
Uses Decimal-based calculations from data_parser for accuracy.
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from dashboard.services.data_parser import DataParser


class ChartDataService:
    """Prepare chart data for visualizations"""

    def __init__(self, data_parser: DataParser):
        """
        Initialize chart data service

        Args:
            data_parser: Data parser instance
        """
        self.data_parser = data_parser

    def get_cumulative_pnl(self, time_range: str = "1M") -> Dict[str, Any]:
        """
        Get cumulative P&L chart data using Decimal-based calculations

        Args:
            time_range: Time range (1D, 1W, 1M, 3M, 6M, 1Y, ALL)

        Returns:
            Dictionary with chart data
        """
        trades = self.data_parser.get_all_trades()

        # Determine date range
        now = datetime.now()
        if time_range == "1D":
            start_date = now - timedelta(days=1)
        elif time_range == "1W":
            start_date = now - timedelta(weeks=1)
        elif time_range == "1M":
            start_date = now - timedelta(days=30)
        elif time_range == "3M":
            start_date = now - timedelta(days=90)
        elif time_range == "6M":
            start_date = now - timedelta(days=180)
        elif time_range == "1Y":
            start_date = now - timedelta(days=365)
        else:  # ALL
            start_date = datetime.min

        # Filter trades by date range
        filtered_trades = [
            t for t in trades if datetime.fromisoformat(t["timestamp"]) >= start_date
        ]

        # Sort by entry time
        filtered_trades.sort(key=lambda x: x["timestamp"])

        # Use data_parser's Decimal-based cumulative calculation
        chart_data = self.data_parser.prepare_cumulative_pnl_chart_data(filtered_trades)

        # Convert to the format expected by existing code
        data_points = []
        for i, (label, value) in enumerate(
            zip(chart_data["labels"], chart_data["data"])
        ):
            # Find corresponding trade for this date
            date_obj = (
                datetime.fromisoformat(label).date()
                if isinstance(label, str)
                else label
            )
            trades_on_date = [
                t
                for t in filtered_trades
                if datetime.fromisoformat(t["timestamp"]).date() == date_obj
            ]

            # Use last trade of the day for display
            if trades_on_date:
                last_trade = trades_on_date[-1]
                data_points.append(
                    {
                        "timestamp": last_trade["timestamp"],
                        "value": round(value, 2),
                        "trade_id": last_trade["id"],
                        "symbol": last_trade["symbol"],
                    }
                )

        return {
            "data": data_points,
            "start_date": (
                start_date.isoformat() if start_date != datetime.min else None
            ),
            "end_date": now.isoformat(),
            "total_pnl": data_points[-1]["value"] if data_points else 0,
        }

    def get_daily_pnl(self) -> Dict[str, Any]:
        """
        Get daily P&L chart data using Decimal-based calculations

        Returns:
            Dictionary with daily P&L data
        """
        trades = self.data_parser.get_all_trades()

        # Use data_parser's Decimal-based daily calculation
        chart_data = self.data_parser.prepare_daily_pnl_chart_data(trades)

        # Convert to the format expected by existing code
        data_points = []
        for label, pnl in zip(chart_data["labels"], chart_data["data"]):
            data_points.append(
                {
                    "date": label,
                    "pnl": round(pnl, 2),
                    "color": "green" if pnl > 0 else "red",
                }
            )

        # Calculate moving average (7-day)
        ma_period = 7
        for i, point in enumerate(data_points):
            start_idx = max(0, i - ma_period + 1)
            ma_values = [data_points[j]["pnl"] for j in range(start_idx, i + 1)]
            point["ma"] = round(sum(ma_values) / len(ma_values), 2)

        return {
            "data": data_points,
            "total_days": len(data_points),
            "profitable_days": len([p for p in data_points if p["pnl"] > 0]),
            "loss_days": len([p for p in data_points if p["pnl"] < 0]),
        }

    def get_strategy_performance(self) -> Dict[str, Any]:
        """
        Get strategy performance comparison data using Decimal precision

        Returns:
            Dictionary with strategy comparison data
        """
        # Use data_parser's Decimal-based method
        performance = self.data_parser.get_strategy_performance()

        # Convert to list format for charts
        strategies = []
        for strategy_name, data in performance.items():
            strategies.append(
                {
                    "name": strategy_name,
                    "pnl": data["total_pnl"],
                    "win_rate": data["win_rate"],
                    "total_trades": data["trades_executed"],
                    "wins": data["wins"],
                    "losses": data["losses"],
                    "opportunities": data["opportunities_found"],
                }
            )

        # Sort by P&L (descending)
        strategies.sort(key=lambda x: x["pnl"], reverse=True)

        return {"strategies": strategies, "total_strategies": len(strategies)}

    def get_win_rate_distribution(self) -> Dict[str, Any]:
        """
        Get win/loss distribution for pie chart

        Returns:
            Dictionary with win/loss distribution
        """
        trades = self.data_parser.get_all_trades()

        wins = len([t for t in trades if t["pnl_usd"] > 0])
        losses = len([t for t in trades if t["pnl_usd"] < 0])
        breakeven = len([t for t in trades if t["pnl_usd"] == 0])

        total = len(trades)

        return {
            "data": [
                {
                    "label": "Wins",
                    "value": wins,
                    "percentage": round(wins / total * 100, 2) if total > 0 else 0,
                    "color": "#10b981",
                },
                {
                    "label": "Losses",
                    "value": losses,
                    "percentage": round(losses / total * 100, 2) if total > 0 else 0,
                    "color": "#ef4444",
                },
                {
                    "label": "Breakeven",
                    "value": breakeven,
                    "percentage": round(breakeven / total * 100, 2) if total > 0 else 0,
                    "color": "#6b7280",
                },
            ],
            "total": total,
        }

    def get_pnl_over_time(self) -> Dict[str, Any]:
        """
        Get P&L over time formatted for Chart.js
        
        Returns:
            Dictionary with labels and values for chart
        """
        trades = self.data_parser.get_all_trades()
        
        if not trades:
            return {"labels": [], "values": []}
        
        # Sort by timestamp
        trades.sort(key=lambda x: x["timestamp"])
        
        # Calculate cumulative P&L
        cumulative_pnl = Decimal(0)
        labels = []
        values = []
        
        for trade in trades:
            cumulative_pnl += Decimal(str(trade.get("pnl_usd", 0)))
            
            # Parse timestamp safely - handle both string and datetime objects
            timestamp_val = trade["timestamp"]
            if isinstance(timestamp_val, str):
                try:
                    timestamp = datetime.fromisoformat(timestamp_val.replace("Z", "+00:00"))
                except (ValueError, AttributeError):
                    # Skip trades with invalid timestamps
                    continue
            elif isinstance(timestamp_val, datetime):
                timestamp = timestamp_val
            else:
                # Skip trades with unexpected timestamp formats
                continue
            
            # Format timestamp as date
            date_label = timestamp.strftime("%Y-%m-%d")
            
            labels.append(date_label)
            values.append(float(cumulative_pnl))
        
        return {
            "labels": labels,
            "values": values
        }
