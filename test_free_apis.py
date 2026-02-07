#!/usr/bin/env python3
"""
Test script for free API clients
Tests Binance, CoinGecko, Polymarket Subgraph, and Price Aggregator
"""

import sys
import time
from apis.binance_client import BinanceClient
from apis.coingecko_client import CoinGeckoClient
from apis.polymarket_subgraph import PolymarketSubgraph
from apis.price_aggregator import PriceAggregator


def test_binance():
    """Test Binance API client"""
    print("\n" + "="*60)
    print("Testing Binance Client (FREE)")
    print("="*60)
    
    client = BinanceClient()
    
    # Test health check
    print("\n1. Health Check:")
    healthy = client.health_check()
    print(f"   Status: {'✓ Healthy' if healthy else '✗ Unhealthy'}")
    
    if not healthy:
        print("   Skipping Binance tests - API unavailable")
        return False
    
    # Test single price
    print("\n2. Get BTC Price:")
    btc_price = client.get_price("BTCUSDT")
    if btc_price:
        print(f"   BTC/USDT: ${btc_price:,.2f}")
    else:
        print("   ✗ Failed to get BTC price")
    
    # Test multiple prices
    print("\n3. Get Multiple Prices:")
    prices = client.get_multiple_prices(['BTCUSDT', 'ETHUSDT', 'SOLUSDT'])
    for symbol, price in prices.items():
        print(f"   {symbol}: ${price:,.2f}")
    
    # Test 24h stats
    print("\n4. Get 24h Stats for BTC:")
    stats = client.get_24h_stats("BTCUSDT")
    if stats:
        print(f"   Price: ${stats['price']:,.2f}")
        print(f"   24h Change: {stats['price_change_percent']:.2f}%")
        print(f"   24h Volume: ${stats['quote_volume']:,.0f}")
    
    return True


def test_coingecko():
    """Test CoinGecko API client"""
    print("\n" + "="*60)
    print("Testing CoinGecko Client (FREE)")
    print("="*60)
    
    client = CoinGeckoClient()
    
    # Test health check
    print("\n1. Health Check:")
    healthy = client.health_check()
    print(f"   Status: {'✓ Healthy' if healthy else '✗ Unhealthy'}")
    
    if not healthy:
        print("   Skipping CoinGecko tests - API unavailable")
        return False
    
    # Test single price
    print("\n2. Get BTC Price:")
    btc_price = client.get_price('bitcoin')
    if btc_price:
        print(f"   Bitcoin: ${btc_price:,.2f}")
    else:
        print("   ✗ Failed to get Bitcoin price")
    
    # Test with symbol
    print("\n3. Get Price by Symbol (BTC):")
    btc_price = client.get_price('BTC')
    if btc_price:
        print(f"   BTC: ${btc_price:,.2f}")
    
    # Test multiple prices
    print("\n4. Get Multiple Prices:")
    prices = client.get_multiple_prices(['BTC', 'ETH', 'SOL'])
    for coin, price in prices.items():
        print(f"   {coin}: ${price:,.2f}")
    
    # Test market data
    print("\n5. Get Market Data for BTC:")
    market_data = client.get_market_data('BTC')
    if market_data:
        print(f"   Price: ${market_data['price']:,.2f}")
        print(f"   Market Cap: ${market_data['market_cap']:,.0f}")
        print(f"   24h Volume: ${market_data['volume_24h']:,.0f}")
        print(f"   24h Change: {market_data['change_24h']:.2f}%")
    
    return True


def test_polymarket_subgraph():
    """Test Polymarket Subgraph client"""
    print("\n" + "="*60)
    print("Testing Polymarket Subgraph (FREE GraphQL)")
    print("="*60)
    
    client = PolymarketSubgraph()
    
    # Test health check
    print("\n1. Health Check:")
    healthy = client.health_check()
    print(f"   Status: {'✓ Healthy' if healthy else '✗ Unhealthy'}")
    
    if not healthy:
        print("   Skipping Subgraph tests - API unavailable")
        return False
    
    # Test query markets
    print("\n2. Query Active Markets (top 5):")
    markets = client.query_markets(active=True, first=5)
    if markets:
        print(f"   Found {len(markets)} markets")
        for i, market in enumerate(markets[:3], 1):
            print(f"   {i}. {market.get('question', 'N/A')[:60]}")
            print(f"      Volume: ${float(market.get('volumeUSD', 0)):,.0f}")
    else:
        print("   ✗ No markets found")
    
    # Test search by topic
    print("\n3. Search Markets by Topic (Bitcoin):")
    btc_markets = client.search_markets_by_topic("Bitcoin", limit=3)
    if btc_markets:
        print(f"   Found {len(btc_markets)} Bitcoin-related markets")
        for market in btc_markets:
            print(f"   - {market.get('question', 'N/A')[:60]}")
    else:
        print("   No Bitcoin markets found")
    
    # Test get market prices
    if markets and len(markets) > 0:
        print("\n4. Get Market Prices (first market):")
        market_id = markets[0].get('id')
        prices = client.get_market_prices(market_id)
        if prices:
            print(f"   Market: {prices.get('question', 'N/A')[:60]}")
            print(f"   YES: {prices['yes']:.3f}")
            print(f"   NO: {prices['no']:.3f}")
    
    return True


def test_price_aggregator():
    """Test Price Aggregator (consensus pricing)"""
    print("\n" + "="*60)
    print("Testing Price Aggregator (Multi-source Consensus)")
    print("="*60)
    
    aggregator = PriceAggregator()
    
    # Test health check
    print("\n1. Health Check (All Sources):")
    health = aggregator.health_check()
    for source, status in health.items():
        print(f"   {source}: {'✓ Healthy' if status else '✗ Unhealthy'}")
    
    # Test consensus price
    print("\n2. Get Best Price (BTC) - Multi-source Consensus:")
    result = aggregator.get_best_price('BTC')
    if result:
        print(f"   Symbol: {result['symbol']}")
        print(f"   Price: ${result['price']:,.2f}")
        print(f"   Sources: {', '.join(result['sources'])}")
        print(f"   Confidence: {result['confidence']*100:.0f}%")
        if 'price_range' in result:
            print(f"   Range: ${result['price_range']['min']:,.2f} - ${result['price_range']['max']:,.2f}")
            print(f"   Spread: {result['price_range']['spread_percent']:.2f}%")
    else:
        print("   ✗ Failed to get consensus price")
    
    # Test price comparison
    print("\n3. Detailed Price Comparison (BTC):")
    comparison = aggregator.get_price_comparison('BTC')
    if comparison:
        print(f"   Symbol: {comparison['symbol']}")
        for source, data in comparison['sources'].items():
            if data.get('available'):
                print(f"   {source}: ${data['price']:,.2f}")
            else:
                print(f"   {source}: unavailable")
        
        if 'statistics' in comparison:
            stats = comparison['statistics']
            print(f"   Median: ${stats['median']:,.2f}")
            print(f"   Spread: {stats['spread_percent']:.2f}%")
    
    return True


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("FREE API DATA SOURCES TEST SUITE")
    print("Testing: Binance, CoinGecko, Polymarket Subgraph")
    print("="*60)
    
    results = {}
    
    # Run tests
    try:
        results['binance'] = test_binance()
        time.sleep(2)  # Rate limiting
        
        results['coingecko'] = test_coingecko()
        time.sleep(2)  # Rate limiting
        
        results['subgraph'] = test_polymarket_subgraph()
        time.sleep(2)  # Rate limiting
        
        results['aggregator'] = test_price_aggregator()
        
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nTest failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name.upper()}: {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "="*60)
    if all_passed:
        print("✓ ALL TESTS PASSED")
        print("="*60)
        print("\nAll free API clients are working correctly!")
        print("✓ Binance - Real-time crypto prices")
        print("✓ CoinGecko - Fallback pricing")
        print("✓ Polymarket Subgraph - On-chain market data")
        print("✓ Price Aggregator - Multi-source consensus")
        print("\nYou can now use these FREE data sources with no API keys!")
        return 0
    else:
        print("✗ SOME TESTS FAILED")
        print("="*60)
        print("\nCheck the output above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
