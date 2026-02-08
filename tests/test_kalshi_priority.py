"""
Unit Tests for Kalshi Priority

Tests Kalshi-first sorting and validation logic.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from strategies.arbitrage_types import ArbitrageType, ArbitrageLeg, ArbitrageOpportunity
from strategies.kalshi_priority import sort_legs_kalshi_first, validate_kalshi_first


class TestKalshiPriority:
    """Test suite for Kalshi priority"""

    def test_sort_legs_kalshi_first_moves_kalshi_to_front(self):
        """Test sort_legs_kalshi_first() moves Kalshi to front"""
        leg1 = ArbitrageLeg("polymarket", "buy", "m1", 0.45, 100, 1)
        leg2 = ArbitrageLeg("kalshi", "sell", "m2", 0.55, 100, 2)
        leg3 = ArbitrageLeg("binance", "buy", "m3", 0.50, 100, 3)

        legs = [leg1, leg2, leg3]
        sorted_legs = sort_legs_kalshi_first(legs)

        # Kalshi should be first
        assert sorted_legs[0].exchange == "kalshi", "Kalshi should be first"
        assert sorted_legs[0].order == 1, "Kalshi should have order 1"

        # Others should follow in original relative order
        assert sorted_legs[1].exchange == "polymarket"
        assert sorted_legs[1].order == 2
        assert sorted_legs[2].exchange == "binance"
        assert sorted_legs[2].order == 3

        print(
            "✓ test_sort_legs_kalshi_first_moves_kalshi_to_front: Kalshi moved to front"
        )

    def test_sort_legs_kalshi_first_no_kalshi_legs(self):
        """Test sort_legs_kalshi_first() with no Kalshi legs returns original order"""
        leg1 = ArbitrageLeg("polymarket", "buy", "m1", 0.45, 100, 1)
        leg2 = ArbitrageLeg("binance", "sell", "m2", 0.55, 100, 2)

        legs = [leg1, leg2]
        sorted_legs = sort_legs_kalshi_first(legs)

        # Order should be unchanged
        assert sorted_legs[0].exchange == "polymarket"
        assert sorted_legs[0].order == 1
        assert sorted_legs[1].exchange == "binance"
        assert sorted_legs[1].order == 2

        print("✓ test_sort_legs_kalshi_first_no_kalshi_legs: No Kalshi legs handled")

    def test_sort_legs_kalshi_first_multiple_kalshi_legs(self):
        """Test sort_legs_kalshi_first() with multiple Kalshi legs"""
        leg1 = ArbitrageLeg("polymarket", "buy", "m1", 0.45, 100, 1)
        leg2 = ArbitrageLeg("kalshi", "sell", "m2", 0.55, 100, 2)
        leg3 = ArbitrageLeg("kalshi", "buy", "m3", 0.50, 100, 3)
        leg4 = ArbitrageLeg("binance", "sell", "m4", 0.60, 100, 4)

        legs = [leg1, leg2, leg3, leg4]
        sorted_legs = sort_legs_kalshi_first(legs)

        # Both Kalshi legs should be first (in their original relative order)
        assert sorted_legs[0].exchange == "kalshi"
        assert sorted_legs[0].market_id == "m2"
        assert sorted_legs[0].order == 1

        assert sorted_legs[1].exchange == "kalshi"
        assert sorted_legs[1].market_id == "m3"
        assert sorted_legs[1].order == 2

        # Non-Kalshi legs follow
        assert sorted_legs[2].exchange == "polymarket"
        assert sorted_legs[2].order == 3
        assert sorted_legs[3].exchange == "binance"
        assert sorted_legs[3].order == 4

        print(
            "✓ test_sort_legs_kalshi_first_multiple_kalshi_legs: Multiple Kalshi legs handled"
        )

    def test_sort_legs_kalshi_first_empty_list(self):
        """Test sort_legs_kalshi_first() with empty list"""
        legs = []
        sorted_legs = sort_legs_kalshi_first(legs)

        assert len(sorted_legs) == 0, "Empty list should return empty list"
        print("✓ test_sort_legs_kalshi_first_empty_list: Empty list handled")

    def test_sort_legs_kalshi_first_already_first(self):
        """Test sort_legs_kalshi_first() when Kalshi is already first"""
        leg1 = ArbitrageLeg("kalshi", "buy", "m1", 0.45, 100, 1)
        leg2 = ArbitrageLeg("polymarket", "sell", "m2", 0.55, 100, 2)

        legs = [leg1, leg2]
        sorted_legs = sort_legs_kalshi_first(legs)

        # Should maintain order
        assert sorted_legs[0].exchange == "kalshi"
        assert sorted_legs[0].order == 1
        assert sorted_legs[1].exchange == "polymarket"
        assert sorted_legs[1].order == 2

        print(
            "✓ test_sort_legs_kalshi_first_already_first: Already correct order maintained"
        )

    def test_validate_kalshi_first_passes_when_kalshi_first(self):
        """Test validate_kalshi_first() passes when Kalshi is first"""
        leg1 = ArbitrageLeg("kalshi", "buy", "m1", 0.45, 100, 1)
        leg2 = ArbitrageLeg("polymarket", "sell", "m2", 0.55, 100, 2)

        opportunity = ArbitrageOpportunity(
            type=ArbitrageType.TWO_WAY, legs=[leg1, leg2], expected_profit=10.0
        )

        assert validate_kalshi_first(opportunity) == True
        print(
            "✓ test_validate_kalshi_first_passes_when_kalshi_first: Validation passed"
        )

    def test_validate_kalshi_first_fails_when_kalshi_not_first(self):
        """Test validate_kalshi_first() fails when Kalshi exists but not first"""
        leg1 = ArbitrageLeg("polymarket", "buy", "m1", 0.45, 100, 1)
        leg2 = ArbitrageLeg("kalshi", "sell", "m2", 0.55, 100, 2)

        opportunity = ArbitrageOpportunity(
            type=ArbitrageType.TWO_WAY, legs=[leg1, leg2], expected_profit=10.0
        )

        assert validate_kalshi_first(opportunity) == False
        print(
            "✓ test_validate_kalshi_first_fails_when_kalshi_not_first: Validation failed correctly"
        )

    def test_validate_kalshi_first_passes_when_no_kalshi(self):
        """Test validate_kalshi_first() passes when no Kalshi legs exist"""
        leg1 = ArbitrageLeg("polymarket", "buy", "m1", 0.45, 100, 1)
        leg2 = ArbitrageLeg("binance", "sell", "m2", 0.55, 100, 2)

        opportunity = ArbitrageOpportunity(
            type=ArbitrageType.TWO_WAY, legs=[leg1, leg2], expected_profit=10.0
        )

        assert validate_kalshi_first(opportunity) == True
        print(
            "✓ test_validate_kalshi_first_passes_when_no_kalshi: No Kalshi validation passed"
        )

    def test_validate_kalshi_first_empty_opportunity(self):
        """Test validate_kalshi_first() with empty legs"""
        opportunity = ArbitrageOpportunity(
            type=ArbitrageType.TWO_WAY, legs=[], expected_profit=0.0
        )

        assert validate_kalshi_first(opportunity) == True
        print("✓ test_validate_kalshi_first_empty_opportunity: Empty legs handled")


def run_all_tests():
    """Run all tests and report results"""
    test_suite = TestKalshiPriority()

    tests = [
        test_suite.test_sort_legs_kalshi_first_moves_kalshi_to_front,
        test_suite.test_sort_legs_kalshi_first_no_kalshi_legs,
        test_suite.test_sort_legs_kalshi_first_multiple_kalshi_legs,
        test_suite.test_sort_legs_kalshi_first_empty_list,
        test_suite.test_sort_legs_kalshi_first_already_first,
        test_suite.test_validate_kalshi_first_passes_when_kalshi_first,
        test_suite.test_validate_kalshi_first_fails_when_kalshi_not_first,
        test_suite.test_validate_kalshi_first_passes_when_no_kalshi,
        test_suite.test_validate_kalshi_first_empty_opportunity,
    ]

    passed = 0
    failed = 0

    print("\n" + "=" * 70)
    print("RUNNING KALSHI PRIORITY TESTS")
    print("=" * 70 + "\n")

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

    print("\n" + "=" * 70)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 70 + "\n")

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
