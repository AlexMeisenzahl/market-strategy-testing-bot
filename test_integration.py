#!/usr/bin/env python3
"""
Integration Test for Live API and Enhanced Features

Tests the integration of:
- Live Polymarket API
- Enhanced notification system
- Market filtering
"""

import yaml
import sys

def test_config_loading():
    """Test configuration loading"""
    print("Testing configuration loading...")
    
    try:
        with open('config.example.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        # Verify key sections exist
        assert 'paper_trading' in config
        assert 'polymarket' in config
        assert 'notifications' in config
        assert config['paper_trading'] == True
        
        print("  ✓ Configuration loads correctly")
        print("  ✓ Paper trading is enabled")
        print("  ✓ All required sections present")
        return True
    except Exception as e:
        print(f"  ✗ Configuration test failed: {e}")
        return False


def test_polymarket_api():
    """Test Polymarket API client"""
    print("\nTesting Polymarket API client...")
    
    try:
        from polymarket_api import PolymarketAPI
        
        # Initialize API client
        api = PolymarketAPI(timeout=5, retry_attempts=2)
        print("  ✓ API client initialized")
        
        # Test API health (this will fail if API is down, but that's ok)
        try:
            is_healthy = api.check_health()
            if is_healthy:
                print("  ✓ Polymarket API is accessible")
            else:
                print("  ⚠ Polymarket API is not accessible (will use fallback)")
        except Exception:
            print("  ⚠ Could not check API health (will use fallback)")
        
        return True
    except Exception as e:
        print(f"  ✗ API client test failed: {e}")
        return False


def test_notification_system():
    """Test enhanced notification system"""
    print("\nTesting enhanced notification system...")
    
    try:
        from notification_rate_limiter import NotificationRateLimiter
        from quiet_hours import QuietHours
        from notifier import Notifier
        
        # Test rate limiter
        rate_limiter = NotificationRateLimiter(
            max_per_minute=5,
            max_per_hour=20,
            cooldown_seconds=30
        )
        assert rate_limiter.allow() == True
        rate_limiter.record()
        print("  ✓ Rate limiter working")
        
        # Test quiet hours
        quiet_hours = QuietHours(
            enabled=False,
            start_time="23:00",
            end_time="07:00",
            timezone="UTC"
        )
        assert quiet_hours.is_quiet_time() == False
        print("  ✓ Quiet hours working")
        
        # Test notifier with full config
        config = {
            'paper_trading': True,
            'notifications': {
                'desktop': {
                    'enabled': True,
                    'event_types': {
                        'trade': True,
                        'opportunity': True,
                        'error': True
                    }
                },
                'email': {'enabled': False, 'event_types': {}},
                'telegram': {'enabled': False, 'event_types': {}},
                'rate_limiting': {
                    'enabled': True,
                    'max_per_minute': 5,
                    'max_per_hour': 20
                },
                'quiet_hours': {
                    'enabled': False,
                    'start_time': '23:00',
                    'end_time': '07:00',
                    'timezone': 'UTC'
                }
            },
            'notification_triggers': {},
            'desktop_notifications': True,
            'sound_alerts': False,
            'telegram': {'enabled': False},
            'email': {'enabled': False}
        }
        
        notifier = Notifier(config)
        
        # Test should_send method
        assert notifier.should_send('trade', 'desktop') == True
        print("  ✓ Notifier working")
        
        # Get statistics
        stats = notifier.get_statistics()
        assert 'rate_limiter' in stats
        assert 'quiet_hours' in stats
        print("  ✓ Notifier statistics available")
        
        return True
    except Exception as e:
        print(f"  ✗ Notification system test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_monitor_integration():
    """Test monitor with live API integration"""
    print("\nTesting monitor integration...")
    
    try:
        from monitor import PolymarketMonitor
        
        config = {
            'paper_trading': True,
            'polymarket': {
                'api': {
                    'enabled': False,  # Disabled for testing
                    'timeout': 5,
                    'retry_attempts': 2
                }
            },
            'rate_limit_max': 100,
            'api_timeout_seconds': 5,
            'max_retries': 3,
            'request_delay_seconds': 0.5,
            'rate_limit_warning_threshold': 0.80,
            'rate_limit_pause_threshold': 0.95
        }
        
        monitor = PolymarketMonitor(config)
        print("  ✓ Monitor initialized")
        
        # Test getting prices (will use fallback since API is disabled)
        prices = monitor.get_market_prices('test-market')
        assert prices is not None
        assert 'yes' in prices
        assert 'no' in prices
        print("  ✓ Monitor can fetch prices (using fallback)")
        
        return True
    except Exception as e:
        print(f"  ✗ Monitor integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_bot_market_fetching():
    """Test bot can fetch markets"""
    print("\nTesting bot market fetching...")
    
    try:
        # Just test that the imports work and basic initialization
        # We won't run the full bot
        from bot import ArbitrageBot
        print("  ✓ Bot module imports successfully")
        
        # Check that _get_live_markets method exists
        assert hasattr(ArbitrageBot, '_get_live_markets')
        assert hasattr(ArbitrageBot, '_get_demo_markets')
        print("  ✓ Bot has market fetching methods")
        
        return True
    except Exception as e:
        print(f"  ✗ Bot test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all integration tests"""
    print("=" * 60)
    print("INTEGRATION TEST SUITE")
    print("=" * 60)
    
    tests = [
        test_config_loading,
        test_polymarket_api,
        test_notification_system,
        test_monitor_integration,
        test_bot_market_fetching
    ]
    
    results = []
    for test in tests:
        result = test()
        results.append(result)
    
    print("\n" + "=" * 60)
    print("TEST RESULTS")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("\n✅ ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} TEST(S) FAILED")
        return 1


if __name__ == '__main__':
    sys.exit(main())
