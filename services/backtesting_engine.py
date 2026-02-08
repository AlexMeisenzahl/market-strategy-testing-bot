"""
Backtesting Engine

Simulates strategy execution on historical data to validate performance
before live trading.
"""

import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from database.models import CryptoPriceHistory, PolymarketHistory


class BacktestingEngine:
    """
    Backtesting engine for strategy validation

    Simulates strategy execution on historical data and calculates
    comprehensive performance metrics.
    """

    def __init__(
        self,
        initial_capital: float = 10000.0,
        slippage_pct: float = 0.1,
        fee_pct: float = 0.2,
    ):
        """
        Initialize backtesting engine

        Args:
            initial_capital: Starting capital for backtest
            slippage_pct: Simulated slippage percentage (default 0.1%)
            fee_pct: Trading fee percentage (default 0.2%)
        """
        self.logger = logging.getLogger(__name__)
        self.initial_capital = initial_capital
        self.slippage_pct = slippage_pct / 100.0
        self.fee_pct = fee_pct / 100.0

    def run_backtest(
        self,
        strategy: Any,
        start_date: datetime,
        end_date: datetime,
        symbol: str = "bitcoin",
    ) -> Dict:
        """
        Run backtest for a strategy on historical data

        Args:
            strategy: Strategy object with execute() method
            start_date: Start date for backtest
            end_date: End date for backtest
            symbol: Crypto symbol to test on

        Returns:
            Dict with backtest results and metrics
        """
        self.logger.info(
            f"Running backtest for {strategy.__class__.__name__} "
            f"from {start_date.date()} to {end_date.date()}"
        )

        # Load historical data
        historical_data = self._load_historical_data(symbol, start_date, end_date)

        if not historical_data:
            return {
                "success": False,
                "error": "No historical data available for the specified period",
            }

        # Initialize backtest state
        capital = self.initial_capital
        positions = []
        trades = []
        equity_curve = [self.initial_capital]

        # Simulate strategy execution
        for i, data_point in enumerate(historical_data):
            timestamp = data_point["timestamp"]
            price = data_point["price_usd"]

            # Check if strategy generates a signal
            try:
                # Strategy should have a method to evaluate if it would trade
                # For now, we'll simulate simple logic
                signal = self._evaluate_strategy_signal(
                    strategy, data_point, historical_data[: i + 1]
                )

                if signal == "BUY" and capital > 0:
                    # Execute buy with slippage and fees
                    execution_price = price * (1 + self.slippage_pct)
                    position_size = capital * 0.1  # Risk 10% per trade
                    shares = position_size / execution_price
                    fee = position_size * self.fee_pct

                    capital -= position_size + fee

                    positions.append(
                        {
                            "entry_time": timestamp,
                            "entry_price": execution_price,
                            "shares": shares,
                            "size": position_size,
                        }
                    )

                elif signal == "SELL" and positions:
                    # Close oldest position
                    position = positions.pop(0)

                    execution_price = price * (1 - self.slippage_pct)
                    proceeds = position["shares"] * execution_price
                    fee = proceeds * self.fee_pct
                    profit = proceeds - fee - position["size"]

                    capital += proceeds - fee

                    trades.append(
                        {
                            "entry_time": position["entry_time"],
                            "exit_time": timestamp,
                            "entry_price": position["entry_price"],
                            "exit_price": execution_price,
                            "profit": profit,
                            "return_pct": (profit / position["size"]) * 100,
                        }
                    )

            except Exception as e:
                self.logger.warning(f"Error evaluating strategy at {timestamp}: {e}")

            # Update equity curve
            position_value = sum(p["shares"] * price for p in positions)
            equity_curve.append(capital + position_value)

        # Close any remaining positions at final price
        final_price = historical_data[-1]["price_usd"]
        for position in positions:
            execution_price = final_price * (1 - self.slippage_pct)
            proceeds = position["shares"] * execution_price
            fee = proceeds * self.fee_pct
            profit = proceeds - fee - position["size"]

            capital += proceeds - fee

            trades.append(
                {
                    "entry_time": position["entry_time"],
                    "exit_time": historical_data[-1]["timestamp"],
                    "entry_price": position["entry_price"],
                    "exit_price": execution_price,
                    "profit": profit,
                    "return_pct": (profit / position["size"]) * 100,
                }
            )

        positions.clear()
        equity_curve.append(capital)

        # Calculate metrics
        metrics = self._calculate_metrics(trades, equity_curve)

        # Generate recommendation
        recommendation = self._generate_recommendation(metrics)

        self.logger.info(
            f"Backtest complete: {len(trades)} trades, "
            f"{metrics['return_pct']:.2f}% return, "
            f"Recommendation: {recommendation}"
        )

        return {
            "success": True,
            "strategy": strategy.__class__.__name__,
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": (end_date - start_date).days,
            },
            "trades": trades,
            "metrics": metrics,
            "recommendation": recommendation,
            "equity_curve": equity_curve,
        }

    def _load_historical_data(
        self, symbol: str, start_date: datetime, end_date: datetime
    ) -> List[Dict]:
        """
        Load historical price data from database

        Args:
            symbol: Crypto symbol
            start_date: Start date
            end_date: End date

        Returns:
            List of price data points
        """
        start_ts = int(start_date.timestamp())
        end_ts = int(end_date.timestamp())

        data = CryptoPriceHistory.get_history(symbol, start_ts, end_ts)

        self.logger.info(f"Loaded {len(data)} historical data points")

        return data

    def _evaluate_strategy_signal(
        self, strategy: Any, current_data: Dict, historical_data: List[Dict]
    ) -> Optional[str]:
        """
        Evaluate if strategy would generate a trading signal

        Args:
            strategy: Strategy object
            current_data: Current price data point
            historical_data: Historical data up to current point

        Returns:
            'BUY', 'SELL', or None
        """
        # This is a simplified implementation
        # In production, this would call the actual strategy logic

        if len(historical_data) < 20:
            return None

        # Simple moving average crossover example
        recent_prices = [d["price_usd"] for d in historical_data[-20:]]
        short_ma = np.mean(recent_prices[-5:])
        long_ma = np.mean(recent_prices[-20:])

        if short_ma > long_ma * 1.02:  # 2% above
            return "BUY"
        elif short_ma < long_ma * 0.98:  # 2% below
            return "SELL"

        return None

    def _calculate_metrics(self, trades: List[Dict], equity_curve: List[float]) -> Dict:
        """
        Calculate comprehensive performance metrics

        Args:
            trades: List of completed trades
            equity_curve: Portfolio value over time

        Returns:
            Dict with performance metrics
        """
        if not trades:
            return {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0.0,
                "return_pct": 0.0,
                "sharpe_ratio": 0.0,
                "max_drawdown": 0.0,
                "avg_profit": 0.0,
                "avg_loss": 0.0,
                "profit_factor": 0.0,
            }

        # Basic metrics
        winning_trades = [t for t in trades if t["profit"] > 0]
        losing_trades = [t for t in trades if t["profit"] <= 0]

        total_profit = sum(t["profit"] for t in trades)
        return_pct = (total_profit / self.initial_capital) * 100

        win_rate = (len(winning_trades) / len(trades)) * 100

        # Average profit/loss
        avg_profit = (
            sum(t["profit"] for t in winning_trades) / len(winning_trades)
            if winning_trades
            else 0.0
        )
        avg_loss = (
            sum(abs(t["profit"]) for t in losing_trades) / len(losing_trades)
            if losing_trades
            else 0.0
        )

        # Profit factor
        total_wins = sum(t["profit"] for t in winning_trades)
        total_losses = sum(abs(t["profit"]) for t in losing_trades)
        profit_factor = total_wins / total_losses if total_losses > 0 else float("inf")

        # Sharpe ratio (simplified)
        returns = np.diff(equity_curve) / equity_curve[:-1]
        sharpe_ratio = (
            (np.mean(returns) / np.std(returns)) * np.sqrt(252)
            if np.std(returns) > 0
            else 0.0
        )

        # Max drawdown
        max_drawdown = self._calculate_max_drawdown(equity_curve)

        return {
            "total_trades": len(trades),
            "winning_trades": len(winning_trades),
            "losing_trades": len(losing_trades),
            "win_rate": win_rate,
            "return_pct": return_pct,
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown": max_drawdown,
            "avg_profit": avg_profit,
            "avg_loss": avg_loss,
            "profit_factor": profit_factor,
            "total_profit": total_profit,
        }

    def _calculate_max_drawdown(self, equity_curve: List[float]) -> float:
        """
        Calculate maximum drawdown

        Args:
            equity_curve: Portfolio value over time

        Returns:
            Maximum drawdown percentage
        """
        if not equity_curve:
            return 0.0

        peak = equity_curve[0]
        max_drawdown = 0.0

        for value in equity_curve:
            if value > peak:
                peak = value

            drawdown = ((peak - value) / peak) * 100
            max_drawdown = max(max_drawdown, drawdown)

        return max_drawdown

    def _generate_recommendation(self, metrics: Dict) -> str:
        """
        Generate recommendation based on metrics

        Args:
            metrics: Performance metrics

        Returns:
            Recommendation: "EXCELLENT", "GOOD", "MARGINAL", or "FAILED"
        """
        # Scoring system
        score = 0

        # Return percentage (max 30 points)
        if metrics["return_pct"] > 20:
            score += 30
        elif metrics["return_pct"] > 10:
            score += 20
        elif metrics["return_pct"] > 5:
            score += 10
        elif metrics["return_pct"] > 0:
            score += 5

        # Win rate (max 25 points)
        if metrics["win_rate"] > 60:
            score += 25
        elif metrics["win_rate"] > 50:
            score += 20
        elif metrics["win_rate"] > 40:
            score += 10

        # Sharpe ratio (max 25 points)
        if metrics["sharpe_ratio"] > 2.0:
            score += 25
        elif metrics["sharpe_ratio"] > 1.0:
            score += 20
        elif metrics["sharpe_ratio"] > 0.5:
            score += 10

        # Max drawdown (max 20 points - lower is better)
        if metrics["max_drawdown"] < 5:
            score += 20
        elif metrics["max_drawdown"] < 10:
            score += 15
        elif metrics["max_drawdown"] < 20:
            score += 10
        elif metrics["max_drawdown"] < 30:
            score += 5

        # Generate recommendation
        if score >= 80:
            return "EXCELLENT"
        elif score >= 60:
            return "GOOD"
        elif score >= 40:
            return "MARGINAL"
        else:
            return "FAILED"


# Global instance
backtesting_engine = BacktestingEngine()
