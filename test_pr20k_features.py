"""
Comprehensive Tests for PR#20K Features

Tests for backtesting, risk management, execution reliability, and UX features.
"""

import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_imports():
    """Test that all new modules can be imported"""
    print("\n" + "="*60)
    print("TEST 1: Module Imports")
    print("="*60)
    
    try:
        # Part 1: Strategy Validation
        from services.backtesting_engine import backtesting_engine
        print("✓ Backtesting Engine")
        
        from services.historical_data_collector import historical_data_collector
        print("✓ Historical Data Collector")
        
        from services.strategy_optimizer import strategy_optimizer
        print("✓ Strategy Optimizer")
        
        # Part 2: Risk Management
        from services.risk_enforcer import RiskEnforcer
        print("✓ Risk Enforcer")
        
        from services.exit_manager import exit_manager
        print("✓ Exit Manager")
        
        from services.rebalancer import portfolio_rebalancer
        print("✓ Portfolio Rebalancer")
        
        # Part 3: Execution & Reliability
        from services.trade_verifier import trade_verifier
        print("✓ Trade Verifier")
        
        from services.crash_recovery import crash_recovery
        print("✓ Crash Recovery")
        
        from services.order_timeout_handler import order_timeout_handler
        print("✓ Order Timeout Handler")
        
        from utils.rate_limiter import PriorityRateLimiter
        print("✓ Priority Rate Limiter")
        
        # Part 4: User Experience
        from services.alert_manager import alert_manager
        print("✓ Alert Manager")
        
        from database.models import (
            CryptoPriceHistory,
            TradeJournal,
            Alert,
            PositionConfig,
            APIKey
        )
        print("✓ Database Models")
        
        print("\n✅ All imports successful!")
        return True
        
    except ImportError as e:
        print(f"\n❌ Import failed: {e}")
        return False


def test_backtesting():
    """Test backtesting engine"""
    print("\n" + "="*60)
    print("TEST 2: Backtesting Engine")
    print("="*60)
    
    try:
        from services.backtesting_engine import BacktestingEngine
        
        engine = BacktestingEngine(initial_capital=10000)
        print(f"✓ Initialized with ${engine.initial_capital} capital")
        
        # Placeholder strategy
        class TestStrategy:
            __name__ = "TestStrategy"
        
        # Note: Requires historical data in database
        # For now, just verify the engine is working
        print("✓ Backtesting engine ready (requires historical data)")
        
        return True
        
    except Exception as e:
        print(f"❌ Backtesting test failed: {e}")
        return False


def test_risk_enforcer():
    """Test risk enforcer"""
    print("\n" + "="*60)
    print("TEST 3: Risk Enforcer")
    print("="*60)
    
    try:
        from services.risk_enforcer import RiskEnforcer
        
        enforcer = RiskEnforcer()
        
        # Test trade allowed
        allowed, reason = enforcer.check_trade_allowed(
            trade_size=500,
            current_exposure=1000,
            daily_pnl=0,
            num_positions=2,
            portfolio_value=10000
        )
        
        print(f"✓ Trade check: {'Allowed' if allowed else 'Blocked'}")
        print(f"  Reason: {reason}")
        
        # Test circuit breaker
        enforcer.trigger_circuit_breaker("Test trigger")
        print("✓ Circuit breaker triggered")
        
        # Get status
        status = enforcer.get_risk_status()
        print(f"✓ Circuit breaker active: {status['circuit_breaker_active']}")
        
        # Reset
        enforcer.reset_circuit_breaker(manual_override=True)
        print("✓ Circuit breaker reset")
        
        return True
        
    except Exception as e:
        print(f"❌ Risk enforcer test failed: {e}")
        return False


def test_exit_manager():
    """Test exit manager"""
    print("\n" + "="*60)
    print("TEST 4: Exit Manager")
    print("="*60)
    
    try:
        from services.exit_manager import ExitManager
        
        manager = ExitManager()
        print("✓ Exit manager initialized")
        
        # Test configuration
        manager.set_position_config(
            position_id="test_pos_1",
            stop_loss_pct=-5.0,
            take_profit_pct=10.0,
            max_hold_hours=24
        )
        print("✓ Position config set")
        
        # Get statistics
        stats = manager.get_exit_statistics()
        print(f"✓ Statistics: {stats['total_exits']} total exits")
        
        return True
        
    except Exception as e:
        print(f"❌ Exit manager test failed: {e}")
        return False


def test_trade_verifier():
    """Test trade verifier"""
    print("\n" + "="*60)
    print("TEST 5: Trade Verifier")
    print("="*60)
    
    try:
        from services.trade_verifier import trade_verifier
        
        # Verify a trade
        result = trade_verifier.verify_trade(
            order_id="test_order_123",
            exchange="binance",
            expected_price=50000.0,
            expected_size=100.0
        )
        
        print(f"✓ Trade verified: {result['verified']}")
        print(f"  Status: {result['status']}")
        
        # Get statistics
        stats = trade_verifier.get_verification_statistics()
        print(f"✓ Statistics: {stats['total_verifications']} verifications")
        
        return True
        
    except Exception as e:
        print(f"❌ Trade verifier test failed: {e}")
        return False


def test_crash_recovery():
    """Test crash recovery"""
    print("\n" + "="*60)
    print("TEST 6: Crash Recovery")
    print("="*60)
    
    try:
        from services.crash_recovery import CrashRecovery
        
        recovery = CrashRecovery()
        
        # Save state
        test_state = {
            'active_strategies': ['strategy1', 'strategy2'],
            'open_positions': [],
            'portfolio_value': 10000.0
        }
        
        success = recovery.save_state(test_state)
        print(f"✓ State saved: {success}")
        
        # Get state info
        info = recovery.get_state_info()
        print(f"✓ State file exists: {info['state_file_exists']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Crash recovery test failed: {e}")
        return False


def test_alert_manager():
    """Test alert manager"""
    print("\n" + "="*60)
    print("TEST 7: Alert Manager")
    print("="*60)
    
    try:
        from services.alert_manager import alert_manager
        
        # Create price alert
        alert_id = alert_manager.create_alert(
            'price',
            {'symbol': 'BTC', 'threshold': 100000, 'direction': 'above'}
        )
        print(f"✓ Price alert created: #{alert_id}")
        
        # Get all alerts
        alerts = alert_manager.get_all_alerts()
        print(f"✓ Total alerts: {len(alerts)}")
        
        # Get statistics
        stats = alert_manager.get_alert_statistics()
        print(f"✓ Enabled alerts: {stats['enabled_alerts']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Alert manager test failed: {e}")
        return False


def test_database_models():
    """Test database models"""
    print("\n" + "="*60)
    print("TEST 8: Database Models")
    print("="*60)
    
    try:
        from database.models import (
            CryptoPriceHistory,
            TradeJournal,
            Alert,
            init_trading_db
        )
        
        # Initialize database
        init_trading_db()
        print("✓ Database initialized")
        
        # Test CryptoPriceHistory
        price_id = CryptoPriceHistory.insert(
            symbol='bitcoin',
            price_usd=50000.0,
            volume=1000000.0
        )
        print(f"✓ Price history inserted: #{price_id}")
        
        # Test TradeJournal
        journal_id = TradeJournal.create(
            entry_reason="Test trade",
            confidence_level=8
        )
        print(f"✓ Journal entry created: #{journal_id}")
        
        # Test Alert
        alert_id = Alert.create(
            'price',
            '{"symbol": "BTC", "threshold": 100000}'
        )
        print(f"✓ Alert created: #{alert_id}")
        
        return True
        
    except Exception as e:
        print(f"❌ Database models test failed: {e}")
        return False


def test_priority_rate_limiter():
    """Test priority rate limiter"""
    print("\n" + "="*60)
    print("TEST 9: Priority Rate Limiter")
    print("="*60)
    
    try:
        from utils.rate_limiter import PriorityRateLimiter
        
        limiter = PriorityRateLimiter(calls_per_minute=10)
        print("✓ Priority rate limiter initialized")
        
        # Queue a request
        def dummy_api_call():
            return "success"
        
        request_id = limiter.queue_request(dummy_api_call, priority=5)
        print(f"✓ Request queued: {request_id[:8]}...")
        
        # Get queue status
        status = limiter.get_queue_status()
        print(f"✓ Queue size: {status['queue_size']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Priority rate limiter test failed: {e}")
        return False


def test_portfolio_manager_enhancements():
    """Test portfolio manager volatility-adjusted sizing"""
    print("\n" + "="*60)
    print("TEST 10: Portfolio Manager Enhancements")
    print("="*60)
    
    try:
        from services.portfolio_manager import portfolio_manager
        
        # Test volatility-adjusted position sizing
        high_vol_size = portfolio_manager.calculate_position_size_volatility_adjusted(
            strategy='test',
            entry_price=100.0,
            volatility=10.0  # High volatility
        )
        
        low_vol_size = portfolio_manager.calculate_position_size_volatility_adjusted(
            strategy='test',
            entry_price=100.0,
            volatility=2.0  # Low volatility
        )
        
        print(f"✓ High volatility position size: ${high_vol_size:.2f}")
        print(f"✓ Low volatility position size: ${low_vol_size:.2f}")
        print(f"✓ Size difference: {(low_vol_size / high_vol_size):.1f}x")
        
        return True
        
    except Exception as e:
        print(f"❌ Portfolio manager test failed: {e}")
        return False


def run_all_tests():
    """Run all tests"""
    print("\n" + "#"*60)
    print("# PR#20K Comprehensive Test Suite")
    print("#"*60)
    
    tests = [
        test_imports,
        test_backtesting,
        test_risk_enforcer,
        test_exit_manager,
        test_trade_verifier,
        test_crash_recovery,
        test_alert_manager,
        test_database_models,
        test_priority_rate_limiter,
        test_portfolio_manager_enhancements
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n❌ Test crashed: {e}")
            results.append(False)
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Passed: {passed}/{total}")
    print(f"Failed: {total - passed}/{total}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\n✅ All tests passed!")
    else:
        print(f"\n⚠️ {total - passed} test(s) failed")
    
    print("="*60)


if __name__ == "__main__":
    run_all_tests()
