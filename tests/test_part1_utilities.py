"""
Unit Tests for Part 1 Utility Modules

Tests for:
- SymbolMapper
- MarketParser
- RateLimiter
- Error Handlers
- Logging Configuration
- Market Validator Config
"""

import sys
import os
import time
import logging
from pathlib import Path
from unittest.mock import Mock, patch
import threading

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.symbol_mappings import SymbolMapper
from utils.market_parser import MarketParser
from utils.rate_limiter import RateLimiter
from utils.error_handlers import with_retry, handle_api_error
from utils.logging_config import setup_logging, get_logger
from services.market_validator_config import (
    get_discrepancy_level, 
    DiscrepancyLevel,
    ConfidenceLevel,
    get_confidence_score
)


class TestSymbolMapper:
    """Test suite for SymbolMapper"""
    
    def test_to_coingecko(self):
        """Test conversion to CoinGecko format"""
        assert SymbolMapper.to_coingecko('BTC') == 'bitcoin'
        assert SymbolMapper.to_coingecko('ETH') == 'ethereum'
        assert SymbolMapper.to_coingecko('SOL') == 'solana'
        assert SymbolMapper.to_coingecko('AVAX') == 'avalanche-2'
        assert SymbolMapper.to_coingecko('MATIC') == 'matic-network'
        print("✓ test_to_coingecko passed")
    
    def test_to_binance(self):
        """Test conversion to Binance format"""
        assert SymbolMapper.to_binance('BTC') == 'BTCUSDT'
        assert SymbolMapper.to_binance('ETH') == 'ETHUSDT'
        assert SymbolMapper.to_binance('SOL') == 'SOLUSDT'
        print("✓ test_to_binance passed")
    
    def test_to_coinbase(self):
        """Test conversion to Coinbase format"""
        assert SymbolMapper.to_coinbase('BTC') == 'BTC-USD'
        assert SymbolMapper.to_coinbase('ETH') == 'ETH-USD'
        assert SymbolMapper.to_coinbase('SOL') == 'SOL-USD'
        print("✓ test_to_coinbase passed")
    
    def test_from_coingecko(self):
        """Test reverse conversion from CoinGecko"""
        assert SymbolMapper.from_coingecko('bitcoin') == 'BTC'
        assert SymbolMapper.from_coingecko('ethereum') == 'ETH'
        assert SymbolMapper.from_coingecko('solana') == 'SOL'
        print("✓ test_from_coingecko passed")
    
    def test_from_binance(self):
        """Test reverse conversion from Binance"""
        assert SymbolMapper.from_binance('BTCUSDT') == 'BTC'
        assert SymbolMapper.from_binance('ETHUSDT') == 'ETH'
        assert SymbolMapper.from_binance('SOLUSDT') == 'SOL'
        print("✓ test_from_binance passed")
    
    def test_from_coinbase(self):
        """Test reverse conversion from Coinbase"""
        assert SymbolMapper.from_coinbase('BTC-USD') == 'BTC'
        assert SymbolMapper.from_coinbase('ETH-USD') == 'ETH'
        assert SymbolMapper.from_coinbase('SOL-USD') == 'SOL'
        print("✓ test_from_coinbase passed")
    
    def test_get_full_name(self):
        """Test getting full cryptocurrency names"""
        assert SymbolMapper.get_full_name('BTC') == 'Bitcoin'
        assert SymbolMapper.get_full_name('ETH') == 'Ethereum'
        assert SymbolMapper.get_full_name('SOL') == 'Solana'
        print("✓ test_get_full_name passed")
    
    def test_get_all_symbols(self):
        """Test getting all supported symbols"""
        symbols = SymbolMapper.get_all_symbols()
        assert isinstance(symbols, list)
        assert 'BTC' in symbols
        assert 'ETH' in symbols
        assert len(symbols) >= 20
        print(f"✓ test_get_all_symbols passed ({len(symbols)} symbols)")
    
    def test_is_supported(self):
        """Test checking if symbol is supported"""
        assert SymbolMapper.is_supported('BTC') is True
        assert SymbolMapper.is_supported('ETH') is True
        assert SymbolMapper.is_supported('INVALID') is False
        print("✓ test_is_supported passed")


class TestMarketParser:
    """Test suite for MarketParser"""
    
    def test_extract_crypto_info_simple(self):
        """Test extracting crypto info from simple market names"""
        result = MarketParser.extract_crypto_info("Will Bitcoin be above $100,000?")
        assert result['valid'] is True
        assert result['symbol'] == 'BTC'
        assert result['threshold'] == 100000
        assert result['direction'] == 'above'
        print("✓ test_extract_crypto_info_simple passed")
    
    def test_extract_crypto_info_k_notation(self):
        """Test extracting crypto info with 'k' notation"""
        result = MarketParser.extract_crypto_info("BTC > 100k by Feb 2026")
        assert result['valid'] is True
        assert result['symbol'] == 'BTC'
        assert result['threshold'] == 100000
        assert result['direction'] == 'above'
        print("✓ test_extract_crypto_info_k_notation passed")
    
    def test_extract_crypto_info_ethereum(self):
        """Test extracting Ethereum market info"""
        result = MarketParser.extract_crypto_info("Will Ethereum exceed $5,000?")
        assert result['valid'] is True
        assert result['symbol'] == 'ETH'
        assert result['threshold'] == 5000
        assert result['direction'] == 'above'
        print("✓ test_extract_crypto_info_ethereum passed")
    
    def test_extract_crypto_info_below(self):
        """Test extracting crypto info with 'below' direction"""
        result = MarketParser.extract_crypto_info("Will BTC fall below $50,000?")
        assert result['valid'] is True
        assert result['symbol'] == 'BTC'
        assert result['threshold'] == 50000
        assert result['direction'] == 'below'
        print("✓ test_extract_crypto_info_below passed")
    
    def test_extract_crypto_info_invalid(self):
        """Test extraction with invalid market name"""
        result = MarketParser.extract_crypto_info("Random text without crypto info")
        assert result['valid'] is False
        print("✓ test_extract_crypto_info_invalid passed")
    
    def test_is_crypto_market(self):
        """Test checking if market is about crypto"""
        assert MarketParser.is_crypto_market("Will Bitcoin be above $100,000?") is True
        assert MarketParser.is_crypto_market("Will it rain tomorrow?") is False
        print("✓ test_is_crypto_market passed")
    
    def test_format_threshold(self):
        """Test formatting price thresholds"""
        assert MarketParser.format_threshold(100000) == '$100k'
        assert MarketParser.format_threshold(5000) == '$5k'
        assert MarketParser.format_threshold(500) == '$500'
        print("✓ test_format_threshold passed")


class TestRateLimiter:
    """Test suite for RateLimiter"""
    
    def test_initialization(self):
        """Test rate limiter initialization"""
        limiter = RateLimiter(calls_per_minute=10)
        assert limiter.calls_per_minute == 10
        assert limiter.get_remaining_calls() == 10
        print("✓ test_initialization passed")
    
    def test_acquire_within_limit(self):
        """Test acquiring when within rate limit"""
        limiter = RateLimiter(calls_per_minute=5)
        
        # Should be able to acquire 5 times
        for i in range(5):
            result = limiter.acquire(timeout=1)
            assert result is True
        
        # 6th attempt should fail (or timeout)
        result = limiter.acquire(timeout=0.1)
        assert result is False
        print("✓ test_acquire_within_limit passed")
    
    def test_get_remaining_calls(self):
        """Test getting remaining call count"""
        limiter = RateLimiter(calls_per_minute=10)
        
        assert limiter.get_remaining_calls() == 10
        limiter.acquire()
        assert limiter.get_remaining_calls() == 9
        limiter.acquire()
        assert limiter.get_remaining_calls() == 8
        print("✓ test_get_remaining_calls passed")
    
    def test_reset(self):
        """Test resetting rate limiter"""
        limiter = RateLimiter(calls_per_minute=5)
        
        # Use up some calls
        limiter.acquire()
        limiter.acquire()
        assert limiter.get_remaining_calls() == 3
        
        # Reset
        limiter.reset()
        assert limiter.get_remaining_calls() == 5
        print("✓ test_reset passed")
    
    def test_thread_safety(self):
        """Test thread-safe operation"""
        limiter = RateLimiter(calls_per_minute=20)
        results = []
        
        def make_calls():
            for _ in range(5):
                result = limiter.acquire(timeout=1)
                results.append(result)
        
        # Create multiple threads
        threads = [threading.Thread(target=make_calls) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Should have limited some calls
        assert len(results) == 15
        print(f"✓ test_thread_safety passed ({sum(results)} calls succeeded)")


class TestErrorHandlers:
    """Test suite for error handler decorators"""
    
    def test_with_retry_success(self):
        """Test retry decorator with successful function"""
        call_count = [0]
        
        @with_retry(max_retries=3, backoff_factor=0.1)
        def successful_function():
            call_count[0] += 1
            return "success"
        
        result = successful_function()
        assert result == "success"
        assert call_count[0] == 1
        print("✓ test_with_retry_success passed")
    
    def test_with_retry_eventual_success(self):
        """Test retry decorator with eventual success"""
        call_count = [0]
        
        @with_retry(max_retries=3, backoff_factor=0.1)
        def flaky_function():
            call_count[0] += 1
            if call_count[0] < 3:
                raise Exception("Temporary error")
            return "success"
        
        result = flaky_function()
        assert result == "success"
        assert call_count[0] == 3
        print("✓ test_with_retry_eventual_success passed")
    
    def test_handle_api_error_success(self):
        """Test API error handler with successful function"""
        @handle_api_error(default_return={'error': 'default'})
        def successful_function():
            return {'data': 'success'}
        
        result = successful_function()
        assert result == {'data': 'success'}
        print("✓ test_handle_api_error_success passed")
    
    def test_handle_api_error_failure(self):
        """Test API error handler with failing function"""
        @handle_api_error(default_return={'error': 'default'})
        def failing_function():
            raise Exception("API Error")
        
        result = failing_function()
        assert result == {'error': 'default'}
        print("✓ test_handle_api_error_failure passed")


class TestLoggingConfig:
    """Test suite for logging configuration"""
    
    def test_setup_logging(self):
        """Test setting up logging"""
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = 'test.log'
            logger = setup_logging(
                log_level='INFO',
                log_file=log_file,
                log_dir=tmpdir
            )
            
            assert logger is not None
            assert len(logger.handlers) >= 2  # Console and file handlers
            
            # Test logging
            logger.info("Test message")
            
            # Check file was created
            log_path = Path(tmpdir) / log_file
            assert log_path.exists()
            print("✓ test_setup_logging passed")
    
    def test_get_logger(self):
        """Test getting logger instance"""
        logger = get_logger('test_module')
        assert logger is not None
        assert logger.name == 'test_module'
        print("✓ test_get_logger passed")


class TestMarketValidatorConfig:
    """Test suite for market validator configuration"""
    
    def test_get_discrepancy_level_extreme(self):
        """Test extreme discrepancy detection"""
        result = get_discrepancy_level(
            current_price=150000,  # Far above threshold
            threshold=100000,
            market_yes_price=0.75,  # Very underpriced
            direction='above'
        )
        
        assert result['level'] == DiscrepancyLevel.EXTREME
        assert result['confidence'] == ConfidenceLevel.VERY_HIGH
        assert result['expected_outcome'] is True
        print("✓ test_get_discrepancy_level_extreme passed")
    
    def test_get_discrepancy_level_high(self):
        """Test high discrepancy detection"""
        result = get_discrepancy_level(
            current_price=150000,  # Far above threshold
            threshold=100000,
            market_yes_price=0.85,  # Somewhat underpriced
            direction='above'
        )
        
        assert result['level'] == DiscrepancyLevel.HIGH
        assert result['confidence'] == ConfidenceLevel.HIGH
        print("✓ test_get_discrepancy_level_high passed")
    
    def test_get_discrepancy_level_near_threshold(self):
        """Test near threshold detection"""
        result = get_discrepancy_level(
            current_price=102000,  # Within 5% of threshold
            threshold=100000,
            market_yes_price=0.50,
            direction='above'
        )
        
        assert result['level'] == DiscrepancyLevel.LOW
        print("✓ test_get_discrepancy_level_near_threshold passed")
    
    def test_get_confidence_score(self):
        """Test converting confidence to numeric score"""
        assert get_confidence_score(ConfidenceLevel.VERY_HIGH) == 0.95
        assert get_confidence_score(ConfidenceLevel.HIGH) == 0.85
        assert get_confidence_score(ConfidenceLevel.MEDIUM) == 0.70
        assert get_confidence_score(ConfidenceLevel.LOW) == 0.50
        print("✓ test_get_confidence_score passed")


def run_all_tests():
    """Run all test suites"""
    print("\n" + "="*60)
    print("Running Part 1 Utility Tests")
    print("="*60 + "\n")
    
    # SymbolMapper tests
    print("Testing SymbolMapper...")
    test_mapper = TestSymbolMapper()
    test_mapper.test_to_coingecko()
    test_mapper.test_to_binance()
    test_mapper.test_to_coinbase()
    test_mapper.test_from_coingecko()
    test_mapper.test_from_binance()
    test_mapper.test_from_coinbase()
    test_mapper.test_get_full_name()
    test_mapper.test_get_all_symbols()
    test_mapper.test_is_supported()
    
    # MarketParser tests
    print("\nTesting MarketParser...")
    test_parser = TestMarketParser()
    test_parser.test_extract_crypto_info_simple()
    test_parser.test_extract_crypto_info_k_notation()
    test_parser.test_extract_crypto_info_ethereum()
    test_parser.test_extract_crypto_info_below()
    test_parser.test_extract_crypto_info_invalid()
    test_parser.test_is_crypto_market()
    test_parser.test_format_threshold()
    
    # RateLimiter tests
    print("\nTesting RateLimiter...")
    test_limiter = TestRateLimiter()
    test_limiter.test_initialization()
    test_limiter.test_acquire_within_limit()
    test_limiter.test_get_remaining_calls()
    test_limiter.test_reset()
    test_limiter.test_thread_safety()
    
    # ErrorHandlers tests
    print("\nTesting ErrorHandlers...")
    test_errors = TestErrorHandlers()
    test_errors.test_with_retry_success()
    test_errors.test_with_retry_eventual_success()
    test_errors.test_handle_api_error_success()
    test_errors.test_handle_api_error_failure()
    
    # LoggingConfig tests
    print("\nTesting LoggingConfig...")
    test_logging = TestLoggingConfig()
    test_logging.test_setup_logging()
    test_logging.test_get_logger()
    
    # MarketValidatorConfig tests
    print("\nTesting MarketValidatorConfig...")
    test_validator = TestMarketValidatorConfig()
    test_validator.test_get_discrepancy_level_extreme()
    test_validator.test_get_discrepancy_level_high()
    test_validator.test_get_discrepancy_level_near_threshold()
    test_validator.test_get_confidence_score()
    
    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED!")
    print("="*60 + "\n")


if __name__ == '__main__':
    run_all_tests()
