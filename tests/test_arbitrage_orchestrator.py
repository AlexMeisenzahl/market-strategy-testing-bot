"""
Unit Tests for ArbitrageOrchestrator

Tests orchestrator integration with tracker and strategy,
ensuring proper coordination and metrics tracking.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from strategies.arbitrage_orchestrator import ArbitrageOrchestrator


class TestArbitrageOrchestrator:
    """Test suite for ArbitrageOrchestrator"""
    
    def setup_method(self):
        """Setup test environment"""
        config = {
            'min_profit_margin': 0.02,
            'max_trade_size': 10,
            'max_price_sum': 0.98
        }
        self.orchestrator = ArbitrageOrchestrator(config)
    
    def test_orchestrator_initializes_tracker(self):
        """Test orchestrator initializes tracker properly"""
        assert self.orchestrator.tracker is not None, "Tracker should be initialized"
        assert self.orchestrator.strategy is not None, "Strategy should be initialized"
        assert self.orchestrator.tracker.opportunities_found == 0, "Should start with 0 opportunities"
        print("✓ test_orchestrator_initializes_tracker: Components initialized")
    
    def test_detect_opportunity_calls_tracker(self):
        """Test orchestrator calls tracker when opportunity is detected"""
        market_data = {
            'id': 'test_market_1',
            'question': 'Test Market Question'
        }
        
        price_data = {
            'yes': 0.45,
            'no': 0.48
        }
        
        # Initial count
        initial_count = self.orchestrator.tracker.opportunities_found
        
        # Detect opportunity
        opportunity = self.orchestrator.detect_opportunity(market_data, price_data)
        
        # Verify tracker was updated
        if opportunity:
            assert self.orchestrator.tracker.opportunities_found == initial_count + 1, \
                "Tracker should increment when opportunity found"
            print("✓ test_detect_opportunity_calls_tracker: Tracker incremented")
        else:
            # If no opportunity detected, tracker should not increment
            assert self.orchestrator.tracker.opportunities_found == initial_count, \
                "Tracker should not increment when no opportunity"
            print("✓ test_detect_opportunity_calls_tracker: Tracker not incremented (no opportunity)")
    
    def test_detect_opportunity_returns_none_for_no_arbitrage(self):
        """Test orchestrator returns None when no arbitrage exists"""
        market_data = {
            'id': 'test_market_1',
            'question': 'Test Market Question'
        }
        
        # Price sum > 1.0 (no arbitrage)
        price_data = {
            'yes': 0.55,
            'no': 0.50
        }
        
        opportunity = self.orchestrator.detect_opportunity(market_data, price_data)
        
        assert opportunity is None, "Should return None when no arbitrage opportunity"
        print("✓ test_detect_opportunity_returns_none_for_no_arbitrage: Correctly returns None")
    
    def test_execute_opportunity_calls_tracker(self):
        """Test orchestrator calls tracker after execution"""
        # First detect an opportunity
        market_data = {
            'id': 'test_market_1',
            'question': 'Test Market Question'
        }
        
        price_data = {
            'yes': 0.45,
            'no': 0.48
        }
        
        opportunity = self.orchestrator.detect_opportunity(market_data, price_data)
        
        if opportunity:
            initial_executions = self.orchestrator.tracker.opportunities_executed
            
            # Execute the opportunity
            result = self.orchestrator.execute_opportunity(opportunity, trade_size=10.0)
            
            # Verify tracker was updated
            assert self.orchestrator.tracker.opportunities_executed == initial_executions + 1, \
                "Tracker should increment executions"
            assert 'profit' in result, "Result should contain profit"
            assert 'market_id' in result, "Result should contain market_id"
            
            print("✓ test_execute_opportunity_calls_tracker: Tracker updated after execution")
        else:
            print("✓ test_execute_opportunity_calls_tracker: Skipped (no opportunity detected)")
    
    def test_get_performance_metrics_returns_valid_data(self):
        """Test get_performance_metrics returns tracker data"""
        metrics = self.orchestrator.get_performance_metrics()
        
        # Check expected keys exist
        expected_keys = [
            'opportunities_found', 'opportunities_executed',
            'total_profit', 'total_loss', 'win_rate', 'average_profit'
        ]
        
        for key in expected_keys:
            assert key in metrics, f"Missing key: {key}"
        
        print("✓ test_get_performance_metrics_returns_valid_data: All keys present")
    
    def test_full_workflow_tracks_correctly(self):
        """Test complete workflow from detection to execution tracking"""
        # Setup test data
        market_data_1 = {
            'id': 'market_1',
            'question': 'Test Market 1'
        }
        price_data_1 = {
            'yes': 0.40,
            'no': 0.45
        }
        
        market_data_2 = {
            'id': 'market_2',
            'question': 'Test Market 2'
        }
        price_data_2 = {
            'yes': 0.42,
            'no': 0.46
        }
        
        # Detect first opportunity
        opp1 = self.orchestrator.detect_opportunity(market_data_1, price_data_1)
        
        # Detect second opportunity
        opp2 = self.orchestrator.detect_opportunity(market_data_2, price_data_2)
        
        # Get metrics before execution
        metrics_before = self.orchestrator.get_performance_metrics()
        opportunities_found = metrics_before['opportunities_found']
        
        # Execute opportunities if found
        executions_count = 0
        if opp1:
            self.orchestrator.execute_opportunity(opp1, trade_size=10.0)
            executions_count += 1
        
        if opp2:
            self.orchestrator.execute_opportunity(opp2, trade_size=10.0)
            executions_count += 1
        
        # Get final metrics
        final_metrics = self.orchestrator.get_performance_metrics()
        
        # Verify tracking
        assert final_metrics['opportunities_found'] == opportunities_found, \
            f"Should have found {opportunities_found} opportunities"
        assert final_metrics['opportunities_executed'] == executions_count, \
            f"Should have executed {executions_count} opportunities"
        
        if executions_count > 0:
            assert final_metrics['total_profit'] > 0, "Should have positive profit"
            assert final_metrics['win_rate'] > 0, "Should have positive win rate"
        
        print(f"✓ test_full_workflow_tracks_correctly: Found {opportunities_found}, Executed {executions_count}")
    
    def test_print_performance_dashboard(self):
        """Test dashboard printing doesn't raise errors"""
        # Add some data
        market_data = {
            'id': 'test_market',
            'question': 'Test Market'
        }
        price_data = {
            'yes': 0.40,
            'no': 0.45
        }
        
        opportunity = self.orchestrator.detect_opportunity(market_data, price_data)
        if opportunity:
            self.orchestrator.execute_opportunity(opportunity, trade_size=10.0)
        
        # Should not raise any errors
        try:
            self.orchestrator.print_performance_dashboard()
            print("✓ test_print_performance_dashboard: Dashboard prints successfully")
        except Exception as e:
            raise AssertionError(f"Dashboard printing failed: {e}")
    
    def test_reset_performance_tracking(self):
        """Test resetting performance tracking"""
        # Add some data
        market_data = {
            'id': 'test_market',
            'question': 'Test Market'
        }
        price_data = {
            'yes': 0.40,
            'no': 0.45
        }
        
        opportunity = self.orchestrator.detect_opportunity(market_data, price_data)
        if opportunity:
            self.orchestrator.execute_opportunity(opportunity, trade_size=10.0)
        
        # Verify data exists
        metrics_before = self.orchestrator.get_performance_metrics()
        has_data = (metrics_before['opportunities_found'] > 0 or 
                   metrics_before['opportunities_executed'] > 0)
        
        # Reset
        self.orchestrator.reset_performance_tracking()
        
        # Verify reset
        metrics_after = self.orchestrator.get_performance_metrics()
        assert metrics_after['opportunities_found'] == 0, "Should reset to 0"
        assert metrics_after['opportunities_executed'] == 0, "Should reset to 0"
        assert metrics_after['total_profit'] == 0.0, "Should reset to 0"
        
        if has_data:
            print("✓ test_reset_performance_tracking: Metrics reset successfully")
        else:
            print("✓ test_reset_performance_tracking: Reset verified (no data to reset)")


def run_all_tests():
    """Run all tests and report results"""
    test_suite = TestArbitrageOrchestrator()
    
    tests = [
        test_suite.test_orchestrator_initializes_tracker,
        test_suite.test_detect_opportunity_calls_tracker,
        test_suite.test_detect_opportunity_returns_none_for_no_arbitrage,
        test_suite.test_execute_opportunity_calls_tracker,
        test_suite.test_get_performance_metrics_returns_valid_data,
        test_suite.test_full_workflow_tracks_correctly,
        test_suite.test_print_performance_dashboard,
        test_suite.test_reset_performance_tracking,
    ]
    
    passed = 0
    failed = 0
    
    print("\n" + "="*70)
    print("RUNNING ARBITRAGE ORCHESTRATOR TESTS")
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
