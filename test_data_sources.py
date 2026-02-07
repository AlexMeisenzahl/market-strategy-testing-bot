"""
Tests for Free Data Sources
Tests Binance, CoinGecko, Polymarket Subgraph clients and Price Aggregator
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_sources.binance_client import BinanceClient
from data_sources.coingecko_client import CoinGeckoClient
from data_sources.polymarket_subgraph import PolymarketSubgraph
from data_sources.price_aggregator import PriceAggregator


class TestBinanceClient(unittest.TestCase):
    """Test Binance client functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.client = BinanceClient()
    
    @patch('requests.get')
    def test_get_current_price(self, mock_get):
        """Test getting current price via REST API"""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'price': '50000.00'}
        mock_get.return_value = mock_response
        
        # Test
        price = self.client.get_current_price('BTCUSDT')
        
        # Assertions
        self.assertIsNotNone(price)
        self.assertEqual(price, 50000.00)
        mock_get.assert_called_once()
    
    @patch('requests.get')
    def test_get_24h_ticker(self, mock_get):
        """Test getting 24-hour ticker data"""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'symbol': 'BTCUSDT',
            'lastPrice': '50000.00',
            'volume': '1000.0',
            'highPrice': '51000.00',
            'lowPrice': '49000.00',
            'priceChangePercent': '2.5'
        }
        mock_get.return_value = mock_response
        
        # Test
        ticker = self.client.get_24h_ticker('BTCUSDT')
        
        # Assertions
        self.assertIsNotNone(ticker)
        self.assertEqual(ticker['symbol'], 'BTCUSDT')
        self.assertEqual(ticker['price'], 50000.00)
        self.assertEqual(ticker['volume'], 1000.0)
    
    @patch('requests.get')
    def test_get_historical_klines(self, mock_get):
        """Test getting historical candlestick data"""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            [1609459200000, '29000.0', '29500.0', '28500.0', '29200.0', '100.0', 1609462800000, '2920000.0', 500],
            [1609462800000, '29200.0', '29800.0', '29100.0', '29500.0', '120.0', 1609466400000, '3540000.0', 600]
        ]
        mock_get.return_value = mock_response
        
        # Test
        klines = self.client.get_historical_klines('BTCUSDT', interval='1h', limit=2)
        
        # Assertions
        self.assertIsNotNone(klines)
        self.assertEqual(len(klines), 2)
        self.assertEqual(klines[0]['open'], 29000.0)
        self.assertEqual(klines[0]['close'], 29200.0)
    
    def test_get_cached_price(self):
        """Test getting cached price from WebSocket"""
        # Manually add to cache
        self.client.price_cache['BTCUSDT'] = {
            'symbol': 'BTCUSDT',
            'price': 50000.0,
            'volume': 1000.0
        }
        
        # Test
        cached = self.client.get_cached_price('BTCUSDT')
        
        # Assertions
        self.assertIsNotNone(cached)
        self.assertEqual(cached['price'], 50000.0)


class TestCoinGeckoClient(unittest.TestCase):
    """Test CoinGecko client functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.client = CoinGeckoClient()
    
    @patch('requests.get')
    @patch('time.sleep')
    def test_get_price(self, mock_sleep, mock_get):
        """Test getting current price"""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'bitcoin': {'usd': 50000.0}}
        mock_get.return_value = mock_response
        
        # Test
        price = self.client.get_price('BTCUSDT')
        
        # Assertions
        self.assertIsNotNone(price)
        self.assertEqual(price, 50000.0)
    
    @patch('requests.get')
    @patch('time.sleep')
    def test_get_prices_batch(self, mock_sleep, mock_get):
        """Test getting multiple prices"""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'bitcoin': {'usd': 50000.0},
            'ethereum': {'usd': 3000.0}
        }
        mock_get.return_value = mock_response
        
        # Test
        prices = self.client.get_prices_batch(['BTCUSDT', 'ETHUSDT'])
        
        # Assertions
        self.assertIsNotNone(prices)
        self.assertIn('BTCUSDT', prices)
        self.assertIn('ETHUSDT', prices)
        self.assertEqual(prices['BTCUSDT'], 50000.0)
        self.assertEqual(prices['ETHUSDT'], 3000.0)
    
    @patch('requests.get')
    @patch('time.sleep')
    def test_get_market_data(self, mock_sleep, mock_get):
        """Test getting comprehensive market data"""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{
            'symbol': 'btc',
            'current_price': 50000.0,
            'market_cap': 1000000000.0,
            'total_volume': 50000000.0,
            'price_change_percentage_24h': 2.5,
            'high_24h': 51000.0,
            'low_24h': 49000.0,
            'circulating_supply': 19000000.0,
            'last_updated': '2024-01-01T00:00:00Z'
        }]
        mock_get.return_value = mock_response
        
        # Test
        data = self.client.get_market_data('BTCUSDT')
        
        # Assertions
        self.assertIsNotNone(data)
        self.assertEqual(data['price'], 50000.0)
        self.assertEqual(data['market_cap'], 1000000000.0)
    
    def test_symbol_to_coin_id(self):
        """Test symbol mapping"""
        self.assertEqual(self.client._symbol_to_coin_id('BTCUSDT'), 'bitcoin')
        self.assertEqual(self.client._symbol_to_coin_id('ETHUSDT'), 'ethereum')
        self.assertEqual(self.client._symbol_to_coin_id('BNBUSDT'), 'binancecoin')


class TestPolymarketSubgraph(unittest.TestCase):
    """Test Polymarket Subgraph client functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.client = PolymarketSubgraph()
    
    @patch('requests.get')
    def test_query_markets(self, mock_get):
        """Test querying active markets"""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{
            'id': 'market-1',
            'question': 'Will BTC reach $100k?',
            'active': True,
            'volume': 10000.0,
            'liquidity': 5000.0,
            'outcomePrices': [0.6, 0.4]
        }]
        mock_get.return_value = mock_response
        
        # Test
        markets = self.client.query_markets(filters={'active': True}, limit=10)
        
        # Assertions
        self.assertIsNotNone(markets)
        self.assertEqual(len(markets), 1)
        self.assertEqual(markets[0]['id'], 'market-1')
        self.assertEqual(markets[0]['question'], 'Will BTC reach $100k?')
    
    @patch('requests.get')
    def test_get_market(self, mock_get):
        """Test getting specific market"""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'id': 'market-1',
            'question': 'Will BTC reach $100k?',
            'active': True,
            'volume': 10000.0,
            'liquidity': 5000.0,
            'outcomePrices': [0.6, 0.4]
        }
        mock_get.return_value = mock_response
        
        # Test
        market = self.client.get_market('market-1')
        
        # Assertions
        self.assertIsNotNone(market)
        self.assertEqual(market['id'], 'market-1')
        self.assertEqual(market['yes_price'], 0.6)
        self.assertEqual(market['no_price'], 0.4)
    
    @patch('requests.get')
    def test_search_markets(self, mock_get):
        """Test searching markets by keyword"""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                'id': 'market-1',
                'question': 'Will Bitcoin reach $100k?',
                'description': 'Bitcoin price prediction',
                'active': True,
                'outcomePrices': [0.5, 0.5]
            },
            {
                'id': 'market-2',
                'question': 'Will Ethereum reach $10k?',
                'description': 'Ethereum price prediction',
                'active': True,
                'outcomePrices': [0.5, 0.5]
            }
        ]
        mock_get.return_value = mock_response
        
        # Test
        results = self.client.search_markets('bitcoin', limit=20)
        
        # Assertions
        self.assertIsNotNone(results)
        self.assertTrue(len(results) > 0)


class TestPriceAggregator(unittest.TestCase):
    """Test Price Aggregator functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.aggregator = PriceAggregator(enable_websocket=False)
    
    @patch.object(BinanceClient, 'get_current_price')
    def test_get_best_price_binance(self, mock_binance):
        """Test getting price from Binance"""
        mock_binance.return_value = 50000.0
        
        price = self.aggregator.get_best_price('BTCUSDT')
        
        self.assertEqual(price, 50000.0)
        mock_binance.assert_called_once_with('BTCUSDT')
    
    @patch.object(BinanceClient, 'get_current_price')
    @patch.object(CoinGeckoClient, 'get_price')
    def test_get_best_price_fallback(self, mock_coingecko, mock_binance):
        """Test fallback to CoinGecko when Binance fails"""
        mock_binance.return_value = None
        mock_coingecko.return_value = 50000.0
        
        price = self.aggregator.get_best_price('BTCUSDT')
        
        self.assertEqual(price, 50000.0)
        mock_coingecko.assert_called_once()
    
    @patch.object(BinanceClient, 'get_24h_ticker')
    def test_get_best_market_data(self, mock_ticker):
        """Test getting comprehensive market data"""
        mock_ticker.return_value = {
            'symbol': 'BTCUSDT',
            'price': 50000.0,
            'volume': 1000.0,
            'high': 51000.0,
            'low': 49000.0,
            'price_change_percent': 2.5
        }
        
        data = self.aggregator.get_best_market_data('BTCUSDT')
        
        self.assertIsNotNone(data)
        self.assertEqual(data['price'], 50000.0)
    
    @patch.object(CoinGeckoClient, 'get_prices_batch')
    def test_get_prices_batch(self, mock_batch):
        """Test getting multiple prices"""
        mock_batch.return_value = {
            'BTCUSDT': 50000.0,
            'ETHUSDT': 3000.0
        }
        
        prices = self.aggregator.get_prices_batch(['BTCUSDT', 'ETHUSDT'])
        
        self.assertIn('BTCUSDT', prices)
        self.assertIn('ETHUSDT', prices)
        self.assertEqual(prices['BTCUSDT'], 50000.0)
        self.assertEqual(prices['ETHUSDT'], 3000.0)
    
    def test_get_statistics(self):
        """Test getting usage statistics"""
        stats = self.aggregator.get_statistics()
        
        self.assertIn('total_requests', stats)
        self.assertIn('sources', stats)
        self.assertIn('binance_ws', stats['sources'])
        self.assertIn('binance_rest', stats['sources'])
        self.assertIn('coingecko', stats['sources'])


def run_tests():
    """Run all tests"""
    print("Running data sources tests...")
    print("=" * 60)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestBinanceClient))
    suite.addTests(loader.loadTestsFromTestCase(TestCoinGeckoClient))
    suite.addTests(loader.loadTestsFromTestCase(TestPolymarketSubgraph))
    suite.addTests(loader.loadTestsFromTestCase(TestPriceAggregator))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
