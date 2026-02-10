"""
Performance Calculator

Calculates real performance metrics for trading strategies:
- Sharpe Ratio
- Sortino Ratio
- Maximum Drawdown
- Win Rate
- Profit Factor
- CAGR (Compound Annual Growth Rate)
- Recovery Factor
"""

import logging
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class PerformanceCalculator:
    """
    Calculates performance metrics from trade history

    Provides real statistical analysis of trading performance.
    """

    def __init__(self, risk_free_rate: float = 0.02):
        """
        Initialize performance calculator

        Args:
            risk_free_rate: Annual risk-free rate (default: 2%)
        """
        self.risk_free_rate = risk_free_rate
        self.logs_dir = Path("logs")

    def calculate_all_metrics(self, trades: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate all performance metrics

        Args:
            trades: List of trade dictionaries with P&L data

        Returns:
            Dictionary with all metrics
        """
        if not trades:
            return self._get_empty_metrics()

        returns = self._extract_returns(trades)

        return {
            "sharpe_ratio": self.calculate_sharpe_ratio(returns),
            "sortino_ratio": self.calculate_sortino_ratio(returns),
            "max_drawdown": self.calculate_max_drawdown(returns),
            "max_drawdown_pct": self.calculate_max_drawdown_pct(returns),
            "win_rate": self.calculate_win_rate(trades),
            "profit_factor": self.calculate_profit_factor(trades),
            "cagr": self.calculate_cagr(returns, trades),
            "recovery_factor": self.calculate_recovery_factor(returns),
            "total_return": self.calculate_total_return(returns),
            "volatility": self.calculate_volatility(returns),
            "avg_win": self.calculate_avg_win(trades),
            "avg_loss": self.calculate_avg_loss(trades),
            "largest_win": self.calculate_largest_win(trades),
            "largest_loss": self.calculate_largest_loss(trades),
            "total_trades": len(trades),
            "winning_trades": len([t for t in trades if self._get_trade_pnl(t) > 0]),
            "losing_trades": len([t for t in trades if self._get_trade_pnl(t) < 0]),
        }

    def calculate_sharpe_ratio(self, returns: List[float]) -> float:
        """
        Calculate Sharpe Ratio

        Sharpe Ratio = (Mean Return - Risk Free Rate) / Std Dev of Returns

        Args:
            returns: List of returns

        Returns:
            Sharpe ratio (annualized)
        """
        if not returns or len(returns) < 2:
            return 0.0

        try:
            returns_array = np.array(returns)

            # Calculate excess returns
            mean_return = np.mean(returns_array)
            std_return = np.std(returns_array, ddof=1)

            if std_return == 0:
                return 0.0

            # Annualize (assuming daily returns)
            daily_risk_free = self.risk_free_rate / 252
            sharpe = (mean_return - daily_risk_free) / std_return

            # Annualize Sharpe ratio
            annualized_sharpe = sharpe * np.sqrt(252)

            return float(annualized_sharpe)

        except Exception as e:
            logger.error(f"Error calculating Sharpe ratio: {e}")
            return 0.0

    def calculate_sortino_ratio(self, returns: List[float]) -> float:
        """
        Calculate Sortino Ratio

        Similar to Sharpe but only considers downside volatility

        Args:
            returns: List of returns

        Returns:
            Sortino ratio (annualized)
        """
        if not returns or len(returns) < 2:
            return 0.0

        try:
            returns_array = np.array(returns)

            # Calculate mean return
            mean_return = np.mean(returns_array)

            # Calculate downside deviation (only negative returns)
            downside_returns = returns_array[returns_array < 0]

            if len(downside_returns) == 0:
                return float("inf")  # No downside = infinite Sortino

            downside_std = np.std(downside_returns, ddof=1)

            if downside_std == 0:
                return 0.0

            # Annualize
            daily_risk_free = self.risk_free_rate / 252
            sortino = (mean_return - daily_risk_free) / downside_std

            # Annualize Sortino ratio
            annualized_sortino = sortino * np.sqrt(252)

            return float(annualized_sortino)

        except Exception as e:
            logger.error(f"Error calculating Sortino ratio: {e}")
            return 0.0

    def calculate_max_drawdown(self, returns: List[float]) -> float:
        """
        Calculate maximum drawdown in absolute terms

        Args:
            returns: List of returns

        Returns:
            Maximum drawdown (absolute value)
        """
        if not returns:
            return 0.0

        try:
            # Calculate cumulative returns
            cumulative = np.cumprod(1 + np.array(returns))

            # Calculate running maximum
            running_max = np.maximum.accumulate(cumulative)

            # Calculate drawdown
            drawdown = cumulative - running_max

            max_dd = float(np.min(drawdown))

            return abs(max_dd)

        except Exception as e:
            logger.error(f"Error calculating max drawdown: {e}")
            return 0.0

    def calculate_max_drawdown_pct(self, returns: List[float]) -> float:
        """
        Calculate maximum drawdown as percentage

        Args:
            returns: List of returns

        Returns:
            Maximum drawdown percentage
        """
        if not returns:
            return 0.0

        try:
            # Calculate cumulative returns
            cumulative = np.cumprod(1 + np.array(returns))

            # Calculate running maximum
            running_max = np.maximum.accumulate(cumulative)

            # Calculate drawdown percentage
            drawdown_pct = (cumulative - running_max) / running_max

            max_dd_pct = float(np.min(drawdown_pct)) * 100

            return abs(max_dd_pct)

        except Exception as e:
            logger.error(f"Error calculating max drawdown %: {e}")
            return 0.0

    def calculate_win_rate(self, trades: List[Dict[str, Any]]) -> float:
        """
        Calculate win rate percentage

        Args:
            trades: List of trades

        Returns:
            Win rate percentage (0-100)
        """
        if not trades:
            return 0.0

        winning_trades = sum(1 for t in trades if self._get_trade_pnl(t) > 0)

        return (winning_trades / len(trades)) * 100

    def calculate_profit_factor(self, trades: List[Dict[str, Any]]) -> float:
        """
        Calculate profit factor

        Profit Factor = Gross Profit / Gross Loss

        Args:
            trades: List of trades

        Returns:
            Profit factor
        """
        if not trades:
            return 0.0

        gross_profit = sum(
            self._get_trade_pnl(t) for t in trades if self._get_trade_pnl(t) > 0
        )
        gross_loss = abs(
            sum(self._get_trade_pnl(t) for t in trades if self._get_trade_pnl(t) < 0)
        )

        if gross_loss == 0:
            return float("inf") if gross_profit > 0 else 0.0

        return gross_profit / gross_loss

    def calculate_cagr(
        self, returns: List[float], trades: List[Dict[str, Any]]
    ) -> float:
        """
        Calculate Compound Annual Growth Rate

        Args:
            returns: List of returns
            trades: List of trades (for date range)

        Returns:
            CAGR percentage
        """
        if not returns or not trades:
            return 0.0

        try:
            # Get date range
            dates = [self._get_trade_date(t) for t in trades if self._get_trade_date(t)]

            if not dates:
                return 0.0

            start_date = min(dates)
            end_date = max(dates)

            # Calculate years
            days = (end_date - start_date).days
            if days < 1:
                return 0.0

            years = days / 365.25

            # Calculate total return
            total_return = np.prod(1 + np.array(returns))

            # Calculate CAGR
            cagr = (total_return ** (1 / years) - 1) * 100

            return float(cagr)

        except Exception as e:
            logger.error(f"Error calculating CAGR: {e}")
            return 0.0

    def calculate_recovery_factor(self, returns: List[float]) -> float:
        """
        Calculate recovery factor

        Recovery Factor = Total Return / Max Drawdown

        Args:
            returns: List of returns

        Returns:
            Recovery factor
        """
        if not returns:
            return 0.0

        total_return = self.calculate_total_return(returns)
        max_dd = self.calculate_max_drawdown(returns)

        if max_dd == 0:
            return float("inf") if total_return > 0 else 0.0

        return total_return / max_dd

    def calculate_total_return(self, returns: List[float]) -> float:
        """
        Calculate total return percentage

        Args:
            returns: List of returns

        Returns:
            Total return percentage
        """
        if not returns:
            return 0.0

        total = (np.prod(1 + np.array(returns)) - 1) * 100
        return float(total)

    def calculate_volatility(self, returns: List[float]) -> float:
        """
        Calculate annualized volatility

        Args:
            returns: List of returns

        Returns:
            Annualized volatility percentage
        """
        if not returns or len(returns) < 2:
            return 0.0

        # Calculate standard deviation
        std = np.std(returns, ddof=1)

        # Annualize (assuming daily returns)
        annualized_vol = std * np.sqrt(252) * 100

        return float(annualized_vol)

    def calculate_avg_win(self, trades: List[Dict[str, Any]]) -> float:
        """
        Calculate average winning trade

        Args:
            trades: List of trades

        Returns:
            Average win amount
        """
        winning_trades = [
            self._get_trade_pnl(t) for t in trades if self._get_trade_pnl(t) > 0
        ]

        if not winning_trades:
            return 0.0

        return np.mean(winning_trades)

    def calculate_avg_loss(self, trades: List[Dict[str, Any]]) -> float:
        """
        Calculate average losing trade

        Args:
            trades: List of trades

        Returns:
            Average loss amount (absolute value)
        """
        losing_trades = [
            abs(self._get_trade_pnl(t)) for t in trades if self._get_trade_pnl(t) < 0
        ]

        if not losing_trades:
            return 0.0

        return np.mean(losing_trades)

    def calculate_largest_win(self, trades: List[Dict[str, Any]]) -> float:
        """
        Calculate largest winning trade

        Args:
            trades: List of trades

        Returns:
            Largest win amount
        """
        if not trades:
            return 0.0

        pnls = [self._get_trade_pnl(t) for t in trades]
        return max(pnls) if pnls else 0.0

    def calculate_largest_loss(self, trades: List[Dict[str, Any]]) -> float:
        """
        Calculate largest losing trade

        Args:
            trades: List of trades

        Returns:
            Largest loss amount (absolute value)
        """
        if not trades:
            return 0.0

        pnls = [self._get_trade_pnl(t) for t in trades]
        return abs(min(pnls)) if pnls else 0.0

    def _extract_returns(self, trades: List[Dict[str, Any]]) -> List[float]:
        """
        Extract returns from trades

        Args:
            trades: List of trades

        Returns:
            List of returns (as decimals, e.g., 0.05 for 5%)
        """
        # For simplicity, assume each trade's P&L represents a return
        # In reality, this should be: (P&L / Capital at trade time)
        returns = []

        for trade in trades:
            pnl = self._get_trade_pnl(trade)
            # TODO: Get actual capital from portfolio tracker instead of hardcoded value
            # This hardcoded value may lead to inaccurate return calculations
            capital = 10000
            returns.append(pnl / capital)

        return returns

    def _get_trade_pnl(self, trade: Dict[str, Any]) -> float:
        """Get P&L from trade dictionary"""
        return trade.get("pnl", trade.get("profit", 0.0))

    def _get_trade_date(self, trade: Dict[str, Any]) -> Optional[datetime]:
        """Get date from trade dictionary"""
        timestamp = trade.get("timestamp", trade.get("created_at"))

        if not timestamp:
            return None

        if isinstance(timestamp, str):
            try:
                return datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            except:
                return None

        return timestamp

    def _get_empty_metrics(self) -> Dict[str, Any]:
        """Return empty metrics dictionary"""
        return {
            "sharpe_ratio": 0.0,
            "sortino_ratio": 0.0,
            "max_drawdown": 0.0,
            "max_drawdown_pct": 0.0,
            "win_rate": 0.0,
            "profit_factor": 0.0,
            "cagr": 0.0,
            "recovery_factor": 0.0,
            "total_return": 0.0,
            "volatility": 0.0,
            "avg_win": 0.0,
            "avg_loss": 0.0,
            "largest_win": 0.0,
            "largest_loss": 0.0,
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
        }


# Global instance
performance_calculator: Optional[PerformanceCalculator] = None


def get_performance_calculator() -> PerformanceCalculator:
    """
    Get or create global performance calculator instance

    Returns:
        PerformanceCalculator instance
    """
    global performance_calculator

    if performance_calculator is None:
        performance_calculator = PerformanceCalculator()

    return performance_calculator
