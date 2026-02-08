"""
Unit Tests for Dashboard Calculations

Tests all P&L calculations, win rate, cumulative P&L, and other metrics
to ensure mathematical accuracy using Decimal precision.

All calculations MUST use Decimal for money to avoid floating point errors.
"""

import sys
import os
from pathlib import Path
from decimal import Decimal

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dashboard.services.data_parser import DataParser


class TestCalculations:
    """Test suite for all dashboard calculations"""
    
    def setup_method(self):
        """Setup test environment"""
        # Create a temporary logs directory for testing
        self.test_logs_dir = Path(__file__).parent / 'test_logs'
        self.test_logs_dir.mkdir(exist_ok=True)
        self.data_parser = DataParser(self.test_logs_dir)
    
    def test_total_pnl_calculation(self):
        """Test total P&L calculation with known values"""
        trades = [
            {'pnl_usd': 10.50},
            {'pnl_usd': -5.25},
            {'pnl_usd': 20.00},
            {'pnl_usd': -3.50}
        ]
        
        expected = 21.75
        actual = self.data_parser.calculate_total_pnl(trades)
        
        assert abs(actual - expected) < 0.01, f"Expected {expected}, got {actual}"
        print(f"✓ test_total_pnl_calculation: {actual} == {expected}")
    
    def test_total_pnl_empty(self):
        """Test with zero trades"""
        result = self.data_parser.calculate_total_pnl([])
        assert result == 0.0, f"Expected 0.0 for empty trades, got {result}"
        print(f"✓ test_total_pnl_empty: {result} == 0.0")
    
    def test_total_pnl_single_trade(self):
        """Test with single trade"""
        trades = [{'pnl_usd': 15.50}]
        result = self.data_parser.calculate_total_pnl(trades)
        assert abs(result - 15.50) < 0.01, f"Expected 15.50, got {result}"
        print(f"✓ test_total_pnl_single_trade: {result} == 15.50")
    
    def test_win_rate_calculation(self):
        """Test win rate with known values"""
        trades = [
            {'pnl_usd': 10.00},  # Win
            {'pnl_usd': -5.00},  # Loss
            {'pnl_usd': 8.00},   # Win
            {'pnl_usd': 12.00}   # Win
        ]
        
        expected = 75.0  # 3 wins out of 4 = 75%
        actual = self.data_parser.calculate_win_rate(trades)
        
        assert actual == expected, f"Expected {expected}%, got {actual}%"
        print(f"✓ test_win_rate_calculation: {actual}% == {expected}%")
    
    def test_win_rate_all_wins(self):
        """Test with 100% win rate"""
        trades = [{'pnl_usd': 10}, {'pnl_usd': 5}, {'pnl_usd': 8}]
        result = self.data_parser.calculate_win_rate(trades)
        assert result == 100.0, f"Expected 100%, got {result}%"
        print(f"✓ test_win_rate_all_wins: {result}% == 100.0%")
    
    def test_win_rate_all_losses(self):
        """Test with 0% win rate"""
        trades = [{'pnl_usd': -10}, {'pnl_usd': -5}, {'pnl_usd': -8}]
        result = self.data_parser.calculate_win_rate(trades)
        assert result == 0.0, f"Expected 0%, got {result}%"
        print(f"✓ test_win_rate_all_losses: {result}% == 0.0%")
    
    def test_win_rate_empty(self):
        """Test win rate with empty trades"""
        result = self.data_parser.calculate_win_rate([])
        assert result == 0.0, f"Expected 0% for empty trades, got {result}%"
        print(f"✓ test_win_rate_empty: {result}% == 0.0%")
    
    def test_average_pnl(self):
        """Test average P&L calculation"""
        trades = [
            {'pnl_usd': 10.00},
            {'pnl_usd': 20.00},
            {'pnl_usd': 30.00}
        ]
        
        expected = 20.00  # (10 + 20 + 30) / 3
        actual = self.data_parser.calculate_average_pnl(trades)
        
        assert abs(actual - expected) < 0.01, f"Expected {expected}, got {actual}"
        print(f"✓ test_average_pnl: {actual} == {expected}")
    
    def test_average_pnl_empty(self):
        """Test average P&L with empty trades"""
        result = self.data_parser.calculate_average_pnl([])
        assert result == 0.0, f"Expected 0.0 for empty trades, got {result}"
        print(f"✓ test_average_pnl_empty: {result} == 0.0")
    
    def test_daily_pnl_chart_data(self):
        """Test daily P&L chart data preparation"""
        trades = [
            {'entry_time': '2026-02-01T10:00:00', 'pnl_usd': 10.00},
            {'entry_time': '2026-02-01T11:00:00', 'pnl_usd': 5.00},
            {'entry_time': '2026-02-02T10:00:00', 'pnl_usd': -3.00},
            {'entry_time': '2026-02-03T10:00:00', 'pnl_usd': 8.00}
        ]
        
        result = self.data_parser.prepare_daily_pnl_chart_data(trades)
        
        # Should have 3 days (Feb 1, 2, 3)
        assert len(result['labels']) == 3, f"Expected 3 days, got {len(result['labels'])}"
        assert len(result['data']) == 3, f"Expected 3 data points, got {len(result['data'])}"
        
        # Day 1: 10 + 5 = 15
        # Day 2: -3
        # Day 3: 8
        expected_values = [15.0, -3.0, 8.0]
        
        for i, (actual, expected) in enumerate(zip(result['data'], expected_values)):
            assert abs(actual - expected) < 0.01, \
                f"Day {i+1}: Expected {expected}, got {actual}"
        
        # Verify sum equals total P&L
        total_pnl = self.data_parser.calculate_total_pnl(trades)
        daily_sum = sum(result['data'])
        assert abs(daily_sum - total_pnl) < 0.01, \
            f"Daily sum ({daily_sum}) doesn't match total P&L ({total_pnl})"
        
        print(f"✓ test_daily_pnl_chart_data: 3 days, values {expected_values}")
    
    def test_cumulative_pnl_chart_data(self):
        """Test cumulative P&L calculation"""
        trades = [
            {'entry_time': '2026-02-01T10:00:00', 'pnl_usd': 10.00},
            {'entry_time': '2026-02-01T11:00:00', 'pnl_usd': 5.00},
            {'entry_time': '2026-02-02T10:00:00', 'pnl_usd': -3.00},
            {'entry_time': '2026-02-03T10:00:00', 'pnl_usd': 8.00}
        ]
        
        result = self.data_parser.prepare_cumulative_pnl_chart_data(trades)
        
        # Day 1: 10 + 5 = 15
        # Day 2: 15 - 3 = 12
        # Day 3: 12 + 8 = 20
        
        expected_cumulative = [15.0, 12.0, 20.0]
        
        assert len(result['data']) == len(expected_cumulative), \
            f"Expected {len(expected_cumulative)} points, got {len(result['data'])}"
        
        for i, (actual, expected) in enumerate(zip(result['data'], expected_cumulative)):
            assert abs(actual - expected) < 0.01, \
                f"Point {i+1}: Expected {expected}, got {actual}"
        
        # Final point must equal total P&L
        total_pnl = self.data_parser.calculate_total_pnl(trades)
        final_point = result['data'][-1]
        assert abs(final_point - total_pnl) < 0.01, \
            f"Final cumulative ({final_point}) doesn't match total P&L ({total_pnl})"
        
        print(f"✓ test_cumulative_pnl_chart_data: {expected_cumulative}, final={total_pnl}")
    
    def test_cumulative_pnl_empty(self):
        """Test cumulative P&L with empty trades"""
        result = self.data_parser.prepare_cumulative_pnl_chart_data([])
        assert result['labels'] == [], "Expected empty labels for empty trades"
        assert result['data'] == [], "Expected empty data for empty trades"
        print(f"✓ test_cumulative_pnl_empty: empty result for empty trades")
    
    def test_arbitrage_profit_percentage(self):
        """Test arbitrage profit % calculation"""
        # Yes = 0.48, No = 0.48, Sum = 0.96
        # Profit % = ((1.00 - 0.96) / 0.96) * 100 = 4.17%
        
        yes_price = 0.48
        no_price = 0.48
        
        expected = 4.17
        actual = self.data_parser.calculate_arbitrage_profit_pct(yes_price, no_price)
        
        assert abs(actual - expected) < 0.01, \
            f"Expected {expected}%, got {actual}%"
        print(f"✓ test_arbitrage_profit_percentage: {actual}% ≈ {expected}%")
    
    def test_no_arbitrage_opportunity(self):
        """Test when sum >= 1.00 (no opportunity)"""
        yes_price = 0.51
        no_price = 0.50
        
        actual = self.data_parser.calculate_arbitrage_profit_pct(yes_price, no_price)
        assert actual == 0.0, f"Expected 0% when no opportunity, got {actual}%"
        print(f"✓ test_no_arbitrage_opportunity: {actual}% == 0.0%")
    
    def test_decimal_precision(self):
        """Test that Decimal prevents floating point errors"""
        # Classic floating point error case
        trades = [
            {'pnl_usd': 0.1},
            {'pnl_usd': 0.2}
        ]
        
        result = self.data_parser.calculate_total_pnl(trades)
        expected = 0.3
        
        # With float, 0.1 + 0.2 != 0.3 exactly
        # With Decimal, it should be exactly 0.3
        assert result == expected, f"Decimal precision failed: {result} != {expected}"
        print(f"✓ test_decimal_precision: {result} == {expected} (no float error)")
    
    def test_dates_unique_in_daily_chart(self):
        """Test that each date appears exactly once in daily chart"""
        trades = [
            {'entry_time': '2026-02-01T10:00:00', 'pnl_usd': 10.00},
            {'entry_time': '2026-02-01T14:00:00', 'pnl_usd': 5.00},
            {'entry_time': '2026-02-01T18:00:00', 'pnl_usd': 3.00},
            {'entry_time': '2026-02-02T10:00:00', 'pnl_usd': -2.00},
        ]
        
        result = self.data_parser.prepare_daily_pnl_chart_data(trades)
        
        # Should have 2 unique dates (Feb 1 and Feb 2)
        assert len(result['labels']) == 2, \
            f"Expected 2 unique dates, got {len(result['labels'])}"
        
        # Each date should appear exactly once
        assert len(result['labels']) == len(set(result['labels'])), \
            "Dates are not unique!"
        
        # Feb 1 should sum to 18, Feb 2 should be -2
        assert abs(result['data'][0] - 18.0) < 0.01, \
            f"Expected 18.0 for Feb 1, got {result['data'][0]}"
        assert abs(result['data'][1] - (-2.0)) < 0.01, \
            f"Expected -2.0 for Feb 2, got {result['data'][1]}"
        
        print(f"✓ test_dates_unique_in_daily_chart: 2 unique dates, aggregated correctly")


def run_all_tests():
    """Run all tests and report results"""
    test_suite = TestCalculations()
    test_suite.setup_method()
    
    tests = [
        test_suite.test_total_pnl_calculation,
        test_suite.test_total_pnl_empty,
        test_suite.test_total_pnl_single_trade,
        test_suite.test_win_rate_calculation,
        test_suite.test_win_rate_all_wins,
        test_suite.test_win_rate_all_losses,
        test_suite.test_win_rate_empty,
        test_suite.test_average_pnl,
        test_suite.test_average_pnl_empty,
        test_suite.test_daily_pnl_chart_data,
        test_suite.test_cumulative_pnl_chart_data,
        test_suite.test_cumulative_pnl_empty,
        test_suite.test_arbitrage_profit_percentage,
        test_suite.test_no_arbitrage_opportunity,
        test_suite.test_decimal_precision,
        test_suite.test_dates_unique_in_daily_chart,
    ]
    
    passed = 0
    failed = 0
    
    print("\n" + "="*70)
    print("RUNNING CALCULATION TESTS")
    print("="*70 + "\n")
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"✗ {test.__name__}: FAILED - {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__}: ERROR - {e}")
            failed += 1
    
    print("\n" + "="*70)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("="*70 + "\n")
    
    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
