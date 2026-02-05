#!/usr/bin/env python3
"""
Test script to validate safety features and core functionality
"""

import yaml
import sys
from pathlib import Path

# Import bot components
from logger import get_logger
from monitor import PolymarketMonitor, RateLimiter
from detector import ArbitrageDetector, ArbitrageOpportunity
from paper_trader import PaperTrader

def test_config_loading():
    """Test that config loads correctly"""
    print("Testing config loading...")
    try:
        with open('config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        # Verify critical settings
        assert config['paper_trading'] == True, "❌ Paper trading must be enabled!"
        assert config['kill_switch'] == False, "❌ Kill switch must be false to start!"
        assert config['max_trade_size'] > 0, "❌ Max trade size must be positive!"
        
        print("✓ Config loaded successfully")
        print(f"  - Paper trading: {config['paper_trading']}")
        print(f"  - Kill switch: {config['kill_switch']}")
        print(f"  - Max trade size: ${config['max_trade_size']}")
        return True
    except Exception as e:
        print(f"❌ Config loading failed: {e}")
        return False

def test_logger():
    """Test logger functionality"""
    print("\nTesting logger...")
    try:
        logger = get_logger()
        
        # Test log directory creation
        log_dir = Path("logs")
        assert log_dir.exists(), "❌ Logs directory not created!"
        
        # Test logging functions
        logger.log_opportunity("TEST_MARKET", 0.45, 0.50, "test")
        logger.log_trade("TEST_MARKET", 0.45, 0.50, 0.50, "test")
        logger.log_warning("Test warning message")
        logger.log_connection("healthy", 100)
        
        print("✓ Logger working correctly")
        print(f"  - Logs directory exists: {log_dir.exists()}")
        return True
    except Exception as e:
        print(f"❌ Logger test failed: {e}")
        return False

def test_rate_limiter():
    """Test rate limiter functionality"""
    print("\nTesting rate limiter...")
    try:
        limiter = RateLimiter(max_requests=10, time_window=60)
        
        # Test basic functionality
        assert limiter.can_make_request(), "❌ Should allow first request!"
        limiter.record_request()
        assert limiter.get_remaining_requests() == 9, "❌ Remaining count incorrect!"
        
        # Test percentage calculation
        usage_pct = limiter.get_usage_percentage()
        assert 0 <= usage_pct <= 100, "❌ Usage percentage out of range!"
        
        print("✓ Rate limiter working correctly")
        print(f"  - Usage: {usage_pct:.1f}%")
        print(f"  - Remaining: {limiter.get_remaining_requests()}")
        return True
    except Exception as e:
        print(f"❌ Rate limiter test failed: {e}")
        return False

def test_detector():
    """Test arbitrage detector"""
    print("\nTesting arbitrage detector...")
    try:
        config = {
            'min_profit_margin': 0.02,
            'max_trade_size': 10
        }
        detector = ArbitrageDetector(config)
        
        # Create test opportunity
        opp = ArbitrageOpportunity("test_id", "Test Market", 0.45, 0.50)
        
        # Verify calculations
        assert opp.price_sum == 0.95, "❌ Price sum incorrect!"
        assert opp.profit_margin > 0, "❌ Profit margin should be positive!"
        assert opp.expected_profit > 0, "❌ Expected profit should be positive!"
        
        print("✓ Arbitrage detector working correctly")
        print(f"  - Price sum: ${opp.price_sum:.2f}")
        print(f"  - Profit margin: {opp.profit_margin:.1f}%")
        print(f"  - Expected profit: ${opp.expected_profit:.2f}")
        return True
    except Exception as e:
        print(f"❌ Detector test failed: {e}")
        return False

def test_paper_trader():
    """Test paper trader"""
    print("\nTesting paper trader...")
    try:
        config = {
            'paper_trading': True,
            'max_trade_size': 10,
            'max_trades_per_hour': 10
        }
        trader = PaperTrader(config)
        
        # Create test opportunity
        opp = ArbitrageOpportunity("test_id", "Test Market", 0.45, 0.50)
        
        # Execute paper trade
        trade = trader.execute_paper_trade(opp)
        assert trade is not None, "❌ Paper trade execution failed!"
        assert trade.expected_profit > 0, "❌ Expected profit should be positive!"
        
        # Check statistics
        stats = trader.get_statistics()
        assert stats['trades_executed'] == 1, "❌ Trade count incorrect!"
        assert stats['total_profit'] > 0, "❌ Total profit should be positive!"
        
        print("✓ Paper trader working correctly")
        print(f"  - Trades executed: {stats['trades_executed']}")
        print(f"  - Total profit: ${stats['total_profit']:.2f}")
        print(f"  - Return: {stats['return_percentage']:.1f}%")
        return True
    except Exception as e:
        print(f"❌ Paper trader test failed: {e}")
        return False

def test_safety_features():
    """Test safety features"""
    print("\nTesting safety features...")
    try:
        # Test paper trading requirement
        config = {
            'paper_trading': True,
            'max_trade_size': 10,
            'max_trades_per_hour': 10
        }
        trader = PaperTrader(config)
        print("✓ Paper trading enforced correctly")
        
        # Test that disabling paper trading raises error
        try:
            bad_config = {
                'paper_trading': False,
                'max_trade_size': 10,
                'max_trades_per_hour': 10
            }
            bad_trader = PaperTrader(bad_config)
            print("❌ Should have raised error for disabled paper trading!")
            return False
        except ValueError:
            print("✓ Correctly prevents disabling paper trading")
        
        return True
    except Exception as e:
        print(f"❌ Safety feature test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("ARBITRAGE BOT SAFETY & FUNCTIONALITY TESTS")
    print("=" * 60)
    
    tests = [
        ("Config Loading", test_config_loading),
        ("Logger", test_logger),
        ("Rate Limiter", test_rate_limiter),
        ("Arbitrage Detector", test_detector),
        ("Paper Trader", test_paper_trader),
        ("Safety Features", test_safety_features),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ {name} test crashed: {e}")
            results.append((name, False))
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "❌ FAIL"
        print(f"{status:8} - {name}")
    
    print("=" * 60)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ All tests passed! Bot is ready to run.")
        return 0
    else:
        print("❌ Some tests failed. Please review errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
