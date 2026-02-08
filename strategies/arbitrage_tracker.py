"""
Arbitrage Tracker Module

Tracks and analyzes arbitrage strategy performance metrics including
opportunities found, execution results, win rate, and profit/loss statistics.
"""

from typing import Dict, List, Any
from datetime import datetime


class ArbitrageTracker:
    """
    Tracks arbitrage strategy performance metrics

    Maintains statistics on opportunities detected, executions performed,
    profit/loss results, and win rate calculations.
    """

    def __init__(self):
        """Initialize tracker with zero metrics"""
        self.opportunities_found: int = 0
        self.opportunities_executed: int = 0
        self.total_profit: float = 0.0
        self.total_loss: float = 0.0
        self.start_time: datetime = datetime.now()
        self.execution_history: List[Dict[str, Any]] = []

    @property
    def win_rate(self) -> float:
        """
        Calculate win rate as percentage of profitable executions

        Returns:
            Win rate percentage (0-100)
        """
        if self.opportunities_executed == 0:
            return 0.0

        profitable_executions = sum(
            1 for execution in self.execution_history if execution.get("profit", 0) > 0
        )

        return (profitable_executions / self.opportunities_executed) * 100

    @property
    def average_profit(self) -> float:
        """
        Calculate average profit per execution

        Returns:
            Average profit in USD (handles losses too)
        """
        if self.opportunities_executed == 0:
            return 0.0

        net_profit = self.total_profit - self.total_loss
        return net_profit / self.opportunities_executed

    def record_opportunity(self, opportunity: Dict[str, Any]) -> None:
        """
        Record when an arbitrage opportunity is detected

        Args:
            opportunity: Dictionary containing opportunity details
                        (market_id, market_name, yes_price, no_price, etc.)
        """
        self.opportunities_found += 1

    def record_execution(self, result: Dict[str, Any]) -> None:
        """
        Record the result of an arbitrage execution

        Args:
            result: Dictionary containing execution results with keys:
                   - 'profit': float (profit/loss amount in USD)
                   - 'market_id': str
                   - 'market_name': str
                   - 'executed_at': datetime or str (optional)
        """
        self.opportunities_executed += 1

        profit = result.get("profit", 0.0)

        # Track profit or loss
        if profit > 0:
            self.total_profit += profit
        else:
            self.total_loss += abs(profit)

        # Add to execution history
        execution_record = {
            "executed_at": result.get("executed_at", datetime.now()),
            "market_id": result.get("market_id", "unknown"),
            "market_name": result.get("market_name", "Unknown Market"),
            "profit": profit,
        }

        self.execution_history.append(execution_record)

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get current metrics snapshot

        Returns:
            Dictionary containing all current metrics
        """
        running_time = datetime.now() - self.start_time
        hours = int(running_time.total_seconds() // 3600)
        minutes = int((running_time.total_seconds() % 3600) // 60)

        return {
            "opportunities_found": self.opportunities_found,
            "opportunities_executed": self.opportunities_executed,
            "total_profit": self.total_profit,
            "total_loss": self.total_loss,
            "net_profit": self.total_profit - self.total_loss,
            "win_rate": self.win_rate,
            "average_profit": self.average_profit,
            "start_time": self.start_time,
            "running_time_hours": hours,
            "running_time_minutes": minutes,
            "execution_history": self.execution_history,
        }

    def reset_metrics(self) -> None:
        """Reset all metrics to zero (for testing or new sessions)"""
        self.opportunities_found = 0
        self.opportunities_executed = 0
        self.total_profit = 0.0
        self.total_loss = 0.0
        self.start_time = datetime.now()
        self.execution_history = []

    def export_summary(self) -> str:
        """
        Generate human-readable summary of metrics

        Returns:
            Formatted string for console output
        """
        metrics = self.get_metrics()

        net_profit = metrics["net_profit"]

        summary = "=== ARBITRAGE PERFORMANCE ===\n"
        summary += f"Opportunities Found: {metrics['opportunities_found']}\n"
        summary += f"Opportunities Executed: {metrics['opportunities_executed']}\n"
        summary += f"Win Rate: {metrics['win_rate']:.2f}%\n"
        summary += f"Total Profit: ${net_profit:.2f}\n"
        summary += f"Average Profit: ${metrics['average_profit']:.2f}\n"
        summary += f"Running Time: {metrics['running_time_hours']}h {metrics['running_time_minutes']}m\n"
        summary += "============================"

        return summary
