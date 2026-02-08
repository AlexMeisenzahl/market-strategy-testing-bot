"""
Unit Tests for Arbitrage Types

Tests ArbitrageType enum, ArbitrageLeg, and ArbitrageOpportunity dataclasses.
"""

import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from strategies.arbitrage_types import ArbitrageType, ArbitrageLeg, ArbitrageOpportunity


class TestArbitrageTypes:
    """Test suite for arbitrage types"""
    
    def test_arbitrage_type_enum_has_all_types(self):
        """Test ArbitrageType enum has all required types"""
        assert hasattr(ArbitrageType, 'TWO_WAY'), "Should have TWO_WAY"
        assert hasattr(ArbitrageType, 'THREE_WAY'), "Should have THREE_WAY"
        assert hasattr(ArbitrageType, 'MULTI_LEG'), "Should have MULTI_LEG"
        
        assert ArbitrageType.TWO_WAY.value == "2-way"
        assert ArbitrageType.THREE_WAY.value == "3-way"
        assert ArbitrageType.MULTI_LEG.value == "multi-leg"
        
        print("✓ test_arbitrage_type_enum_has_all_types: All types present with correct values")
    
    def test_arbitrage_leg_validates_required_fields(self):
        """Test ArbitrageLeg dataclass validates required fields"""
        # Valid leg should work
        leg = ArbitrageLeg(
            exchange="kalshi",
            action="buy",
            market_id="market_123",
            price=0.45,
            quantity=100.0,
            order=1
        )
        
        assert leg.exchange == "kalshi"
        assert leg.action == "buy"
        assert leg.market_id == "market_123"
        assert leg.price == 0.45
        assert leg.quantity == 100.0
        assert leg.order == 1
        
        print("✓ test_arbitrage_leg_validates_required_fields: Valid leg created successfully")
    
    def test_arbitrage_leg_rejects_invalid_action(self):
        """Test ArbitrageLeg rejects invalid action"""
        try:
            leg = ArbitrageLeg(
                exchange="kalshi",
                action="invalid",  # Should be "buy" or "sell"
                market_id="market_123",
                price=0.45,
                quantity=100.0,
                order=1
            )
            raise AssertionError("Should have raised ValueError for invalid action")
        except ValueError as e:
            assert "Action must be 'buy' or 'sell'" in str(e)
            print("✓ test_arbitrage_leg_rejects_invalid_action: Invalid action rejected")
    
    def test_arbitrage_leg_rejects_negative_price(self):
        """Test ArbitrageLeg rejects negative price"""
        try:
            leg = ArbitrageLeg(
                exchange="kalshi",
                action="buy",
                market_id="market_123",
                price=-0.45,  # Invalid
                quantity=100.0,
                order=1
            )
            raise AssertionError("Should have raised ValueError for negative price")
        except ValueError as e:
            assert "Price must be positive" in str(e)
            print("✓ test_arbitrage_leg_rejects_negative_price: Negative price rejected")
    
    def test_arbitrage_leg_rejects_negative_quantity(self):
        """Test ArbitrageLeg rejects negative quantity"""
        try:
            leg = ArbitrageLeg(
                exchange="kalshi",
                action="buy",
                market_id="market_123",
                price=0.45,
                quantity=-100.0,  # Invalid
                order=1
            )
            raise AssertionError("Should have raised ValueError for negative quantity")
        except ValueError as e:
            assert "Quantity must be positive" in str(e)
            print("✓ test_arbitrage_leg_rejects_negative_quantity: Negative quantity rejected")
    
    def test_arbitrage_leg_rejects_invalid_order(self):
        """Test ArbitrageLeg rejects order < 1"""
        try:
            leg = ArbitrageLeg(
                exchange="kalshi",
                action="buy",
                market_id="market_123",
                price=0.45,
                quantity=100.0,
                order=0  # Invalid (must be >= 1)
            )
            raise AssertionError("Should have raised ValueError for order < 1")
        except ValueError as e:
            assert "Order must be >= 1" in str(e)
            print("✓ test_arbitrage_leg_rejects_invalid_order: Invalid order rejected")
    
    def test_arbitrage_opportunity_identifies_kalshi_first(self):
        """Test ArbitrageOpportunity correctly identifies Kalshi-first"""
        # Create legs with Kalshi first
        leg1 = ArbitrageLeg("kalshi", "buy", "m1", 0.45, 100, 1)
        leg2 = ArbitrageLeg("polymarket", "sell", "m2", 0.55, 100, 2)
        
        opportunity = ArbitrageOpportunity(
            type=ArbitrageType.TWO_WAY,
            legs=[leg1, leg2],
            expected_profit=10.0
        )
        
        assert opportunity.kalshi_first == True, "Should identify Kalshi as first"
        print("✓ test_arbitrage_opportunity_identifies_kalshi_first: Kalshi-first detected")
    
    def test_arbitrage_opportunity_identifies_non_kalshi_first(self):
        """Test ArbitrageOpportunity correctly identifies non-Kalshi-first"""
        # Create legs with polymarket first
        leg1 = ArbitrageLeg("polymarket", "buy", "m1", 0.45, 100, 1)
        leg2 = ArbitrageLeg("kalshi", "sell", "m2", 0.55, 100, 2)
        
        opportunity = ArbitrageOpportunity(
            type=ArbitrageType.TWO_WAY,
            legs=[leg1, leg2],
            expected_profit=10.0
        )
        
        assert opportunity.kalshi_first == False, "Should identify non-Kalshi as first"
        print("✓ test_arbitrage_opportunity_identifies_non_kalshi_first: Non-Kalshi-first detected")
    
    def test_arbitrage_opportunity_no_kalshi_legs(self):
        """Test ArbitrageOpportunity with no Kalshi legs"""
        leg1 = ArbitrageLeg("polymarket", "buy", "m1", 0.45, 100, 1)
        leg2 = ArbitrageLeg("binance", "sell", "m2", 0.55, 100, 2)
        
        opportunity = ArbitrageOpportunity(
            type=ArbitrageType.TWO_WAY,
            legs=[leg1, leg2],
            expected_profit=10.0
        )
        
        assert opportunity.kalshi_first == False, "Should be False when no Kalshi legs"
        print("✓ test_arbitrage_opportunity_no_kalshi_legs: No Kalshi legs handled")
    
    def test_arbitrage_opportunity_properties(self):
        """Test ArbitrageOpportunity properties"""
        leg1 = ArbitrageLeg("kalshi", "buy", "m1", 0.45, 100, 1)
        leg2 = ArbitrageLeg("polymarket", "sell", "m2", 0.55, 100, 2)
        leg3 = ArbitrageLeg("binance", "buy", "m3", 0.50, 100, 3)
        
        opportunity = ArbitrageOpportunity(
            type=ArbitrageType.THREE_WAY,
            legs=[leg1, leg2, leg3],
            expected_profit=15.0
        )
        
        assert opportunity.num_legs == 3, "Should have 3 legs"
        assert len(opportunity.exchanges) == 3, "Should have 3 unique exchanges"
        assert "kalshi" in opportunity.exchanges
        assert "polymarket" in opportunity.exchanges
        assert "binance" in opportunity.exchanges
        
        print("✓ test_arbitrage_opportunity_properties: Properties work correctly")
    
    def test_arbitrage_opportunity_to_dict(self):
        """Test ArbitrageOpportunity to_dict method"""
        leg1 = ArbitrageLeg("kalshi", "buy", "m1", 0.45, 100, 1)
        leg2 = ArbitrageLeg("polymarket", "sell", "m2", 0.55, 100, 2)
        
        opportunity = ArbitrageOpportunity(
            type=ArbitrageType.TWO_WAY,
            legs=[leg1, leg2],
            expected_profit=10.0
        )
        
        result = opportunity.to_dict()
        
        assert result['type'] == '2-way'
        assert result['num_legs'] == 2
        assert result['expected_profit'] == 10.0
        assert result['kalshi_first'] == True
        assert len(result['legs']) == 2
        assert result['legs'][0]['exchange'] == 'kalshi'
        assert result['legs'][0]['order'] == 1
        
        print("✓ test_arbitrage_opportunity_to_dict: to_dict() works correctly")


def run_all_tests():
    """Run all tests and report results"""
    test_suite = TestArbitrageTypes()
    
    tests = [
        test_suite.test_arbitrage_type_enum_has_all_types,
        test_suite.test_arbitrage_leg_validates_required_fields,
        test_suite.test_arbitrage_leg_rejects_invalid_action,
        test_suite.test_arbitrage_leg_rejects_negative_price,
        test_suite.test_arbitrage_leg_rejects_negative_quantity,
        test_suite.test_arbitrage_leg_rejects_invalid_order,
        test_suite.test_arbitrage_opportunity_identifies_kalshi_first,
        test_suite.test_arbitrage_opportunity_identifies_non_kalshi_first,
        test_suite.test_arbitrage_opportunity_no_kalshi_legs,
        test_suite.test_arbitrage_opportunity_properties,
        test_suite.test_arbitrage_opportunity_to_dict,
    ]
    
    passed = 0
    failed = 0
    
    print("\n" + "="*70)
    print("RUNNING ARBITRAGE TYPES TESTS")
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
