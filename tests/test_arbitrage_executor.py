"""
Unit Tests for Arbitrage Executor

Tests type-specific arbitrage execution with rollback logic.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from strategies.arbitrage_types import ArbitrageType, ArbitrageLeg, ArbitrageOpportunity
from strategies.arbitrage_executor import ArbitrageExecutor


class TestArbitrageExecutor:
    """Test suite for ArbitrageExecutor"""

    def setup_method(self):
        """Setup test environment"""
        self.executor = ArbitrageExecutor()

    def test_execute_two_way_succeeds_with_valid_opportunity(self):
        """Test execute_two_way() succeeds with valid opportunity"""
        leg1 = ArbitrageLeg("kalshi", "buy", "m1", 0.45, 100, 1)
        leg2 = ArbitrageLeg("polymarket", "sell", "m2", 0.55, 100, 2)

        opportunity = ArbitrageOpportunity(
            type=ArbitrageType.TWO_WAY, legs=[leg1, leg2], expected_profit=10.0
        )

        result = self.executor.execute_two_way(opportunity)

        assert result["success"] == True
        assert result["type"] == "2-way"
        assert result["legs_executed"] == 2
        assert result["legs_failed"] == 0
        assert result["profit"] == 10.0
        assert result["error"] is None

        print(
            "✓ test_execute_two_way_succeeds_with_valid_opportunity: 2-way execution succeeded"
        )

    def test_execute_two_way_rejects_wrong_leg_count(self):
        """Test execute_two_way() rejects opportunities without exactly 2 legs"""
        leg1 = ArbitrageLeg("kalshi", "buy", "m1", 0.45, 100, 1)
        leg2 = ArbitrageLeg("polymarket", "sell", "m2", 0.55, 100, 2)
        leg3 = ArbitrageLeg("binance", "buy", "m3", 0.50, 100, 3)

        opportunity = ArbitrageOpportunity(
            type=ArbitrageType.TWO_WAY, legs=[leg1, leg2, leg3], expected_profit=10.0
        )

        result = self.executor.execute_two_way(opportunity)

        assert result["success"] == False
        assert "requires exactly 2 legs" in result["error"]

        print(
            "✓ test_execute_two_way_rejects_wrong_leg_count: Wrong leg count rejected"
        )

    def test_execute_three_way_succeeds(self):
        """Test execute_three_way() succeeds with valid opportunity"""
        leg1 = ArbitrageLeg("kalshi", "buy", "m1", 0.45, 100, 1)
        leg2 = ArbitrageLeg("polymarket", "sell", "m2", 0.55, 100, 2)
        leg3 = ArbitrageLeg("binance", "buy", "m3", 0.50, 100, 3)

        opportunity = ArbitrageOpportunity(
            type=ArbitrageType.THREE_WAY, legs=[leg1, leg2, leg3], expected_profit=15.0
        )

        result = self.executor.execute_three_way(opportunity)

        assert result["success"] == True
        assert result["type"] == "3-way"
        assert result["legs_executed"] == 3
        assert result["legs_failed"] == 0
        assert result["profit"] == 15.0

        print("✓ test_execute_three_way_succeeds: 3-way execution succeeded")

    def test_execute_three_way_rejects_wrong_leg_count(self):
        """Test execute_three_way() rejects opportunities without exactly 3 legs"""
        leg1 = ArbitrageLeg("kalshi", "buy", "m1", 0.45, 100, 1)
        leg2 = ArbitrageLeg("polymarket", "sell", "m2", 0.55, 100, 2)

        opportunity = ArbitrageOpportunity(
            type=ArbitrageType.THREE_WAY, legs=[leg1, leg2], expected_profit=10.0
        )

        result = self.executor.execute_three_way(opportunity)

        assert result["success"] == False
        assert "requires exactly 3 legs" in result["error"]

        print(
            "✓ test_execute_three_way_rejects_wrong_leg_count: Wrong leg count rejected"
        )

    def test_execute_multi_leg_succeeds(self):
        """Test execute_multi_leg() succeeds with 4+ legs"""
        leg1 = ArbitrageLeg("kalshi", "buy", "m1", 0.45, 100, 1)
        leg2 = ArbitrageLeg("polymarket", "sell", "m2", 0.55, 100, 2)
        leg3 = ArbitrageLeg("binance", "buy", "m3", 0.50, 100, 3)
        leg4 = ArbitrageLeg("ftx", "sell", "m4", 0.60, 100, 4)

        opportunity = ArbitrageOpportunity(
            type=ArbitrageType.MULTI_LEG,
            legs=[leg1, leg2, leg3, leg4],
            expected_profit=20.0,
        )

        result = self.executor.execute_multi_leg(opportunity)

        assert result["success"] == True
        assert result["type"] == "multi-leg"
        assert result["legs_executed"] == 4
        assert result["legs_failed"] == 0
        assert result["profit"] == 20.0

        print("✓ test_execute_multi_leg_succeeds: Multi-leg execution succeeded")

    def test_execute_multi_leg_rejects_less_than_4_legs(self):
        """Test execute_multi_leg() rejects opportunities with less than 4 legs"""
        leg1 = ArbitrageLeg("kalshi", "buy", "m1", 0.45, 100, 1)
        leg2 = ArbitrageLeg("polymarket", "sell", "m2", 0.55, 100, 2)

        opportunity = ArbitrageOpportunity(
            type=ArbitrageType.MULTI_LEG, legs=[leg1, leg2], expected_profit=10.0
        )

        result = self.executor.execute_multi_leg(opportunity)

        assert result["success"] == False
        assert "requires 4+ legs" in result["error"]

        print(
            "✓ test_execute_multi_leg_rejects_less_than_4_legs: Less than 4 legs rejected"
        )

    def test_execute_router_calls_correct_executor(self):
        """Test execute() router calls correct executor based on type"""
        # Test 2-way
        leg1 = ArbitrageLeg("kalshi", "buy", "m1", 0.45, 100, 1)
        leg2 = ArbitrageLeg("polymarket", "sell", "m2", 0.55, 100, 2)

        opportunity = ArbitrageOpportunity(
            type=ArbitrageType.TWO_WAY, legs=[leg1, leg2], expected_profit=10.0
        )

        result = self.executor.execute(opportunity)
        assert result["type"] == "2-way"
        assert result["success"] == True

        print("✓ test_execute_router_calls_correct_executor: Router works correctly")

    def test_executor_rejects_non_kalshi_first_opportunities(self):
        """Test executor rejects non-Kalshi-first opportunities"""
        # Create opportunity with polymarket first (not Kalshi)
        leg1 = ArbitrageLeg("polymarket", "buy", "m1", 0.45, 100, 1)
        leg2 = ArbitrageLeg("kalshi", "sell", "m2", 0.55, 100, 2)

        opportunity = ArbitrageOpportunity(
            type=ArbitrageType.TWO_WAY, legs=[leg1, leg2], expected_profit=10.0
        )

        result = self.executor.execute(opportunity)

        assert result["success"] == False
        assert "Kalshi-first validation failed" in result["error"]

        print(
            "✓ test_executor_rejects_non_kalshi_first_opportunities: Non-Kalshi-first rejected"
        )

    def test_execute_router_handles_all_types(self):
        """Test execute() router handles all arbitrage types"""
        # Test 3-way
        leg1 = ArbitrageLeg("kalshi", "buy", "m1", 0.45, 100, 1)
        leg2 = ArbitrageLeg("polymarket", "sell", "m2", 0.55, 100, 2)
        leg3 = ArbitrageLeg("binance", "buy", "m3", 0.50, 100, 3)

        opportunity = ArbitrageOpportunity(
            type=ArbitrageType.THREE_WAY, legs=[leg1, leg2, leg3], expected_profit=15.0
        )

        result = self.executor.execute(opportunity)
        assert result["type"] == "3-way"
        assert result["success"] == True

        # Test multi-leg
        leg4 = ArbitrageLeg("ftx", "sell", "m4", 0.60, 100, 4)
        opportunity_ml = ArbitrageOpportunity(
            type=ArbitrageType.MULTI_LEG,
            legs=[leg1, leg2, leg3, leg4],
            expected_profit=20.0,
        )

        result_ml = self.executor.execute(opportunity_ml)
        assert result_ml["type"] == "multi-leg"
        assert result_ml["success"] == True

        print("✓ test_execute_router_handles_all_types: All types handled")

    def test_executor_returns_valid_result_structure(self):
        """Test executor returns valid result structure"""
        leg1 = ArbitrageLeg("kalshi", "buy", "m1", 0.45, 100, 1)
        leg2 = ArbitrageLeg("polymarket", "sell", "m2", 0.55, 100, 2)

        opportunity = ArbitrageOpportunity(
            type=ArbitrageType.TWO_WAY, legs=[leg1, leg2], expected_profit=10.0
        )

        result = self.executor.execute(opportunity)

        # Check all required keys exist
        required_keys = [
            "success",
            "type",
            "legs_executed",
            "legs_failed",
            "profit",
            "error",
            "timestamp",
        ]

        for key in required_keys:
            assert key in result, f"Missing key: {key}"

        print("✓ test_executor_returns_valid_result_structure: Result structure valid")


def run_all_tests():
    """Run all tests and report results"""
    test_suite = TestArbitrageExecutor()

    tests = [
        test_suite.test_execute_two_way_succeeds_with_valid_opportunity,
        test_suite.test_execute_two_way_rejects_wrong_leg_count,
        test_suite.test_execute_three_way_succeeds,
        test_suite.test_execute_three_way_rejects_wrong_leg_count,
        test_suite.test_execute_multi_leg_succeeds,
        test_suite.test_execute_multi_leg_rejects_less_than_4_legs,
        test_suite.test_execute_router_calls_correct_executor,
        test_suite.test_executor_rejects_non_kalshi_first_opportunities,
        test_suite.test_execute_router_handles_all_types,
        test_suite.test_executor_returns_valid_result_structure,
    ]

    passed = 0
    failed = 0

    print("\n" + "=" * 70)
    print("RUNNING ARBITRAGE EXECUTOR TESTS")
    print("=" * 70 + "\n")

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

    print("\n" + "=" * 70)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 70 + "\n")

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
