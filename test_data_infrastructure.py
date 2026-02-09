#!/usr/bin/env python3
"""
Integration Test for Data Infrastructure

Tests that all components work together correctly.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

def test_clients():
    """Test all data clients"""
    print("=" * 60)
    print("Testing Data Clients...")
    print("=" * 60)
    
    from clients import (
        MockMarketClient,
        MockCryptoClient,
        PolymarketClient,
        CoinGeckoClient,
    )
    
    # Test mock clients
    print("\n1. Testing MockMarketClient...")
    market_client = MockMarketClient()
    assert market_client.test_connection()["success"], "Mock market connection failed"
    market_client.connect()
    markets = market_client.get_markets(min_volume=1000, limit=5)
    assert len(markets) > 0, "No markets returned"
    print(f"   ✅ Got {len(markets)} mock markets")
    
    print("\n2. Testing MockCryptoClient...")
    crypto_client = MockCryptoClient()
    assert crypto_client.test_connection()["success"], "Mock crypto connection failed"
    crypto_client.connect()
    prices = crypto_client.get_prices(['BTC', 'ETH'])
    assert len(prices) == 2, "Wrong number of prices"
    print(f"   ✅ Got prices for {len(prices)} cryptos")
    
    # Test live clients (will fail gracefully without API keys)
    print("\n3. Testing PolymarketClient (may fail without API)...")
    try:
        poly_client = PolymarketClient()
        result = poly_client.test_connection()
        if result["success"]:
            print(f"   ✅ Polymarket: {result['message']}")
        else:
            print(f"   ⚠️  Polymarket: {result['error']} (expected without API key)")
    except Exception as e:
        print(f"   ⚠️  Polymarket error: {e} (expected without API key)")
    
    print("\n4. Testing CoinGeckoClient...")
    try:
        gecko_client = CoinGeckoClient()
        result = gecko_client.test_connection()
        if result["success"]:
            print(f"   ✅ CoinGecko: {result['message']}")
        else:
            print(f"   ⚠️  CoinGecko: {result['error']}")
    except Exception as e:
        print(f"   ⚠️  CoinGecko error: {e}")
    
    print("\n✅ All client tests passed!\n")


def test_secure_config():
    """Test secure config manager"""
    print("=" * 60)
    print("Testing Secure Config Manager...")
    print("=" * 60)
    
    from services.secure_config_manager import SecureConfigManager
    
    config_mgr = SecureConfigManager()
    
    print("\n1. Testing credential encryption...")
    test_creds = {
        "endpoint": "https://test.example.com",
        "api_key": "secret_key_abc123xyz",
        "api_secret": "super_secret_789"
    }
    config_mgr.save_api_credentials("test", test_creds)
    print("   ✅ Credentials saved")
    
    print("\n2. Testing credential retrieval...")
    loaded = config_mgr.get_api_credentials("test")
    assert loaded["api_key"] == test_creds["api_key"], "Key mismatch!"
    print("   ✅ Credentials loaded correctly")
    
    print("\n3. Testing credential masking...")
    masked = config_mgr.get_masked_credentials("test")
    assert masked["api_key"].startswith("****"), "Not masked!"
    assert masked["api_key"].endswith("123xyz"), "Wrong ending!"
    print(f"   ✅ API key masked: {masked['api_key']}")
    
    print("\n4. Testing data mode detection...")
    mode = config_mgr.get_data_mode()
    print(f"   ✅ Data mode: {mode}")
    
    # Cleanup
    config_mgr.delete_credentials("test")
    print("\n✅ All SecureConfigManager tests passed!\n")


def test_bot_initialization():
    """Test bot can initialize with data clients"""
    print("=" * 60)
    print("Testing Bot Initialization...")
    print("=" * 60)
    
    from run_bot import BotRunner
    
    print("\n1. Creating BotRunner instance...")
    try:
        # This will initialize data clients
        bot = BotRunner("config.example.yaml")
        print("   ✅ Bot created successfully")
        
        print("\n2. Checking data clients...")
        assert bot.market_client is not None, "No market client!"
        assert bot.crypto_client is not None, "No crypto client!"
        print("   ✅ Data clients initialized")
        
        print(f"\n3. Market client type: {type(bot.market_client).__name__}")
        print(f"   Crypto client type: {type(bot.crypto_client).__name__}")
        
        # Test clients work
        print("\n4. Testing market client...")
        markets = bot.market_client.get_markets(min_volume=1000, limit=3)
        print(f"   ✅ Got {len(markets)} markets")
        
        print("\n5. Testing crypto client...")
        prices = bot.crypto_client.get_prices(['BTC'])
        print(f"   ✅ Got {len(prices)} prices")
        
        print("\n✅ Bot initialization tests passed!\n")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        raise


def main():
    """Run all integration tests"""
    print("\n" + "=" * 60)
    print(" Data Infrastructure Integration Tests")
    print("=" * 60 + "\n")
    
    try:
        test_clients()
        test_secure_config()
        test_bot_initialization()
        
        print("=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        print("\nYou can now:")
        print("  1. Run bot with mock data: python run_bot.py")
        print("  2. Configure APIs in dashboard: python start_dashboard.py")
        print("  3. Read documentation: SETUP.md")
        print()
        
        return 0
        
    except Exception as e:
        print("\n" + "=" * 60)
        print("❌ TESTS FAILED")
        print("=" * 60)
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
