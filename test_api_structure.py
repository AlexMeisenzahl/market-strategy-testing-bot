#!/usr/bin/env python3
"""
Unit tests for free API clients (no external dependencies)
Tests code structure, error handling, and logic without network calls
"""

import sys
import unittest
from unittest.mock import Mock, MagicMock, patch
from apis.binance_client import BinanceClient
from apis.coingecko_client import CoinGeckoClient
from apis.polymarket_subgraph import PolymarketSubgraph
from apis.price_aggregator import PriceAggregator


class TestBinanceClient(unittest.TestCase):
    """Test Binance client structure and logic"""
    
    def test_initialization(self):
        """Test client initializes correctly"""
        client = BinanceClient()
        self.assertIsNotNone(client)
        self.assertEqual(client.BASE_URL, "https://api.binance.com")
        self.assertEqual(client.WS_URL, "wss://stream.binance.com:9443/ws")
    
    def test_get_price_with_mock(self):
        """Test price fetching with mocked response"""
        client = BinanceClient()
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'symbol': 'BTCUSDT', 'price': '98432.50'}
        
        with patch.object(client.session, 'get', return_value=mock_response):
            price = client.get_price('BTCUSDT')
            self.assertEqual(price, 98432.50)
    
    def test_get_price_error_handling(self):
        """Test error handling for price fetch"""
        client = BinanceClient()
        
        # Mock error response
        mock_response = Mock()
        mock_response.status_code = 500
        
        with patch.object(client.session, 'get', return_value=mock_response):
            price = client.get_price('BTCUSDT')
            self.assertIsNone(price)


class TestCoinGeckoClient(unittest.TestCase):
    """Test CoinGecko client structure and logic"""
    
    def test_initialization(self):
        """Test client initializes correctly"""
        client = CoinGeckoClient()
        self.assertIsNotNone(client)
        self.assertEqual(client.BASE_URL, "https://api.coingecko.com/api/v3")
        self.assertIn('BTC', client.SYMBOL_TO_ID)
        self.assertEqual(client.SYMBOL_TO_ID['BTC'], 'bitcoin')
    
    def test_symbol_conversion(self):
        """Test symbol to ID conversion"""
        client = CoinGeckoClient()
        self.assertEqual(client._symbol_to_id('BTC'), 'bitcoin')
        self.assertEqual(client._symbol_to_id('ETH'), 'ethereum')
        self.assertEqual(client._symbol_to_id('UNKNOWN'), 'unknown')
    
    def test_get_price_with_mock(self):
        """Test price fetching with mocked response"""
        client = CoinGeckoClient()
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'bitcoin': {'usd': 98432.50}}
        
        with patch.object(client.session, 'get', return_value=mock_response):
            # Bypass rate limiting for test
            client._rate_limit = Mock()
            price = client.get_price('bitcoin')
            self.assertEqual(price, 98432.50)


class TestPolymarketSubgraph(unittest.TestCase):
    """Test Polymarket Subgraph client structure and logic"""
    
    def test_initialization(self):
        """Test client initializes correctly"""
        client = PolymarketSubgraph()
        self.assertIsNotNone(client)
        self.assertIn('thegraph.com', client.graphql_url)
    
    def test_alternative_endpoint(self):
        """Test alternative endpoint selection"""
        client = PolymarketSubgraph(use_alternative=True)
        self.assertIn('polymarket.com', client.graphql_url)
    
    def test_query_markets_with_mock(self):
        """Test market query with mocked response"""
        client = PolymarketSubgraph()
        
        # Mock successful GraphQL response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': {
                'markets': [
                    {
                        'id': '1',
                        'question': 'Will BTC reach $100k?',
                        'volumeUSD': '50000',
                        'active': True
                    }
                ]
            }
        }
        
        with patch.object(client.session, 'post', return_value=mock_response):
            # Bypass rate limiting for test
            client._rate_limit = Mock()
            markets = client.query_markets(active=True, first=10)
            self.assertEqual(len(markets), 1)
            self.assertEqual(markets[0]['question'], 'Will BTC reach $100k?')


class TestPriceAggregator(unittest.TestCase):
    """Test Price Aggregator logic"""
    
    def test_initialization(self):
        """Test aggregator initializes correctly"""
        aggregator = PriceAggregator()
        self.assertIsNotNone(aggregator)
        self.assertIsNotNone(aggregator.binance)
        self.assertIsNotNone(aggregator.coingecko)
        self.assertEqual(aggregator.outlier_threshold, 0.05)
    
    def test_consensus_calculation_single_source(self):
        """Test consensus with single price source"""
        aggregator = PriceAggregator()
        
        prices = {'binance': 98432.50}
        result = aggregator._calculate_consensus(prices, 'BTC')
        
        self.assertIsNotNone(result)
        self.assertEqual(result['price'], 98432.50)
        self.assertEqual(result['sources'], ['binance'])
        self.assertEqual(result['consensus_method'], 'single_source')
        self.assertEqual(result['confidence'], 0.8)
    
    def test_consensus_calculation_multiple_sources(self):
        """Test consensus with multiple price sources"""
        aggregator = PriceAggregator()
        
        # Similar prices - good consensus
        prices = {
            'binance': 98432.50,
            'coingecko': 98450.00
        }
        result = aggregator._calculate_consensus(prices, 'BTC')
        
        self.assertIsNotNone(result)
        self.assertEqual(result['consensus_method'], 'median')
        self.assertEqual(len(result['sources']), 2)
        self.assertGreater(result['confidence'], 0.9)  # High confidence due to close prices
    
    def test_outlier_detection(self):
        """Test outlier detection in price aggregation"""
        aggregator = PriceAggregator()
        
        # One price is an outlier
        prices = {
            'binance': 98432.50,
            'coingecko': 150000.00  # Outlier - 50% higher
        }
        result = aggregator._calculate_consensus(prices, 'BTC')
        
        self.assertIsNotNone(result)
        # Both prices should still be considered since we need minimum sources
        # but confidence should be lower
        self.assertLess(result['confidence'], 1.0)


class TestMonitorIntegration(unittest.TestCase):
    """Test monitor.py integration with new APIs"""
    
    def test_imports(self):
        """Test that monitor.py can import the new APIs"""
        try:
            from monitor import PolymarketMonitor
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Failed to import PolymarketMonitor: {e}")
    
    def test_monitor_initialization_with_config(self):
        """Test monitor initializes with new API clients"""
        from monitor import PolymarketMonitor
        
        config = {
            'data_sources': {
                'crypto_prices': {
                    'primary': 'binance',
                    'fallback': 'coingecko',
                    'use_websocket': True
                },
                'polymarket': {
                    'method': 'subgraph',
                    'url': 'https://api.thegraph.com/subgraphs/name/tokenunion/polymarket',
                    'cache_ttl_seconds': 60
                }
            },
            'rate_limit_max': 100,
            'api_timeout_seconds': 5,
            'max_retries': 3,
            'request_delay_seconds': 0.5,
            'rate_limit_warning_threshold': 0.80,
            'rate_limit_pause_threshold': 0.95
        }
        
        try:
            monitor = PolymarketMonitor(config)
            
            # Check that API clients are initialized
            self.assertIsNotNone(monitor.price_aggregator)
            self.assertIsNotNone(monitor.market_client)
            self.assertEqual(monitor.cache_ttl, 60)
            
        except Exception as e:
            self.fail(f"Failed to initialize monitor: {e}")


def run_tests():
    """Run all tests and print results"""
    print("\n" + "="*60)
    print("UNIT TESTS FOR FREE API CLIENTS")
    print("="*60 + "\n")
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestBinanceClient))
    suite.addTests(loader.loadTestsFromTestCase(TestCoinGeckoClient))
    suite.addTests(loader.loadTestsFromTestCase(TestPolymarketSubgraph))
    suite.addTests(loader.loadTestsFromTestCase(TestPriceAggregator))
    suite.addTests(loader.loadTestsFromTestCase(TestMonitorIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("="*60 + "\n")
    
    if result.wasSuccessful():
        print("✓ ALL TESTS PASSED")
        print("\nFree API clients are correctly implemented:")
        print("✓ BinanceClient - Structure and error handling")
        print("✓ CoinGeckoClient - Symbol mapping and pricing")
        print("✓ PolymarketSubgraph - GraphQL integration")
        print("✓ PriceAggregator - Consensus and outlier detection")
        print("✓ Monitor integration - New APIs properly integrated")
        return 0
    else:
        print("✗ SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(run_tests())
