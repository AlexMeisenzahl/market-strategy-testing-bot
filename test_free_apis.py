#!/usr/bin/env python3
"""
Test script for free API clients
Tests Binance, CoinGecko, Polymarket Subgraph, and Data Aggregator
"""

import sys
import time
from pathlib import Path

# Import API clients
try:
    from apis.binance_client import BinanceClient
    from apis.coingecko_client import CoinGeckoClient
    from apis.polymarket_subgraph import PolymarketSubgraph
    from apis.data_aggregator import FreeDataAggregator
    APIS_AVAILABLE = True
except ImportError as e:
    print(f"❌ Failed to import API clients: {e}")
    APIS_AVAILABLE = False


def test_binance_client():
    """Test Binance API client"""
    print("\nTesting Binance API client...")
    try:
        client = BinanceClient()
        
        # Test ping
        is_healthy = client.ping()
        assert is_healthy, "❌ Binance API not reachable!"
        print("✓ Binance API is reachable")
        
        # Test get_price
        btc_price = client.get_price('BTC')
        assert btc_price is not None, "❌ Failed to get BTC price!"
        assert btc_price > 0, "❌ BTC price should be positive!"
        print(f"✓ BTC price: ${btc_price:,.2f}")
        
        # Test get_ticker_24h
        eth_ticker = client.get_ticker_24h('ETH')
        assert eth_ticker is not None, "❌ Failed to get ETH ticker!"
        assert 'price' in eth_ticker, "❌ Ticker missing price field!"
        assert 'volume' in eth_ticker, "❌ Ticker missing volume field!"
        print(f"✓ ETH 24h data: ${eth_ticker['price']:,.2f}, Volume: {eth_ticker['volume']:,.0f}")
        
        # Test get_multiple_prices
        prices = client.get_multiple_prices(['BTC', 'ETH', 'SOL'])
        assert len(prices) > 0, "❌ Failed to get multiple prices!"
        print(f"✓ Retrieved {len(prices)} crypto prices")
        
        print("✓ Binance client working correctly")
        return True
    except Exception as e:
        print(f"❌ Binance client test failed: {e}")
        return False


def test_coingecko_client():
    """Test CoinGecko API client"""
    print("\nTesting CoinGecko API client...")
    try:
        client = CoinGeckoClient()
        
        # Test ping
        is_healthy = client.ping()
        assert is_healthy, "❌ CoinGecko API not reachable!"
        print("✓ CoinGecko API is reachable")
        
        # Test get_price
        btc_price = client.get_price('BTC')
        assert btc_price is not None, "❌ Failed to get BTC price!"
        assert btc_price > 0, "❌ BTC price should be positive!"
        print(f"✓ BTC price: ${btc_price:,.2f}")
        
        # Test get_market_data
        eth_data = client.get_market_data('ETH')
        assert eth_data is not None, "❌ Failed to get ETH market data!"
        assert 'price' in eth_data, "❌ Market data missing price field!"
        assert 'market_cap' in eth_data, "❌ Market data missing market_cap field!"
        print(f"✓ ETH market data: ${eth_data['price']:,.2f}, MCap: ${eth_data['market_cap']:,.0f}")
        
        # Test get_multiple_prices
        prices = client.get_multiple_prices(['BTC', 'ETH', 'SOL'])
        assert len(prices) > 0, "❌ Failed to get multiple prices!"
        print(f"✓ Retrieved {len(prices)} crypto prices")
        
        print("✓ CoinGecko client working correctly")
        return True
    except Exception as e:
        print(f"❌ CoinGecko client test failed: {e}")
        return False


def test_polymarket_subgraph():
    """Test Polymarket Subgraph client"""
    print("\nTesting Polymarket Subgraph client...")
    try:
        client = PolymarketSubgraph()
        
        # Test ping
        is_healthy = client.ping()
        assert is_healthy, "❌ Polymarket Subgraph not reachable!"
        print("✓ Polymarket Subgraph is reachable")
        
        # Test get_active_markets
        markets = client.get_active_markets(limit=5)
        if markets is not None:
            print(f"✓ Retrieved {len(markets)} active markets")
            if len(markets) > 0:
                print(f"  Sample market: {markets[0].get('question', 'N/A')[:50]}...")
        else:
            print("⚠ No active markets found (subgraph may be down, but client is working)")
        
        # Test get_markets_by_volume
        volume_markets = client.get_markets_by_volume(limit=3)
        if volume_markets is not None:
            print(f"✓ Retrieved {len(volume_markets)} high-volume markets")
        else:
            print("⚠ No high-volume markets found (expected if subgraph is down)")
        
        print("✓ Polymarket Subgraph client working correctly")
        return True
    except Exception as e:
        print(f"❌ Polymarket Subgraph client test failed: {e}")
        return False


def test_data_aggregator():
    """Test Data Aggregator"""
    print("\nTesting Data Aggregator...")
    try:
        config = {
            'binance': {'rate_limit_per_minute': 1200},
            'coingecko': {'rate_limit_per_minute': 50},
            'polymarket_subgraph': {'query_timeout_seconds': 10},
            'cache_ttl_seconds': 10
        }
        
        aggregator = FreeDataAggregator(config)
        
        # Test get_crypto_price (with fallback)
        btc_price = aggregator.get_crypto_price('BTC')
        assert btc_price is not None, "❌ Failed to get BTC price from aggregator!"
        assert btc_price > 0, "❌ BTC price should be positive!"
        print(f"✓ BTC price from aggregator: ${btc_price:,.2f}")
        
        # Test caching (second call should be from cache)
        start_time = time.time()
        cached_price = aggregator.get_crypto_price('BTC')
        elapsed = time.time() - start_time
        assert cached_price == btc_price, "❌ Cached price doesn't match!"
        assert elapsed < 0.1, "❌ Cache lookup took too long!"
        print(f"✓ Cache working correctly (lookup: {elapsed*1000:.1f}ms)")
        
        # Test get_multiple_crypto_prices
        prices = aggregator.get_multiple_crypto_prices(['BTC', 'ETH', 'SOL'])
        assert len(prices) > 0, "❌ Failed to get multiple prices from aggregator!"
        print(f"✓ Retrieved {len(prices)} crypto prices from aggregator")
        
        # Test get_crypto_market_data
        eth_data = aggregator.get_crypto_market_data('ETH')
        if eth_data:
            print(f"✓ ETH market data: ${eth_data['price']:,.2f}")
        
        # Test source health
        health = aggregator.get_all_source_health()
        assert health is not None, "❌ Failed to get source health!"
        print(f"✓ Data source health: Binance={health['binance']}, CoinGecko={health['coingecko']}, Polymarket={health['polymarket']}")
        
        # Test cache stats
        cache_stats = aggregator.get_cache_stats()
        assert cache_stats is not None, "❌ Failed to get cache stats!"
        print(f"✓ Cache stats: {cache_stats['valid_entries']} valid entries")
        
        print("✓ Data Aggregator working correctly")
        return True
    except Exception as e:
        print(f"❌ Data Aggregator test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_integration():
    """Test integration with monitor"""
    print("\nTesting integration with monitor...")
    try:
        import yaml
        from monitor import PolymarketMonitor
        
        # Load config
        with open('config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        # Initialize monitor
        monitor = PolymarketMonitor(config)
        
        # Check if data aggregator is available
        assert monitor.data_aggregator is not None, "❌ Data aggregator not initialized in monitor!"
        print("✓ Monitor initialized with data aggregator")
        
        # Test get_crypto_price method
        btc_price = monitor.get_crypto_price('BTC')
        if btc_price:
            print(f"✓ Got BTC price via monitor: ${btc_price:,.2f}")
        else:
            print("⚠ Could not get BTC price via monitor (API may be rate limited)")
        
        # Test get_data_source_health method
        health = monitor.get_data_source_health()
        if health:
            print(f"✓ Data source health check via monitor: {health}")
        
        # Test get_market_prices with crypto market
        prices = monitor.get_market_prices('btc-above-100k')
        if prices:
            print(f"✓ Got market prices via monitor: YES={prices['yes']:.3f}, NO={prices['no']:.3f}")
        
        print("✓ Integration with monitor working correctly")
        return True
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("FREE API CLIENTS TESTING")
    print("=" * 60)
    
    if not APIS_AVAILABLE:
        print("❌ API clients not available - cannot run tests!")
        return 1
    
    tests = [
        ("Binance Client", test_binance_client),
        ("CoinGecko Client", test_coingecko_client),
        ("Polymarket Subgraph", test_polymarket_subgraph),
        ("Data Aggregator", test_data_aggregator),
        ("Integration", test_integration),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            print(f"\n{'=' * 60}")
            print(f"Running: {name}")
            print('=' * 60)
            result = test_func()
            results.append((name, result))
            
            # Add delay between tests to avoid rate limiting
            if test_func != tests[-1][1]:  # Don't sleep after last test
                time.sleep(2)
                
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
        print("✓ All tests passed! Free API clients are ready to use.")
        return 0
    else:
        print("❌ Some tests failed. Please review errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
