"""
Unit Tests for Rollback Handler

Tests rollback logic for failed arbitrage trades.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from strategies.arbitrage_types import ArbitrageLeg
from strategies.rollback_handler import RollbackHandler


class TestRollbackHandler:
    """Test suite for RollbackHandler"""
    
    def setup_method(self):
        """Setup test environment"""
        self.handler = RollbackHandler()
    
    def test_rollback_leg_reverses_buy_to_sell(self):
        """Test rollback_leg() reverses buy to sell"""
        leg = ArbitrageLeg("kalshi", "buy", "m1", 0.45, 100, 1)
        
        result = self.handler.rollback_leg(leg)
        
        assert result == True, "Rollback should succeed"
        print("✓ test_rollback_leg_reverses_buy_to_sell: Buy reversed to sell")
    
    def test_rollback_leg_reverses_sell_to_buy(self):
        """Test rollback_leg() reverses sell to buy"""
        leg = ArbitrageLeg("polymarket", "sell", "m2", 0.55, 100, 2)
        
        result = self.handler.rollback_leg(leg)
        
        assert result == True, "Rollback should succeed"
        print("✓ test_rollback_leg_reverses_sell_to_buy: Sell reversed to buy")
    
    def test_rollback_opportunity_processes_legs_in_reverse_order(self):
        """Test rollback_opportunity() processes legs in reverse order"""
        leg1 = ArbitrageLeg("kalshi", "buy", "m1", 0.45, 100, 1)
        leg2 = ArbitrageLeg("polymarket", "sell", "m2", 0.55, 100, 2)
        leg3 = ArbitrageLeg("binance", "buy", "m3", 0.50, 100, 3)
        
        executed_legs = [leg1, leg2, leg3]
        
        result = self.handler.rollback_opportunity(executed_legs)
        
        assert result['total_legs'] == 3
        assert result['successful_rollbacks'] == 3
        assert result['failed_rollbacks'] == 0
        
        # Check rollback happened in reverse order
        details = result['rollback_details']
        assert details[0]['order'] == 3, "First rollback should be leg 3"
        assert details[1]['order'] == 2, "Second rollback should be leg 2"
        assert details[2]['order'] == 1, "Third rollback should be leg 1"
        
        print("✓ test_rollback_opportunity_processes_legs_in_reverse_order: Reverse order confirmed")
    
    def test_rollback_opportunity_continues_even_if_individual_legs_fail(self):
        """Test rollback continues even if individual legs fail"""
        # This test verifies the best-effort nature of rollback
        leg1 = ArbitrageLeg("kalshi", "buy", "m1", 0.45, 100, 1)
        leg2 = ArbitrageLeg("polymarket", "sell", "m2", 0.55, 100, 2)
        
        executed_legs = [leg1, leg2]
        
        result = self.handler.rollback_opportunity(executed_legs)
        
        # Should process both legs regardless of individual failures
        assert result['total_legs'] == 2
        assert len(result['rollback_details']) == 2
        
        print("✓ test_rollback_opportunity_continues_even_if_individual_legs_fail: Continues on failure")
    
    def test_rollback_opportunity_empty_legs(self):
        """Test rollback_opportunity() with empty legs"""
        result = self.handler.rollback_opportunity([])
        
        assert result['total_legs'] == 0
        assert result['successful_rollbacks'] == 0
        assert result['failed_rollbacks'] == 0
        assert len(result['rollback_details']) == 0
        
        print("✓ test_rollback_opportunity_empty_legs: Empty legs handled")
    
    def test_rollback_opportunity_single_leg(self):
        """Test rollback_opportunity() with single leg"""
        leg = ArbitrageLeg("kalshi", "buy", "m1", 0.45, 100, 1)
        
        result = self.handler.rollback_opportunity([leg])
        
        assert result['total_legs'] == 1
        assert result['successful_rollbacks'] == 1
        assert result['failed_rollbacks'] == 0
        
        print("✓ test_rollback_opportunity_single_leg: Single leg rolled back")
    
    def test_rollback_opportunity_returns_details(self):
        """Test rollback_opportunity() returns detailed results"""
        leg1 = ArbitrageLeg("kalshi", "buy", "m1", 0.45, 100, 1)
        leg2 = ArbitrageLeg("polymarket", "sell", "m2", 0.55, 100, 2)
        
        result = self.handler.rollback_opportunity([leg1, leg2])
        
        # Check result structure
        assert 'total_legs' in result
        assert 'successful_rollbacks' in result
        assert 'failed_rollbacks' in result
        assert 'rollback_details' in result
        
        # Check details structure
        for detail in result['rollback_details']:
            assert 'exchange' in detail
            assert 'market_id' in detail
            assert 'action' in detail
            assert 'order' in detail
            assert 'success' in detail
        
        print("✓ test_rollback_opportunity_returns_details: Detailed results returned")


def run_all_tests():
    """Run all tests and report results"""
    test_suite = TestRollbackHandler()
    
    tests = [
        test_suite.test_rollback_leg_reverses_buy_to_sell,
        test_suite.test_rollback_leg_reverses_sell_to_buy,
        test_suite.test_rollback_opportunity_processes_legs_in_reverse_order,
        test_suite.test_rollback_opportunity_continues_even_if_individual_legs_fail,
        test_suite.test_rollback_opportunity_empty_legs,
        test_suite.test_rollback_opportunity_single_leg,
        test_suite.test_rollback_opportunity_returns_details,
    ]
    
    passed = 0
    failed = 0
    
    print("\n" + "="*70)
    print("RUNNING ROLLBACK HANDLER TESTS")
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
