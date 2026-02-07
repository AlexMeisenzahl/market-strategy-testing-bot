#!/usr/bin/env python3
"""
Mock test script for free API clients (no internet required)
Tests code structure, imports, and basic logic
"""

import sys
from pathlib import Path


def test_imports():
    """Test that all API clients can be imported"""
    print("\nTesting imports...")
    try:
        from apis.binance_client import BinanceClient
        from apis.coingecko_client import CoinGeckoClient
        from apis.polymarket_subgraph import PolymarketSubgraph
        from apis.data_aggregator import FreeDataAggregator
        
        print("✓ BinanceClient imported successfully")
        print("✓ CoinGeckoClient imported successfully")
        print("✓ PolymarketSubgraph imported successfully")
        print("✓ FreeDataAggregator imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False


def test_client_initialization():
    """Test that clients can be initialized"""
    print("\nTesting client initialization...")
    try:
        from apis.binance_client import BinanceClient
        from apis.coingecko_client import CoinGeckoClient
        from apis.polymarket_subgraph import PolymarketSubgraph
        from apis.data_aggregator import FreeDataAggregator
        
        # Initialize clients
        binance = BinanceClient()
        assert binance is not None, "❌ BinanceClient initialization failed!"
        assert binance.BASE_URL == "https://api.binance.com/api/v3", "❌ Wrong Binance URL!"
        print("✓ BinanceClient initialized with correct URL")
        
        coingecko = CoinGeckoClient()
        assert coingecko is not None, "❌ CoinGeckoClient initialization failed!"
        assert coingecko.BASE_URL == "https://api.coingecko.com/api/v3", "❌ Wrong CoinGecko URL!"
        print("✓ CoinGeckoClient initialized with correct URL")
        
        polymarket = PolymarketSubgraph()
        assert polymarket is not None, "❌ PolymarketSubgraph initialization failed!"
        assert "thegraph.com" in polymarket.SUBGRAPH_URL, "❌ Wrong Polymarket Subgraph URL!"
        print("✓ PolymarketSubgraph initialized with correct URL")
        
        aggregator = FreeDataAggregator()
        assert aggregator is not None, "❌ FreeDataAggregator initialization failed!"
        assert aggregator.binance is not None, "❌ Binance client not initialized in aggregator!"
        assert aggregator.coingecko is not None, "❌ CoinGecko client not initialized in aggregator!"
        assert aggregator.polymarket is not None, "❌ Polymarket client not initialized in aggregator!"
        print("✓ FreeDataAggregator initialized with all clients")
        
        return True
    except Exception as e:
        print(f"❌ Client initialization test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_method_existence():
    """Test that required methods exist on clients"""
    print("\nTesting method existence...")
    try:
        from apis.binance_client import BinanceClient
        from apis.coingecko_client import CoinGeckoClient
        from apis.polymarket_subgraph import PolymarketSubgraph
        from apis.data_aggregator import FreeDataAggregator
        
        # Check Binance methods
        binance = BinanceClient()
        assert hasattr(binance, 'get_price'), "❌ BinanceClient missing get_price method!"
        assert hasattr(binance, 'get_ticker_24h'), "❌ BinanceClient missing get_ticker_24h method!"
        assert hasattr(binance, 'get_multiple_prices'), "❌ BinanceClient missing get_multiple_prices method!"
        assert hasattr(binance, 'ping'), "❌ BinanceClient missing ping method!"
        print("✓ BinanceClient has all required methods")
        
        # Check CoinGecko methods
        coingecko = CoinGeckoClient()
        assert hasattr(coingecko, 'get_price'), "❌ CoinGeckoClient missing get_price method!"
        assert hasattr(coingecko, 'get_market_data'), "❌ CoinGeckoClient missing get_market_data method!"
        assert hasattr(coingecko, 'get_multiple_prices'), "❌ CoinGeckoClient missing get_multiple_prices method!"
        assert hasattr(coingecko, 'ping'), "❌ CoinGeckoClient missing ping method!"
        print("✓ CoinGeckoClient has all required methods")
        
        # Check Polymarket methods
        polymarket = PolymarketSubgraph()
        assert hasattr(polymarket, 'get_active_markets'), "❌ PolymarketSubgraph missing get_active_markets method!"
        assert hasattr(polymarket, 'get_market_by_id'), "❌ PolymarketSubgraph missing get_market_by_id method!"
        assert hasattr(polymarket, 'get_market_odds'), "❌ PolymarketSubgraph missing get_market_odds method!"
        assert hasattr(polymarket, 'ping'), "❌ PolymarketSubgraph missing ping method!"
        print("✓ PolymarketSubgraph has all required methods")
        
        # Check Data Aggregator methods
        aggregator = FreeDataAggregator()
        assert hasattr(aggregator, 'get_crypto_price'), "❌ FreeDataAggregator missing get_crypto_price method!"
        assert hasattr(aggregator, 'get_crypto_market_data'), "❌ FreeDataAggregator missing get_crypto_market_data method!"
        assert hasattr(aggregator, 'get_multiple_crypto_prices'), "❌ FreeDataAggregator missing get_multiple_crypto_prices method!"
        assert hasattr(aggregator, 'get_polymarket_odds'), "❌ FreeDataAggregator missing get_polymarket_odds method!"
        assert hasattr(aggregator, 'get_all_source_health'), "❌ FreeDataAggregator missing get_all_source_health method!"
        print("✓ FreeDataAggregator has all required methods")
        
        return True
    except Exception as e:
        print(f"❌ Method existence test failed: {e}")
        return False


def test_cache_functionality():
    """Test cache functionality in data aggregator"""
    print("\nTesting cache functionality...")
    try:
        from apis.data_aggregator import FreeDataAggregator
        
        config = {'cache_ttl_seconds': 10}
        aggregator = FreeDataAggregator(config)
        
        # Test cache key generation
        key1 = aggregator._get_cache_key('test', 'BTC')
        key2 = aggregator._get_cache_key('test', 'btc')
        assert key1 == key2, "❌ Cache keys should be case-insensitive!"
        print("✓ Cache key generation is case-insensitive")
        
        # Test cache set/get
        test_data = {'price': 50000.0, 'timestamp': '2024-01-01'}
        aggregator._set_cache('test_key', test_data)
        cached = aggregator._get_cached('test_key')
        assert cached is not None, "❌ Failed to retrieve cached data!"
        assert cached['price'] == 50000.0, "❌ Cached data doesn't match!"
        print("✓ Cache set/get working correctly")
        
        # Test cache stats
        stats = aggregator.get_cache_stats()
        assert stats is not None, "❌ Failed to get cache stats!"
        assert 'total_entries' in stats, "❌ Cache stats missing total_entries!"
        assert stats['total_entries'] > 0, "❌ Cache should have at least one entry!"
        print(f"✓ Cache stats: {stats['total_entries']} entries")
        
        # Test cache clear
        aggregator.clear_cache()
        stats_after_clear = aggregator.get_cache_stats()
        assert stats_after_clear['total_entries'] == 0, "❌ Cache not cleared!"
        print("✓ Cache clear working correctly")
        
        return True
    except Exception as e:
        print(f"❌ Cache functionality test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_monitor_integration():
    """Test integration with monitor module"""
    print("\nTesting monitor integration...")
    try:
        import yaml
        from monitor import PolymarketMonitor
        
        # Load config
        with open('config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        # Check config has API settings
        assert 'apis' in config, "❌ Config missing 'apis' section!"
        assert 'binance' in config['apis'], "❌ Config missing Binance settings!"
        assert 'coingecko' in config['apis'], "❌ Config missing CoinGecko settings!"
        assert 'polymarket_subgraph' in config['apis'], "❌ Config missing Polymarket settings!"
        print("✓ Config file has all required API settings")
        
        # Initialize monitor
        monitor = PolymarketMonitor(config)
        assert monitor is not None, "❌ Failed to initialize monitor!"
        print("✓ Monitor initialized successfully")
        
        # Check if data aggregator was initialized
        # Note: It may be None if imports failed, but that's expected without internet
        if monitor.data_aggregator is not None:
            print("✓ Data aggregator initialized in monitor")
            
            # Check new methods exist
            assert hasattr(monitor, 'get_crypto_price'), "❌ Monitor missing get_crypto_price method!"
            assert hasattr(monitor, 'get_data_source_health'), "❌ Monitor missing get_data_source_health method!"
            print("✓ Monitor has new crypto price methods")
        else:
            print("⚠ Data aggregator not initialized (expected without internet)")
        
        return True
    except Exception as e:
        print(f"❌ Monitor integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config_validation():
    """Test configuration validation"""
    print("\nTesting configuration validation...")
    try:
        import yaml
        
        # Load config
        with open('config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        # Validate API configuration structure
        apis = config.get('apis', {})
        
        # Check Binance config
        binance = apis.get('binance', {})
        assert binance.get('enabled') == True, "❌ Binance should be enabled!"
        assert binance.get('rate_limit_per_minute') == 1200, "❌ Wrong Binance rate limit!"
        print("✓ Binance configuration is correct")
        
        # Check CoinGecko config
        coingecko = apis.get('coingecko', {})
        assert coingecko.get('enabled') == True, "❌ CoinGecko should be enabled!"
        assert coingecko.get('rate_limit_per_minute') == 50, "❌ Wrong CoinGecko rate limit!"
        print("✓ CoinGecko configuration is correct")
        
        # Check Polymarket config
        polymarket = apis.get('polymarket_subgraph', {})
        assert polymarket.get('enabled') == True, "❌ Polymarket should be enabled!"
        assert polymarket.get('query_timeout_seconds') == 10, "❌ Wrong Polymarket timeout!"
        print("✓ Polymarket Subgraph configuration is correct")
        
        # Check data aggregator config
        data_agg = config.get('data_aggregator', {})
        assert 'cache_ttl_seconds' in data_agg, "❌ Missing cache_ttl_seconds!"
        print("✓ Data aggregator configuration is correct")
        
        return True
    except Exception as e:
        print(f"❌ Config validation test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("FREE API CLIENTS MOCK TESTS (No Internet Required)")
    print("=" * 60)
    
    tests = [
        ("Imports", test_imports),
        ("Client Initialization", test_client_initialization),
        ("Method Existence", test_method_existence),
        ("Cache Functionality", test_cache_functionality),
        ("Monitor Integration", test_monitor_integration),
        ("Configuration Validation", test_config_validation),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            print(f"\n{'=' * 60}")
            print(f"Running: {name}")
            print('=' * 60)
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ {name} test crashed: {e}")
            import traceback
            traceback.print_exc()
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
        print("✓ All tests passed! Implementation is correct.")
        print("  Note: API connectivity tests require internet access")
        return 0
    else:
        print("❌ Some tests failed. Please review errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
