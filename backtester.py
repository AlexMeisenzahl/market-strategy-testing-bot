"""
Backtester Module - Test strategies on historical data

Tests trading strategies against historical market data to evaluate:
- Total returns and profit/loss
- Sharpe ratio (risk-adjusted returns)
- Maximum drawdown
- Win rate and trade distribution
- Best and worst performing trades

Works with historical CSV data and provides comprehensive performance reports.
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import csv
import statistics
from logger import get_logger


class BacktestTrade:
    """Represents a single trade in the backtest"""

    def __init__(
        self,
        timestamp: datetime,
        market: str,
        yes_price: float,
        no_price: float,
        trade_size: float,
    ):
        """
        Initialize backtest trade

        Args:
            timestamp: When the trade was executed
            market: Market identifier
            yes_price: YES contract price
            no_price: NO contract price
            trade_size: Size of trade in USD
        """
        self.timestamp = timestamp
        self.market = market
        self.yes_price = yes_price
        self.no_price = no_price
        self.trade_size = trade_size

        # Calculate costs and profit
        self.yes_cost = trade_size * yes_price
        self.no_cost = trade_size * no_price
        self.total_cost = self.yes_cost + self.no_cost
        self.expected_return = trade_size
        self.profit = self.expected_return - self.total_cost
        self.profit_pct = (
            (self.profit / self.total_cost) * 100 if self.total_cost > 0 else 0
        )

    def is_winner(self) -> bool:
        """Check if trade was profitable"""
        return self.profit > 0


class Backtester:
    """
    Backtesting engine for testing strategies on historical data

    Simulates trading strategies on past data to evaluate performance
    without risking real capital.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize backtester

        Args:
            config: Configuration dictionary from config.yaml
        """
        self.config = config
        self.logger = get_logger()

        # Trading parameters
        self.max_trade_size = config.get("max_trade_size", 10)
        self.min_profit_margin = config.get("min_profit_margin", 0.02)

        # Backtest results
        self.trades: List[BacktestTrade] = []
        self.opportunities_found = 0
        self.opportunities_traded = 0

        self.logger.log_warning(
            f"Backtester initialized - Trade size: ${self.max_trade_size}, "
            f"Min profit: {self.min_profit_margin*100:.1f}%"
        )

    def load_historical_data(
        self,
        date_range: Optional[Tuple[datetime, datetime]] = None,
        filepath: str = "historical_data.csv",
    ) -> List[Dict[str, Any]]:
        """
        Load historical market data from CSV

        Args:
            date_range: Optional tuple of (start_date, end_date) to filter data
            filepath: Path to historical data CSV file

        Returns:
            List of market data dictionaries

        CSV format expected:
        timestamp,market,yes_price,no_price
        """
        data = []
        filepath_obj = Path(filepath)

        if not filepath_obj.exists():
            self.logger.log_error(f"Historical data file not found: {filepath}")
            return data

        try:
            with open(filepath_obj, "r") as f:
                reader = csv.DictReader(f)

                for row in reader:
                    # Parse timestamp
                    timestamp = datetime.fromisoformat(
                        row["timestamp"].replace("Z", "+00:00")
                    )

                    # Apply date filter if provided
                    if date_range:
                        start_date, end_date = date_range
                        if timestamp < start_date or timestamp > end_date:
                            continue

                    # Parse market data
                    data.append(
                        {
                            "timestamp": timestamp,
                            "market": row["market"],
                            "yes_price": float(row["yes_price"]),
                            "no_price": float(row["no_price"]),
                        }
                    )

            self.logger.log_warning(
                f"Loaded {len(data)} historical data points from {filepath}"
            )

        except Exception as e:
            self.logger.log_error(f"Error loading historical data: {str(e)}")

        return data

    def simulate_strategy(
        self, strategy: str, data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Simulate a trading strategy on historical data

        Args:
            strategy: Strategy name (currently supports "basic_arbitrage")
            data: List of historical market data

        Returns:
            Dictionary with simulation results
        """
        self.trades = []
        self.opportunities_found = 0
        self.opportunities_traded = 0

        if not data:
            self.logger.log_error("No data provided for backtest")
            return {}

        self.logger.log_warning(
            f"Starting backtest: {strategy} strategy on {len(data)} data points"
        )

        # Run strategy simulation
        if strategy == "basic_arbitrage":
            self._simulate_basic_arbitrage(data)
        else:
            self.logger.log_error(f"Unknown strategy: {strategy}")
            return {}

        # Generate results
        results = self._calculate_results()

        self.logger.log_warning(
            f"Backtest complete - Opportunities: {self.opportunities_found}, "
            f"Trades: {self.opportunities_traded}, "
            f"Total P&L: ${results['total_profit']:.2f}"
        )

        return results

    def _simulate_basic_arbitrage(self, data: List[Dict[str, Any]]) -> None:
        """
        Simulate basic arbitrage strategy

        Args:
            data: Historical market data
        """
        for point in data:
            yes_price = point["yes_price"]
            no_price = point["no_price"]
            price_sum = yes_price + no_price

            # Check if arbitrage opportunity exists
            if price_sum < 1.0:
                self.opportunities_found += 1

                # Calculate profit margin
                profit_margin = (1.0 - price_sum) / price_sum

                # Check if meets minimum profit threshold
                if profit_margin >= self.min_profit_margin:
                    # Execute trade
                    trade = BacktestTrade(
                        timestamp=point["timestamp"],
                        market=point["market"],
                        yes_price=yes_price,
                        no_price=no_price,
                        trade_size=self.max_trade_size,
                    )

                    self.trades.append(trade)
                    self.opportunities_traded += 1

    def _calculate_results(self) -> Dict[str, Any]:
        """
        Calculate comprehensive backtest results

        Returns:
            Dictionary with detailed performance metrics
        """
        if not self.trades:
            return {
                "total_trades": 0,
                "total_profit": 0,
                "total_return_pct": 0,
                "sharpe_ratio": 0,
                "max_drawdown_pct": 0,
                "win_rate": 0,
                "best_trade": None,
                "worst_trade": None,
            }

        # Basic metrics
        total_profit = sum(trade.profit for trade in self.trades)
        total_invested = sum(trade.total_cost for trade in self.trades)
        total_return_pct = (
            (total_profit / total_invested * 100) if total_invested > 0 else 0
        )

        # Win rate
        winning_trades = sum(1 for trade in self.trades if trade.is_winner())
        win_rate = winning_trades / len(self.trades) if self.trades else 0

        # Best and worst trades
        best_trade = max(self.trades, key=lambda t: t.profit)
        worst_trade = min(self.trades, key=lambda t: t.profit)

        # Sharpe ratio (risk-adjusted returns)
        sharpe_ratio = self._calculate_sharpe_ratio()

        # Maximum drawdown
        max_drawdown_pct = self._calculate_max_drawdown()

        return {
            "total_trades": len(self.trades),
            "opportunities_found": self.opportunities_found,
            "opportunities_traded": self.opportunities_traded,
            "total_profit": total_profit,
            "total_invested": total_invested,
            "total_return_pct": total_return_pct,
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown_pct": max_drawdown_pct,
            "win_rate": win_rate,
            "winning_trades": winning_trades,
            "losing_trades": len(self.trades) - winning_trades,
            "best_trade": {
                "market": best_trade.market,
                "profit": best_trade.profit,
                "profit_pct": best_trade.profit_pct,
                "timestamp": best_trade.timestamp.isoformat(),
            },
            "worst_trade": {
                "market": worst_trade.market,
                "profit": worst_trade.profit,
                "profit_pct": worst_trade.profit_pct,
                "timestamp": worst_trade.timestamp.isoformat(),
            },
        }

    def _calculate_sharpe_ratio(self) -> float:
        """
        Calculate Sharpe ratio (risk-adjusted returns)

        Returns:
            Sharpe ratio (higher is better, >1.0 is good)
        """
        if len(self.trades) < 2:
            return 0.0

        # Calculate returns for each trade
        returns = [trade.profit_pct for trade in self.trades]

        # Mean return
        mean_return = statistics.mean(returns)

        # Standard deviation of returns
        std_return = statistics.stdev(returns)

        # Sharpe ratio (assuming risk-free rate of 0)
        if std_return == 0:
            return 0.0

        sharpe_ratio = mean_return / std_return

        # Annualized (assuming ~252 trading days)
        sharpe_ratio *= 252**0.5

        return sharpe_ratio

    def _calculate_max_drawdown(self) -> float:
        """
        Calculate maximum drawdown percentage

        Returns:
            Maximum drawdown as percentage (0-100)
        """
        if not self.trades:
            return 0.0

        # Track cumulative P&L
        cumulative_pnl = []
        running_total = 0

        for trade in self.trades:
            running_total += trade.profit
            cumulative_pnl.append(running_total)

        # Find maximum drawdown
        peak = cumulative_pnl[0]
        max_drawdown = 0

        for value in cumulative_pnl:
            if value > peak:
                peak = value

            drawdown = peak - value
            if drawdown > max_drawdown:
                max_drawdown = drawdown

        # Convert to percentage of peak
        max_drawdown_pct = (max_drawdown / abs(peak) * 100) if peak != 0 else 0

        return max_drawdown_pct

    def generate_backtest_report(self) -> str:
        """
        Generate comprehensive backtest report

        Returns:
            Formatted report string
        """
        results = self._calculate_results()

        report = "\n" + "=" * 60 + "\n"
        report += "BACKTEST REPORT\n"
        report += "=" * 60 + "\n\n"

        report += "OPPORTUNITY ANALYSIS:\n"
        report += f"  Total Opportunities Found: {results['opportunities_found']}\n"
        report += f"  Opportunities Traded: {results['opportunities_traded']}\n"
        if results["opportunities_found"] > 0:
            trade_pct = (
                results["opportunities_traded"] / results["opportunities_found"] * 100
            )
            report += f"  Trade Rate: {trade_pct:.1f}%\n"
        report += "\n"

        report += "PERFORMANCE METRICS:\n"
        report += f"  Total Trades: {results['total_trades']}\n"
        report += f"  Total Invested: ${results['total_invested']:.2f}\n"
        report += f"  Total Profit: ${results['total_profit']:.2f}\n"
        report += f"  Total Return: {results['total_return_pct']:.2f}%\n"
        report += f"  Sharpe Ratio: {results['sharpe_ratio']:.2f}\n"
        report += f"  Max Drawdown: {results['max_drawdown_pct']:.2f}%\n"
        report += "\n"

        report += "WIN/LOSS ANALYSIS:\n"
        report += f"  Win Rate: {results['win_rate']*100:.1f}%\n"
        report += f"  Winning Trades: {results['winning_trades']}\n"
        report += f"  Losing Trades: {results['losing_trades']}\n"
        report += "\n"

        if results["best_trade"]:
            report += "BEST TRADE:\n"
            report += f"  Market: {results['best_trade']['market']}\n"
            report += f"  Profit: ${results['best_trade']['profit']:.2f} ({results['best_trade']['profit_pct']:.2f}%)\n"
            report += f"  Time: {results['best_trade']['timestamp']}\n"
            report += "\n"

        if results["worst_trade"]:
            report += "WORST TRADE:\n"
            report += f"  Market: {results['worst_trade']['market']}\n"
            report += f"  Profit: ${results['worst_trade']['profit']:.2f} ({results['worst_trade']['profit_pct']:.2f}%)\n"
            report += f"  Time: {results['worst_trade']['timestamp']}\n"
            report += "\n"

        report += "=" * 60 + "\n"

        return report
