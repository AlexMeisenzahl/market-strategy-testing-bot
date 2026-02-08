"""
Unit Tests for ArbitrageTracker

Tests all tracking functionality including opportunity recording,
execution tracking, metrics calculations, and summary formatting.
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from strategies.arbitrage_tracker import ArbitrageTracker


class TestArbitrageTracker:
    """Test suite for ArbitrageTracker"""
    
    def setup_method(self):
        """Setup test environment"""
        self.tracker = ArbitrageTracker()
    
    def test_initial_state(self):
        """Test tracker starts with zero metrics"""
        assert self.tracker.opportunities_found == 0, "Should start with 0 opportunities"
        assert self.tracker.opportunities_executed == 0, "Should start with 0 executions"
        assert self.tracker.total_profit == 0.0, "Should start with $0 profit"
        assert self.tracker.total_loss == 0.0, "Should start with $0 loss"
        assert self.tracker.win_rate == 0.0, "Should start with 0% win rate"
        assert self.tracker.average_profit == 0.0, "Should start with $0 average"
        assert len(self.tracker.execution_history) == 0, "Should start with empty history"
        print("✓ test_initial_state: All metrics initialized to zero")
    
    def test_record_opportunity_increments_counter(self):
        """Test recording opportunities increments counter"""
        opportunity1 = {
            'market_id': 'market_1',
            'market_name': 'Test Market 1',
            'yes_price': 0.45,
            'no_price': 0.48
        }
        
        opportunity2 = {
            'market_id': 'market_2',
            'market_name': 'Test Market 2',
            'yes_price': 0.40,
            'no_price': 0.50
        }
        
        self.tracker.record_opportunity(opportunity1)
        assert self.tracker.opportunities_found == 1, "Should have 1 opportunity"
        
        self.tracker.record_opportunity(opportunity2)
        assert self.tracker.opportunities_found == 2, "Should have 2 opportunities"
        
        print("✓ test_record_opportunity_increments_counter: Counter works correctly")
    
    def test_record_execution_updates_profit(self):
        """Test recording profitable execution updates profit"""
        result = {
            'market_id': 'market_1',
            'market_name': 'Test Market',
            'profit': 10.50
        }
        
        self.tracker.record_execution(result)
        
        assert self.tracker.opportunities_executed == 1, "Should have 1 execution"
        assert self.tracker.total_profit == 10.50, "Should have $10.50 profit"
        assert self.tracker.total_loss == 0.0, "Should have $0 loss"
        assert len(self.tracker.execution_history) == 1, "Should have 1 history record"
        
        print("✓ test_record_execution_updates_profit: Profit tracked correctly")
    
    def test_record_execution_updates_loss(self):
        """Test recording losing execution updates loss"""
        result = {
            'market_id': 'market_1',
            'market_name': 'Test Market',
            'profit': -5.25
        }
        
        self.tracker.record_execution(result)
        
        assert self.tracker.opportunities_executed == 1, "Should have 1 execution"
        assert self.tracker.total_profit == 0.0, "Should have $0 profit"
        assert self.tracker.total_loss == 5.25, "Should have $5.25 loss"
        assert len(self.tracker.execution_history) == 1, "Should have 1 history record"
        
        print("✓ test_record_execution_updates_loss: Loss tracked correctly")
    
    def test_win_rate_calculation_accurate(self):
        """Test win rate calculation is accurate"""
        # Record 3 wins and 1 loss
        self.tracker.record_execution({'market_id': 'm1', 'market_name': 'M1', 'profit': 10.0})
        self.tracker.record_execution({'market_id': 'm2', 'market_name': 'M2', 'profit': 5.0})
        self.tracker.record_execution({'market_id': 'm3', 'market_name': 'M3', 'profit': -3.0})
        self.tracker.record_execution({'market_id': 'm4', 'market_name': 'M4', 'profit': 8.0})
        
        expected_win_rate = 75.0  # 3 wins out of 4 = 75%
        actual_win_rate = self.tracker.win_rate
        
        assert actual_win_rate == expected_win_rate, \
            f"Expected {expected_win_rate}% win rate, got {actual_win_rate}%"
        
        print(f"✓ test_win_rate_calculation_accurate: {actual_win_rate}% == {expected_win_rate}%")
    
    def test_win_rate_all_wins(self):
        """Test 100% win rate"""
        self.tracker.record_execution({'market_id': 'm1', 'market_name': 'M1', 'profit': 10.0})
        self.tracker.record_execution({'market_id': 'm2', 'market_name': 'M2', 'profit': 5.0})
        self.tracker.record_execution({'market_id': 'm3', 'market_name': 'M3', 'profit': 8.0})
        
        assert self.tracker.win_rate == 100.0, "Expected 100% win rate"
        print("✓ test_win_rate_all_wins: 100% win rate calculated correctly")
    
    def test_win_rate_all_losses(self):
        """Test 0% win rate"""
        self.tracker.record_execution({'market_id': 'm1', 'market_name': 'M1', 'profit': -10.0})
        self.tracker.record_execution({'market_id': 'm2', 'market_name': 'M2', 'profit': -5.0})
        
        assert self.tracker.win_rate == 0.0, "Expected 0% win rate"
        print("✓ test_win_rate_all_losses: 0% win rate calculated correctly")
    
    def test_average_profit_calculation(self):
        """Test average profit calculation"""
        self.tracker.record_execution({'market_id': 'm1', 'market_name': 'M1', 'profit': 10.0})
        self.tracker.record_execution({'market_id': 'm2', 'market_name': 'M2', 'profit': 20.0})
        self.tracker.record_execution({'market_id': 'm3', 'market_name': 'M3', 'profit': 30.0})
        
        expected_average = 20.0  # (10 + 20 + 30) / 3
        actual_average = self.tracker.average_profit
        
        assert abs(actual_average - expected_average) < 0.01, \
            f"Expected ${expected_average} average, got ${actual_average}"
        
        print(f"✓ test_average_profit_calculation: ${actual_average} == ${expected_average}")
    
    def test_average_profit_with_losses(self):
        """Test average profit with mixed wins and losses"""
        self.tracker.record_execution({'market_id': 'm1', 'market_name': 'M1', 'profit': 10.0})
        self.tracker.record_execution({'market_id': 'm2', 'market_name': 'M2', 'profit': -5.0})
        self.tracker.record_execution({'market_id': 'm3', 'market_name': 'M3', 'profit': 8.0})
        
        # Net profit = 10 - 5 + 8 = 13
        # Average = 13 / 3 = 4.33
        expected_average = 4.33
        actual_average = self.tracker.average_profit
        
        assert abs(actual_average - expected_average) < 0.01, \
            f"Expected ${expected_average} average, got ${actual_average}"
        
        print(f"✓ test_average_profit_with_losses: ${actual_average:.2f} ≈ ${expected_average}")
    
    def test_average_profit_handles_zero_executions(self):
        """Test average profit returns 0 when no executions"""
        assert self.tracker.average_profit == 0.0, \
            "Average profit should be 0 when no executions"
        
        print("✓ test_average_profit_handles_zero_executions: Returns 0 for empty history")
    
    def test_reset_metrics_clears_all(self):
        """Test reset clears all metrics"""
        # Add some data
        self.tracker.record_opportunity({'market_id': 'm1', 'market_name': 'M1'})
        self.tracker.record_execution({'market_id': 'm1', 'market_name': 'M1', 'profit': 10.0})
        
        # Verify data exists
        assert self.tracker.opportunities_found > 0
        assert self.tracker.opportunities_executed > 0
        assert self.tracker.total_profit > 0
        
        # Reset
        self.tracker.reset_metrics()
        
        # Verify everything is cleared
        assert self.tracker.opportunities_found == 0, "opportunities_found should be 0"
        assert self.tracker.opportunities_executed == 0, "opportunities_executed should be 0"
        assert self.tracker.total_profit == 0.0, "total_profit should be 0"
        assert self.tracker.total_loss == 0.0, "total_loss should be 0"
        assert len(self.tracker.execution_history) == 0, "execution_history should be empty"
        
        print("✓ test_reset_metrics_clears_all: All metrics reset to zero")
    
    def test_get_metrics_returns_valid_data(self):
        """Test get_metrics returns complete metrics dictionary"""
        self.tracker.record_opportunity({'market_id': 'm1', 'market_name': 'M1'})
        self.tracker.record_execution({'market_id': 'm1', 'market_name': 'M1', 'profit': 15.0})
        
        metrics = self.tracker.get_metrics()
        
        # Check all expected keys exist
        expected_keys = [
            'opportunities_found', 'opportunities_executed', 
            'total_profit', 'total_loss', 'net_profit',
            'win_rate', 'average_profit', 'start_time',
            'running_time_hours', 'running_time_minutes',
            'execution_history'
        ]
        
        for key in expected_keys:
            assert key in metrics, f"Missing key: {key}"
        
        # Check values
        assert metrics['opportunities_found'] == 1
        assert metrics['opportunities_executed'] == 1
        assert metrics['total_profit'] == 15.0
        assert metrics['net_profit'] == 15.0
        
        print("✓ test_get_metrics_returns_valid_data: All metrics keys present and accurate")
    
    def test_export_summary_formats_correctly(self):
        """Test export summary creates readable output"""
        self.tracker.record_opportunity({'market_id': 'm1', 'market_name': 'M1'})
        self.tracker.record_opportunity({'market_id': 'm2', 'market_name': 'M2'})
        self.tracker.record_execution({'market_id': 'm1', 'market_name': 'M1', 'profit': 10.0})
        
        summary = self.tracker.export_summary()
        
        # Check format
        assert "=== ARBITRAGE PERFORMANCE ===" in summary, "Should have header"
        assert "Opportunities Found: 2" in summary, "Should show opportunities found"
        assert "Opportunities Executed: 1" in summary, "Should show executions"
        assert "Win Rate:" in summary, "Should show win rate"
        assert "Total Profit:" in summary, "Should show total profit"
        assert "Average Profit:" in summary, "Should show average profit"
        assert "Running Time:" in summary, "Should show running time"
        assert "============================" in summary, "Should have footer"
        
        print("✓ test_export_summary_formats_correctly: Summary formatted properly")
        print("\nExample output:")
        print(summary)
    
    def test_execution_history_stored(self):
        """Test execution history maintains all executions"""
        result1 = {'market_id': 'm1', 'market_name': 'Market 1', 'profit': 10.0}
        result2 = {'market_id': 'm2', 'market_name': 'Market 2', 'profit': -5.0}
        result3 = {'market_id': 'm3', 'market_name': 'Market 3', 'profit': 8.0}
        
        self.tracker.record_execution(result1)
        self.tracker.record_execution(result2)
        self.tracker.record_execution(result3)
        
        history = self.tracker.execution_history
        
        assert len(history) == 3, "Should have 3 history records"
        assert history[0]['market_id'] == 'm1', "First record should be m1"
        assert history[1]['profit'] == -5.0, "Second record profit should be -5.0"
        assert history[2]['market_name'] == 'Market 3', "Third record name should be Market 3"
        
        print("✓ test_execution_history_stored: History maintains all executions")
    
    def test_net_profit_calculation(self):
        """Test net profit is calculated correctly"""
        self.tracker.record_execution({'market_id': 'm1', 'market_name': 'M1', 'profit': 20.0})
        self.tracker.record_execution({'market_id': 'm2', 'market_name': 'M2', 'profit': 15.0})
        self.tracker.record_execution({'market_id': 'm3', 'market_name': 'M3', 'profit': -8.0})
        
        metrics = self.tracker.get_metrics()
        
        # Total profit: 20 + 15 = 35
        # Total loss: 8
        # Net profit: 35 - 8 = 27
        expected_net_profit = 27.0
        
        assert metrics['total_profit'] == 35.0, "Total profit should be 35"
        assert metrics['total_loss'] == 8.0, "Total loss should be 8"
        assert metrics['net_profit'] == expected_net_profit, \
            f"Net profit should be {expected_net_profit}"
        
        print(f"✓ test_net_profit_calculation: Net profit ${metrics['net_profit']} == ${expected_net_profit}")


def run_all_tests():
    """Run all tests and report results"""
    test_suite = TestArbitrageTracker()
    
    tests = [
        test_suite.test_initial_state,
        test_suite.test_record_opportunity_increments_counter,
        test_suite.test_record_execution_updates_profit,
        test_suite.test_record_execution_updates_loss,
        test_suite.test_win_rate_calculation_accurate,
        test_suite.test_win_rate_all_wins,
        test_suite.test_win_rate_all_losses,
        test_suite.test_average_profit_calculation,
        test_suite.test_average_profit_with_losses,
        test_suite.test_average_profit_handles_zero_executions,
        test_suite.test_reset_metrics_clears_all,
        test_suite.test_get_metrics_returns_valid_data,
        test_suite.test_export_summary_formats_correctly,
        test_suite.test_execution_history_stored,
        test_suite.test_net_profit_calculation,
    ]
    
    passed = 0
    failed = 0
    
    print("\n" + "="*70)
    print("RUNNING ARBITRAGE TRACKER TESTS")
    print("="*70 + "\n")
    
    for test in tests:
        try:
            test_suite.setup_method()  # Reset for each test
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
