"""
Test script to verify all production components are correctly installed
"""

import sys

def test_imports():
    """Test that all new modules can be imported"""
    print("Testing module imports...")
    
    try:
        # Core services
        from services.prometheus_metrics import metrics
        print("✓ Prometheus metrics module")
        
        from services.sentry_integration import sentry
        print("✓ Sentry integration module")
        
        from services.feature_flags import feature_flags
        print("✓ Feature flags module")
        
        from services.security import jwt_auth, api_key_auth, rate_limiter
        print("✓ Security module")
        
        from services.position_tracker import position_tracker
        print("✓ Position tracker module")
        
        from services.portfolio_manager import portfolio_manager
        print("✓ Portfolio manager module")
        
        print("\n✅ All imports successful!")
        return True
        
    except ImportError as e:
        print(f"\n❌ Import failed: {e}")
        return False


def test_feature_flags():
    """Test feature flags functionality"""
    print("\nTesting feature flags...")
    
    try:
        from services.feature_flags import feature_flags
        
        # Get all flags
        all_flags = feature_flags.get_all()
        print(f"✓ Total flags defined: {len(all_flags)}")
        
        # Check that real_trading is always disabled (safety check)
        assert not feature_flags.is_enabled('real_trading')
        print("✓ Real trading is disabled (safety check)")
        
        # Check some default flags
        assert 'prometheus_metrics' in all_flags
        print("✓ Prometheus metrics flag exists")
        
        assert 'paper_trading' in all_flags
        print("✓ Paper trading flag exists")
        
        print("\n✅ Feature flags working correctly!")
        return True
        
    except Exception as e:
        print(f"\n❌ Feature flags test failed: {e}")
        return False


def test_metrics():
    """Test Prometheus metrics"""
    print("\nTesting Prometheus metrics...")
    
    try:
        from services.prometheus_metrics import metrics
        
        # Test recording metrics
        metrics.record_opportunity('arbitrage')
        print("✓ Record opportunity")
        
        metrics.record_api_call('test', 'endpoint', 0.1)
        print("✓ Record API call")
        
        metrics.update_connection_status('test', True)
        print("✓ Update connection status")
        
        # Get metrics output
        metrics_data = metrics.get_metrics()
        assert len(metrics_data) > 0
        print(f"✓ Metrics generated ({len(metrics_data)} bytes)")
        
        print("\n✅ Prometheus metrics working correctly!")
        return True
        
    except Exception as e:
        print(f"\n❌ Metrics test failed: {e}")
        return False


def test_position_tracking():
    """Test position tracking"""
    print("\nTesting position tracking...")
    
    try:
        from services.position_tracker import position_tracker
        
        # Test opening a position
        position = position_tracker.open_position(
            market_id='test-market',
            market_name='Test Market',
            side='both',
            entry_price_yes=0.51,
            entry_price_no=0.49,
            size=100.0,
            strategy='arbitrage',
            expected_profit=5.0
        )
        print(f"✓ Opened position: {position.position_id}")
        
        # Test getting positions
        open_positions = position_tracker.get_open_positions()
        assert len(open_positions) >= 1
        print(f"✓ Retrieved open positions: {len(open_positions)}")
        
        # Test getting stats
        stats = position_tracker.get_position_stats()
        assert 'total_positions' in stats
        print(f"✓ Position stats: {stats['total_positions']} total")
        
        print("\n✅ Position tracking working correctly!")
        return True
        
    except Exception as e:
        print(f"\n❌ Position tracking test failed: {e}")
        return False


def test_security():
    """Test security features"""
    print("\nTesting security features...")
    
    try:
        from services.security import jwt_auth, api_key_auth, rate_limiter
        
        # Test JWT token generation
        token = jwt_auth.generate_token('test_user')
        assert len(token) > 0
        print(f"✓ JWT token generated ({len(token)} chars)")
        
        # Test token verification
        payload = jwt_auth.verify_token(token)
        assert payload is not None
        assert payload['user_id'] == 'test_user'
        print("✓ JWT token verified")
        
        # Test API key generation
        api_key = api_key_auth.generate_key('test_key', ['read', 'write'])
        assert len(api_key) > 0
        print(f"✓ API key generated ({len(api_key)} chars)")
        
        # Test rate limiter
        allowed = rate_limiter.is_allowed('test_client', max_requests=10)
        assert allowed == True
        print("✓ Rate limiter check")
        
        print("\n✅ Security features working correctly!")
        return True
        
    except Exception as e:
        print(f"\n❌ Security test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("="*60)
    print("PRODUCTION COMPONENTS TEST SUITE")
    print("="*60)
    
    results = []
    
    # Run tests
    results.append(("Imports", test_imports()))
    results.append(("Feature Flags", test_feature_flags()))
    results.append(("Metrics", test_metrics()))
    results.append(("Position Tracking", test_position_tracking()))
    results.append(("Security", test_security()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All production components are working correctly!")
        return 0
    else:
        print(f"\n⚠️ {total - passed} test(s) failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
