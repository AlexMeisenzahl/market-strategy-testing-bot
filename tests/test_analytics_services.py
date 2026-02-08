"""
Unit Tests for Analytics Services

Tests strategy analytics, market analytics, time analytics, and risk metrics
to ensure accurate calculations using Decimal precision.
"""

import sys
import os
from pathlib import Path
from decimal import Decimal
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dashboard.services.data_parser import DataParser
from services.strategy_analytics import StrategyAnalytics
from services.market_analytics import MarketAnalytics
from services.time_analytics import TimeAnalytics
from services.risk_metrics import RiskMetrics


class MockDataParser:
    """Mock data parser for testing"""

    def __init__(self, trades=None):
        self.trades = trades or []

    def get_trades(
        self, strategy=None, symbol=None, start_date=None, end_date=None, per_page=100
    ):
        """Return mock trades"""
        filtered = self.trades.copy()

        if strategy:
            filtered = [t for t in filtered if t["strategy"] == strategy]
        if symbol:
            filtered = [t for t in filtered if t["symbol"] == symbol]

        return {"trades": filtered}


class TestStrategyAnalytics:
    """Test suite for StrategyAnalytics service"""

    def setup_method(self):
        """Setup test environment"""
        # Create sample trades
        self.sample_trades = [
            {
                "id": 1,
                "strategy": "Strategy A",
                "symbol": "AAPL",
                "entry_time": "2024-01-01T10:00:00",
                "exit_time": "2024-01-01T11:00:00",
                "duration_minutes": 60,
                "pnl_usd": 100.0,
                "pnl_pct": 2.0,
                "outcome": "win",
            },
            {
                "id": 2,
                "strategy": "Strategy A",
                "symbol": "TSLA",
                "entry_time": "2024-01-01T12:00:00",
                "exit_time": "2024-01-01T13:00:00",
                "duration_minutes": 60,
                "pnl_usd": -50.0,
                "pnl_pct": -1.0,
                "outcome": "loss",
            },
            {
                "id": 3,
                "strategy": "Strategy A",
                "symbol": "MSFT",
                "entry_time": "2024-01-01T14:00:00",
                "exit_time": "2024-01-01T15:00:00",
                "duration_minutes": 60,
                "pnl_usd": 75.0,
                "pnl_pct": 1.5,
                "outcome": "win",
            },
            {
                "id": 4,
                "strategy": "Strategy B",
                "symbol": "GOOGL",
                "entry_time": "2024-01-01T16:00:00",
                "exit_time": "2024-01-01T17:00:00",
                "duration_minutes": 60,
                "pnl_usd": 200.0,
                "pnl_pct": 4.0,
                "outcome": "win",
            },
        ]

        self.mock_parser = MockDataParser(self.sample_trades)
        self.analytics = StrategyAnalytics(self.mock_parser)

    def test_strategy_performance_metrics(self):
        """Test that all 18 metrics are calculated"""
        metrics = self.analytics.get_strategy_performance("Strategy A")

        # Check all required metrics exist
        required_keys = [
            "strategy_name",
            "total_trades",
            "winning_trades",
            "losing_trades",
            "win_rate",
            "total_pnl",
            "avg_profit",
            "avg_win",
            "avg_loss",
            "profit_factor",
            "largest_win",
            "largest_loss",
            "avg_duration_hours",
            "expectancy",
            "max_consecutive_wins",
            "max_consecutive_losses",
            "max_drawdown",
            "recovery_factor",
        ]

        for key in required_keys:
            assert key in metrics, f"Missing metric: {key}"

        print(f"✓ test_strategy_performance_metrics: All 18 metrics present")

    def test_win_rate_calculation(self):
        """Test win rate calculation"""
        metrics = self.analytics.get_strategy_performance("Strategy A")

        # Strategy A has 2 wins out of 3 trades = 66.67%
        expected_win_rate = 66.67
        assert (
            abs(metrics["win_rate"] - expected_win_rate) < 0.1
        ), f"Expected win rate {expected_win_rate}, got {metrics['win_rate']}"

        print(
            f"✓ test_win_rate_calculation: {metrics['win_rate']} ≈ {expected_win_rate}"
        )

    def test_total_pnl_calculation(self):
        """Test total P&L calculation with Decimal precision"""
        metrics = self.analytics.get_strategy_performance("Strategy A")

        # Strategy A: 100 - 50 + 75 = 125
        expected_pnl = 125.0
        assert (
            abs(metrics["total_pnl"] - expected_pnl) < 0.01
        ), f"Expected P&L {expected_pnl}, got {metrics['total_pnl']}"

        print(f"✓ test_total_pnl_calculation: {metrics['total_pnl']} == {expected_pnl}")

    def test_profit_factor_calculation(self):
        """Test profit factor (Gross Profit / Gross Loss)"""
        metrics = self.analytics.get_strategy_performance("Strategy A")

        # Gross profit: 100 + 75 = 175
        # Gross loss: 50
        # Profit factor: 175 / 50 = 3.5
        expected_pf = 3.5
        assert (
            abs(metrics["profit_factor"] - expected_pf) < 0.1
        ), f"Expected profit factor {expected_pf}, got {metrics['profit_factor']}"

        print(
            f"✓ test_profit_factor_calculation: {metrics['profit_factor']} ≈ {expected_pf}"
        )

    def test_profit_factor_zero_loss(self):
        """Test profit factor when there are no losses (should return inf or large number)"""
        # Create trades with only wins
        winning_trades = [
            {
                "id": 1,
                "strategy": "WinOnly",
                "symbol": "AAPL",
                "entry_time": "2024-01-01T10:00:00",
                "duration_minutes": 60,
                "pnl_usd": 100.0,
                "outcome": "win",
            }
        ]

        parser = MockDataParser(winning_trades)
        analytics = StrategyAnalytics(parser)
        metrics = analytics.get_strategy_performance("WinOnly")

        # Should return a very high value (we cap at 999.99)
        assert (
            metrics["profit_factor"] >= 999.0
        ), f"Expected high profit factor for zero losses, got {metrics['profit_factor']}"

        print(f"✓ test_profit_factor_zero_loss: {metrics['profit_factor']} (capped)")

    def test_expectancy_calculation(self):
        """Test expectancy: (Win% × Avg Win) - (Loss% × Avg Loss)"""
        metrics = self.analytics.get_strategy_performance("Strategy A")

        # Win rate: 66.67% (2/3)
        # Avg win: (100 + 75) / 2 = 87.5
        # Loss rate: 33.33% (1/3)
        # Avg loss: -50
        # Expectancy: 0.6667 * 87.5 - 0.3333 * 50 = 58.33 - 16.67 = 41.66
        expected_expectancy = 41.66
        assert (
            abs(metrics["expectancy"] - expected_expectancy) < 1.0
        ), f"Expected expectancy {expected_expectancy}, got {metrics['expectancy']}"

        print(
            f"✓ test_expectancy_calculation: {metrics['expectancy']} ≈ {expected_expectancy}"
        )

    def test_consecutive_wins(self):
        """Test max consecutive wins calculation"""
        # Create trades with consecutive wins
        consecutive_trades = [
            {
                "id": 1,
                "strategy": "Test",
                "symbol": "A",
                "entry_time": "2024-01-01T10:00:00",
                "duration_minutes": 60,
                "pnl_usd": 10.0,
                "outcome": "win",
            },
            {
                "id": 2,
                "strategy": "Test",
                "symbol": "A",
                "entry_time": "2024-01-01T11:00:00",
                "duration_minutes": 60,
                "pnl_usd": 20.0,
                "outcome": "win",
            },
            {
                "id": 3,
                "strategy": "Test",
                "symbol": "A",
                "entry_time": "2024-01-01T12:00:00",
                "duration_minutes": 60,
                "pnl_usd": 30.0,
                "outcome": "win",
            },
            {
                "id": 4,
                "strategy": "Test",
                "symbol": "A",
                "entry_time": "2024-01-01T13:00:00",
                "duration_minutes": 60,
                "pnl_usd": -10.0,
                "outcome": "loss",
            },
            {
                "id": 5,
                "strategy": "Test",
                "symbol": "A",
                "entry_time": "2024-01-01T14:00:00",
                "duration_minutes": 60,
                "pnl_usd": 15.0,
                "outcome": "win",
            },
        ]

        parser = MockDataParser(consecutive_trades)
        analytics = StrategyAnalytics(parser)
        metrics = analytics.get_strategy_performance("Test")

        # Max consecutive wins should be 3
        assert (
            metrics["max_consecutive_wins"] == 3
        ), f"Expected 3 consecutive wins, got {metrics['max_consecutive_wins']}"

        print(f"✓ test_consecutive_wins: {metrics['max_consecutive_wins']} == 3")

    def test_max_drawdown(self):
        """Test max drawdown calculation"""
        # Create trades with drawdown
        dd_trades = [
            {
                "id": 1,
                "strategy": "Test",
                "symbol": "A",
                "entry_time": "2024-01-01T10:00:00",
                "duration_minutes": 60,
                "pnl_usd": 100.0,
                "outcome": "win",
            },
            {
                "id": 2,
                "strategy": "Test",
                "symbol": "A",
                "entry_time": "2024-01-01T11:00:00",
                "duration_minutes": 60,
                "pnl_usd": 50.0,
                "outcome": "win",
            },
            {
                "id": 3,
                "strategy": "Test",
                "symbol": "A",
                "entry_time": "2024-01-01T12:00:00",
                "duration_minutes": 60,
                "pnl_usd": -100.0,
                "outcome": "loss",
            },
            {
                "id": 4,
                "strategy": "Test",
                "symbol": "A",
                "entry_time": "2024-01-01T13:00:00",
                "duration_minutes": 60,
                "pnl_usd": -50.0,
                "outcome": "loss",
            },
        ]

        parser = MockDataParser(dd_trades)
        analytics = StrategyAnalytics(parser)
        metrics = analytics.get_strategy_performance("Test")

        # Peak: 150, Trough: 0, Drawdown: 150
        expected_dd = 150.0
        assert (
            abs(metrics["max_drawdown"] - expected_dd) < 0.1
        ), f"Expected max drawdown {expected_dd}, got {metrics['max_drawdown']}"

        print(f"✓ test_max_drawdown: {metrics['max_drawdown']} ≈ {expected_dd}")

    def test_empty_strategy(self):
        """Test handling of strategy with no trades"""
        metrics = self.analytics.get_strategy_performance("NonExistent")

        assert metrics["total_trades"] == 0
        assert metrics["total_pnl"] == 0.0
        assert metrics["win_rate"] == 0.0

        print(f"✓ test_empty_strategy: Returns zero metrics")

    def test_all_strategies_performance(self):
        """Test getting performance for all strategies"""
        all_strategies = self.analytics.get_all_strategies_performance()

        # Should have 2 strategies (A and B)
        assert (
            len(all_strategies) == 2
        ), f"Expected 2 strategies, got {len(all_strategies)}"

        # Should be sorted by total_pnl descending
        assert (
            all_strategies[0]["total_pnl"] >= all_strategies[1]["total_pnl"]
        ), "Strategies not sorted by P&L descending"

        print(
            f"✓ test_all_strategies_performance: {len(all_strategies)} strategies, sorted"
        )


class TestMarketAnalytics:
    """Test suite for MarketAnalytics service"""

    def setup_method(self):
        """Setup test environment"""
        self.sample_trades = [
            {
                "id": 1,
                "strategy": "A",
                "symbol": "AAPL",
                "entry_time": "2024-01-01T10:00:00",
                "duration_minutes": 60,
                "pnl_usd": 100.0,
                "outcome": "win",
            },
            {
                "id": 2,
                "strategy": "A",
                "symbol": "AAPL",
                "entry_time": "2024-01-01T11:00:00",
                "duration_minutes": 60,
                "pnl_usd": 50.0,
                "outcome": "win",
            },
            {
                "id": 3,
                "strategy": "A",
                "symbol": "AAPL",
                "entry_time": "2024-01-01T12:00:00",
                "duration_minutes": 60,
                "pnl_usd": -25.0,
                "outcome": "loss",
            },
            {
                "id": 4,
                "strategy": "B",
                "symbol": "TSLA",
                "entry_time": "2024-01-01T13:00:00",
                "duration_minutes": 60,
                "pnl_usd": 75.0,
                "outcome": "win",
            },
            {
                "id": 5,
                "strategy": "B",
                "symbol": "TSLA",
                "entry_time": "2024-01-01T14:00:00",
                "duration_minutes": 60,
                "pnl_usd": -30.0,
                "outcome": "loss",
            },
            {
                "id": 6,
                "strategy": "B",
                "symbol": "TSLA",
                "entry_time": "2024-01-01T15:00:00",
                "duration_minutes": 60,
                "pnl_usd": -20.0,
                "outcome": "loss",
            },
        ]

        self.mock_parser = MockDataParser(self.sample_trades)
        self.analytics = MarketAnalytics(self.mock_parser)

    def test_market_grouping(self):
        """Test that trades are grouped by market"""
        markets = self.analytics.get_market_performance(min_trades=1)

        # Should have 2 markets
        assert len(markets) == 2, f"Expected 2 markets, got {len(markets)}"

        market_names = [m["market"] for m in markets]
        assert "AAPL" in market_names and "TSLA" in market_names

        print(f"✓ test_market_grouping: {len(markets)} markets grouped correctly")

    def test_market_win_rate(self):
        """Test win rate calculation per market"""
        markets = self.analytics.get_market_performance(min_trades=1)

        # Find AAPL market (2 wins, 1 loss = 66.67%)
        aapl = next(m for m in markets if m["market"] == "AAPL")
        expected_wr = 66.67
        assert (
            abs(aapl["win_rate"] - expected_wr) < 0.1
        ), f"Expected AAPL win rate {expected_wr}, got {aapl['win_rate']}"

        print(f"✓ test_market_win_rate: AAPL {aapl['win_rate']}% ≈ {expected_wr}%")

    def test_market_frequency(self):
        """Test frequency calculation (% of total trades)"""
        markets = self.analytics.get_market_performance(min_trades=1)

        # AAPL: 3/6 = 50%
        aapl = next(m for m in markets if m["market"] == "AAPL")
        expected_freq = 50.0
        assert (
            abs(aapl["frequency"] - expected_freq) < 0.1
        ), f"Expected AAPL frequency {expected_freq}, got {aapl['frequency']}"

        print(f"✓ test_market_frequency: AAPL {aapl['frequency']}% ≈ {expected_freq}%")

    def test_min_trades_filter(self):
        """Test filtering markets by minimum trades"""
        markets = self.analytics.get_market_performance(min_trades=5)

        # No market has 5+ trades, should return empty
        assert (
            len(markets) == 0
        ), f"Expected 0 markets with min_trades=5, got {len(markets)}"

        print(f"✓ test_min_trades_filter: Correctly filters markets")

    def test_top_markets(self):
        """Test getting top N markets"""
        top_markets = self.analytics.get_top_markets(n=1, metric="total_pnl")

        assert len(top_markets) == 1
        # AAPL should be top (125 vs 25)
        assert top_markets[0]["market"] == "AAPL"

        print(f"✓ test_top_markets: Top market is {top_markets[0]['market']}")

    def test_worst_markets(self):
        """Test getting worst N markets"""
        worst_markets = self.analytics.get_worst_markets(n=1, metric="total_pnl")

        assert len(worst_markets) == 1
        # TSLA should be worst (25 vs 125)
        assert worst_markets[0]["market"] == "TSLA"

        print(f"✓ test_worst_markets: Worst market is {worst_markets[0]['market']}")


class TestTimeAnalytics:
    """Test suite for TimeAnalytics service"""

    def setup_method(self):
        """Setup test environment"""
        # Create trades at different times
        self.sample_trades = [
            {
                "id": 1,
                "strategy": "A",
                "symbol": "AAPL",
                "entry_time": "2024-01-01T10:00:00",  # Monday, 10 AM
                "duration_minutes": 60,
                "pnl_usd": 100.0,
                "outcome": "win",
            },
            {
                "id": 2,
                "strategy": "A",
                "symbol": "AAPL",
                "entry_time": "2024-01-01T10:30:00",  # Monday, 10 AM
                "duration_minutes": 60,
                "pnl_usd": 50.0,
                "outcome": "win",
            },
            {
                "id": 3,
                "strategy": "A",
                "symbol": "AAPL",
                "entry_time": "2024-01-01T14:00:00",  # Monday, 2 PM
                "duration_minutes": 60,
                "pnl_usd": -25.0,
                "outcome": "loss",
            },
            {
                "id": 4,
                "strategy": "B",
                "symbol": "TSLA",
                "entry_time": "2024-01-02T10:00:00",  # Tuesday, 10 AM
                "duration_minutes": 60,
                "pnl_usd": 75.0,
                "outcome": "win",
            },
        ]

        self.mock_parser = MockDataParser(self.sample_trades)
        self.analytics = TimeAnalytics(self.mock_parser)

    def test_hour_analysis_structure(self):
        """Test hour analysis returns correct structure"""
        analysis = self.analytics.get_hour_of_day_analysis()

        assert "hours" in analysis
        assert "trades_per_hour" in analysis
        assert "pnl_per_hour" in analysis
        assert "win_rate_per_hour" in analysis

        # Should have 24 hours
        assert len(analysis["hours"]) == 24
        assert len(analysis["pnl_per_hour"]) == 24

        print(f"✓ test_hour_analysis_structure: 24 hours with all metrics")

    def test_hour_grouping(self):
        """Test trades are grouped by hour correctly"""
        analysis = self.analytics.get_hour_of_day_analysis()

        # Hour 10 should have 3 trades
        hour_10_trades = analysis["trades_per_hour"][10]
        assert (
            hour_10_trades == 3
        ), f"Expected 3 trades at hour 10, got {hour_10_trades}"

        # Hour 14 should have 1 trade
        hour_14_trades = analysis["trades_per_hour"][14]
        assert hour_14_trades == 1, f"Expected 1 trade at hour 14, got {hour_14_trades}"

        print(f"✓ test_hour_grouping: Trades grouped correctly by hour")

    def test_day_analysis_structure(self):
        """Test day of week analysis returns correct structure"""
        analysis = self.analytics.get_day_of_week_analysis()

        assert "days" in analysis
        assert "day_names" in analysis
        assert "trades_per_day" in analysis
        assert "pnl_per_day" in analysis

        # Should have 7 days
        assert len(analysis["days"]) == 7
        assert len(analysis["day_names"]) == 7

        print(f"✓ test_day_analysis_structure: 7 days with all metrics")

    def test_monthly_performance(self):
        """Test monthly performance grouping"""
        months = self.analytics.get_monthly_performance()

        # Should have 1 month (2024-01)
        assert len(months) == 1, f"Expected 1 month, got {len(months)}"
        assert months[0]["month"] == "2024-01"
        assert months[0]["total_trades"] == 4

        print(f"✓ test_monthly_performance: {len(months)} month(s) grouped")

    def test_best_trading_times(self):
        """Test best trading times identification"""
        best_times = self.analytics.get_best_trading_times()

        assert "top_hours" in best_times
        assert "top_days" in best_times

        # Should return top 5 hours and top 3 days
        assert len(best_times["top_hours"]) <= 5
        assert len(best_times["top_days"]) <= 3

        print(
            f"✓ test_best_trading_times: {len(best_times['top_hours'])} hours, {len(best_times['top_days'])} days"
        )


class TestRiskMetrics:
    """Test suite for RiskMetrics service"""

    def setup_method(self):
        """Setup test environment"""
        # Create trades with known returns for risk calculations
        self.sample_trades = [
            {
                "id": 1,
                "strategy": "A",
                "symbol": "AAPL",
                "entry_time": "2024-01-01T10:00:00",
                "duration_minutes": 60,
                "pnl_usd": 100.0,
                "pnl_pct": 2.0,
                "outcome": "win",
            },
            {
                "id": 2,
                "strategy": "A",
                "symbol": "AAPL",
                "entry_time": "2024-01-02T10:00:00",
                "duration_minutes": 60,
                "pnl_usd": -50.0,
                "pnl_pct": -1.0,
                "outcome": "loss",
            },
            {
                "id": 3,
                "strategy": "A",
                "symbol": "AAPL",
                "entry_time": "2024-01-03T10:00:00",
                "duration_minutes": 60,
                "pnl_usd": 75.0,
                "pnl_pct": 1.5,
                "outcome": "win",
            },
            {
                "id": 4,
                "strategy": "A",
                "symbol": "AAPL",
                "entry_time": "2024-01-04T10:00:00",
                "duration_minutes": 60,
                "pnl_usd": 50.0,
                "pnl_pct": 1.0,
                "outcome": "win",
            },
            {
                "id": 5,
                "strategy": "A",
                "symbol": "AAPL",
                "entry_time": "2024-01-05T10:00:00",
                "duration_minutes": 60,
                "pnl_usd": -25.0,
                "pnl_pct": -0.5,
                "outcome": "loss",
            },
        ]

        self.mock_parser = MockDataParser(self.sample_trades)
        self.risk_metrics = RiskMetrics(self.mock_parser)

    def test_all_risk_metrics_present(self):
        """Test that all risk metrics are calculated"""
        metrics = self.risk_metrics.calculate_all_risk_metrics()

        required_keys = [
            "sharpe_ratio",
            "sortino_ratio",
            "var_95",
            "var_99",
            "max_drawdown",
            "max_drawdown_pct",
            "calmar_ratio",
            "std_deviation",
            "downside_deviation",
            "annualized_return",
            "total_return",
            "mean_return",
        ]

        for key in required_keys:
            assert key in metrics, f"Missing risk metric: {key}"

        print(f"✓ test_all_risk_metrics_present: All 12 metrics present")

    def test_sharpe_ratio_calculation(self):
        """Test Sharpe ratio calculation"""
        metrics = self.risk_metrics.calculate_all_risk_metrics()

        # Sharpe should be calculated (positive mean return, positive std dev)
        assert "sharpe_ratio" in metrics
        # Just verify it's a reasonable number (not inf or nan)
        assert -10 < metrics["sharpe_ratio"] < 10

        print(f"✓ test_sharpe_ratio_calculation: {metrics['sharpe_ratio']}")

    def test_max_drawdown_calculation(self):
        """Test max drawdown calculation"""
        metrics = self.risk_metrics.calculate_all_risk_metrics()

        # Max drawdown should be positive
        assert metrics["max_drawdown"] >= 0

        print(f"✓ test_max_drawdown_calculation: ${metrics['max_drawdown']}")

    def test_var_calculation(self):
        """Test VaR (Value at Risk) calculation"""
        metrics = self.risk_metrics.calculate_all_risk_metrics()

        # VaR should be calculated
        assert "var_95" in metrics
        assert "var_99" in metrics

        # VaR 99% should be more extreme than VaR 95%
        assert metrics["var_99"] <= metrics["var_95"]

        print(
            f"✓ test_var_calculation: VaR 95%=${metrics['var_95']}, VaR 99%=${metrics['var_99']}"
        )

    def test_insufficient_data(self):
        """Test handling of insufficient data (< 2 trades)"""
        single_trade = [self.sample_trades[0]]
        parser = MockDataParser(single_trade)
        risk = RiskMetrics(parser)

        metrics = risk.calculate_all_risk_metrics()

        # Should return zero metrics
        assert metrics["sharpe_ratio"] == 0.0
        assert metrics["max_drawdown"] == 0.0

        print(f"✓ test_insufficient_data: Returns zero metrics")

    def test_drawdown_history(self):
        """Test drawdown history calculation"""
        history = self.risk_metrics.calculate_drawdown_history()

        assert "dates" in history
        assert "drawdown_pct" in history
        assert "drawdown_usd" in history

        # Should have same length as trades
        assert len(history["dates"]) == len(self.sample_trades)

        print(f"✓ test_drawdown_history: {len(history['dates'])} data points")


def run_all_tests():
    """Run all test suites"""
    print("\n" + "=" * 60)
    print("RUNNING ANALYTICS SERVICES TEST SUITE")
    print("=" * 60 + "\n")

    # Test StrategyAnalytics
    print("\n--- Testing StrategyAnalytics ---")
    strategy_tests = TestStrategyAnalytics()
    test_methods = [m for m in dir(strategy_tests) if m.startswith("test_")]
    for method_name in test_methods:
        strategy_tests.setup_method()
        getattr(strategy_tests, method_name)()

    # Test MarketAnalytics
    print("\n--- Testing MarketAnalytics ---")
    market_tests = TestMarketAnalytics()
    test_methods = [m for m in dir(market_tests) if m.startswith("test_")]
    for method_name in test_methods:
        market_tests.setup_method()
        getattr(market_tests, method_name)()

    # Test TimeAnalytics
    print("\n--- Testing TimeAnalytics ---")
    time_tests = TestTimeAnalytics()
    test_methods = [m for m in dir(time_tests) if m.startswith("test_")]
    for method_name in test_methods:
        time_tests.setup_method()
        getattr(time_tests, method_name)()

    # Test RiskMetrics
    print("\n--- Testing RiskMetrics ---")
    risk_tests = TestRiskMetrics()
    test_methods = [m for m in dir(risk_tests) if m.startswith("test_")]
    for method_name in test_methods:
        risk_tests.setup_method()
        getattr(risk_tests, method_name)()

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED ✓")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    run_all_tests()
