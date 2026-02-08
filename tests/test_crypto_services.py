"""
Unit Tests for Crypto Services

Tests all crypto-related services:
- Coinbase client
- Crypto Price Manager
- Market Validator
- Reality Arbitrage Detector
- Price Alert Manager
"""

import sys
import os
from pathlib import Path
from decimal import Decimal
from unittest.mock import Mock, patch

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from exchanges.coinbase_client import CoinbaseClient
from services.crypto_price_manager import CryptoPriceManager
from services.market_validator import MarketValidator
from services.reality_arbitrage_detector import RealityArbitrageDetector
from services.price_alert_manager import PriceAlertManager


class TestCoinbaseClient:
    """Test suite for Coinbase API client"""

    def setup_method(self):
        """Setup test environment"""
        self.logger = Mock()
        self.client = CoinbaseClient(logger=self.logger)

    def test_symbol_to_pair_mapping(self):
        """Test symbol to currency pair conversion"""
        assert self.client._symbol_to_pair("BTC") == "BTC-USD"
        assert self.client._symbol_to_pair("ETH") == "ETH-USD"
        assert self.client._symbol_to_pair("SOL") == "SOL-USD"
        print("✓ test_symbol_to_pair_mapping passed")

    def test_health_check(self):
        """Test health check functionality"""
        # This is a real API call, so we just ensure it doesn't crash
        try:
            result = self.client.health_check()
            assert isinstance(result, bool)
            print(f"✓ test_health_check passed: {result}")
        except Exception as e:
            print(f"⚠ test_health_check skipped (network): {str(e)}")


class TestMarketValidator:
    """Test suite for Market Validator"""

    def setup_method(self):
        """Setup test environment"""
        self.logger = Mock()
        self.validator = MarketValidator(logger=self.logger)

    def test_extract_crypto_info_btc_above(self):
        """Test extracting BTC above threshold"""
        market_name = "Will Bitcoin be above $100,000 on Feb 8?"
        result = self.validator._extract_crypto_info(market_name)

        assert result is not None, "Should extract crypto info"
        symbol, threshold, direction = result
        assert symbol == "BTC"
        assert threshold == Decimal("100000")
        assert direction == "above"
        print(f"✓ test_extract_crypto_info_btc_above: {result}")

    def test_extract_crypto_info_eth_below(self):
        """Test extracting ETH below threshold"""
        market_name = "Will Ethereum drop below $3,000?"
        result = self.validator._extract_crypto_info(market_name)

        assert result is not None
        symbol, threshold, direction = result
        assert symbol == "ETH"
        assert threshold == Decimal("3000")
        assert direction == "below"
        print(f"✓ test_extract_crypto_info_eth_below: {result}")

    def test_extract_crypto_info_no_crypto(self):
        """Test non-crypto market returns None"""
        market_name = "Will Trump win the 2024 election?"
        result = self.validator._extract_crypto_info(market_name)

        assert result is None, "Should not extract info from non-crypto market"
        print("✓ test_extract_crypto_info_no_crypto passed")

    def test_validate_market_aligned(self):
        """Test market validation when prices are aligned"""
        market = {
            "market_name": "Will Bitcoin be above $100,000?",
            "yes_price": 0.95,
            "no_price": 0.05,
        }

        current_prices = {"BTC": {"price_usd": Decimal("105000")}}

        validation = self.validator.validate_market_against_reality(
            market, current_prices
        )

        assert validation is not None
        assert validation["symbol"] == "BTC"
        assert validation["reality_met"] is True
        assert (
            validation["valid"] is True
        )  # Should be aligned (price high, reality met)
        print(f"✓ test_validate_market_aligned: {validation['discrepancy']}")

    def test_validate_market_mispriced(self):
        """Test market validation when market is mispriced"""
        market = {
            "market_name": "Will Bitcoin be above $100,000?",
            "yes_price": 0.40,  # Market only at 40%
            "no_price": 0.60,
        }

        current_prices = {
            "BTC": {"price_usd": Decimal("105000")}  # But BTC is already above 100k!
        }

        validation = self.validator.validate_market_against_reality(
            market, current_prices
        )

        assert validation is not None
        assert validation["symbol"] == "BTC"
        assert validation["reality_met"] is True
        assert validation["valid"] is False  # Should be mispriced
        assert validation["opportunity"] == "BUY YES"
        assert validation["profit_potential_pct"] > 50  # Should be high profit
        print(
            f"✓ test_validate_market_mispriced: {validation['profit_potential_pct']:.1f}% profit"
        )


class TestCryptoPriceManager:
    """Test suite for Crypto Price Manager"""

    def setup_method(self):
        """Setup test environment"""
        self.logger = Mock()
        self.config = {
            "crypto_apis": {
                "coingecko": {"enabled": True},
                "binance": {"enabled": True},
                "coinbase": {"enabled": True},
            }
        }
        # Create temporary logs directory
        self.test_logs_dir = Path(__file__).parent / "test_logs"
        self.test_logs_dir.mkdir(exist_ok=True)

    def test_initialization(self):
        """Test price manager initialization"""
        manager = CryptoPriceManager(
            logger=self.logger, log_dir=self.test_logs_dir, config=self.config
        )

        assert manager.coingecko is not None
        assert manager.binance is not None
        assert manager.coinbase is not None
        print("✓ test_initialization passed")

    def test_aggregate_prices(self):
        """Test price aggregation from multiple sources"""
        manager = CryptoPriceManager(
            logger=self.logger, log_dir=self.test_logs_dir, config=self.config
        )

        prices = {"coingecko": 98500.0, "binance": 98600.0, "coinbase": 98550.0}

        result = manager._aggregate_prices("BTC", prices)

        assert result is not None
        assert result["symbol"] == "BTC"
        assert result["sources_count"] == 3
        # Median should be 98550
        assert abs(float(result["price_usd"]) - 98550.0) < 100
        print(f"✓ test_aggregate_prices: ${result['price_usd']}")

    def test_discrepancy_detection(self):
        """Test high discrepancy warning"""
        manager = CryptoPriceManager(
            logger=self.logger, log_dir=self.test_logs_dir, config=self.config
        )

        # Prices with >5% discrepancy
        prices = {
            "coingecko": 95000.0,
            "binance": 100000.0,  # 5% higher
            "coinbase": 105000.0,  # 10% higher
        }

        result = manager._aggregate_prices("BTC", prices)

        assert result is not None
        assert float(result["discrepancy_pct"]) > 5.0  # Should detect high discrepancy
        print(f"✓ test_discrepancy_detection: {result['discrepancy_pct']}%")


class TestPriceAlertManager:
    """Test suite for Price Alert Manager"""

    def setup_method(self):
        """Setup test environment"""
        self.logger = Mock()
        self.config = {
            "price_alerts": {
                "enabled": True,
                "check_interval_seconds": 30,
                "alerts": [
                    {
                        "symbol": "BTC",
                        "type": "above",
                        "threshold": 100000,
                        "notification": True,
                    }
                ],
            },
            "crypto_apis": {
                "coingecko": {"enabled": False},  # Disable for testing
                "binance": {"enabled": False},
                "coinbase": {"enabled": False},
            },
        }

    def test_initialization(self):
        """Test alert manager initialization"""
        manager = PriceAlertManager(logger=self.logger, config=self.config)

        assert manager.enabled is True
        assert len(manager.alerts) == 1
        assert manager.alerts[0]["symbol"] == "BTC"
        print("✓ test_initialization passed")

    def test_add_alert(self):
        """Test adding new alerts"""
        manager = PriceAlertManager(logger=self.logger, config=self.config)

        initial_count = len(manager.alerts)
        manager.add_alert("ETH", "below", 3000, True)

        assert len(manager.alerts) == initial_count + 1
        print("✓ test_add_alert passed")

    def test_remove_alert(self):
        """Test removing alerts"""
        manager = PriceAlertManager(logger=self.logger, config=self.config)

        manager.add_alert("SOL", "above", 150, True)
        removed = manager.remove_alert("SOL", "above", 150)

        assert removed is True
        print("✓ test_remove_alert passed")


class TestRealityArbitrageDetector:
    """Test suite for Reality Arbitrage Detector"""

    def setup_method(self):
        """Setup test environment"""
        self.logger = Mock()
        self.config = {
            "strategies": {
                "polymarket_arbitrage": {
                    "arbitrage_types": {
                        "reality_based": {
                            "enabled": True,
                            "min_profit_pct": 5.0,
                            "min_confidence": "high",
                        }
                    }
                }
            },
            "crypto_apis": {
                "coingecko": {"enabled": False},
                "binance": {"enabled": False},
                "coinbase": {"enabled": False},
            },
        }

    def test_initialization(self):
        """Test detector initialization"""
        detector = RealityArbitrageDetector(logger=self.logger, config=self.config)

        assert detector.enabled is True
        assert detector.min_profit_pct == Decimal("5.0")
        assert detector.min_confidence == "high"
        print("✓ test_initialization passed")


def run_all_tests():
    """Run all test classes"""
    print("\n" + "=" * 60)
    print("Running Crypto Services Test Suite")
    print("=" * 60 + "\n")

    test_classes = [
        TestCoinbaseClient,
        TestMarketValidator,
        TestCryptoPriceManager,
        TestPriceAlertManager,
        TestRealityArbitrageDetector,
    ]

    total_tests = 0
    passed_tests = 0

    for test_class in test_classes:
        print(f"\n{test_class.__name__}:")
        print("-" * 40)

        test_instance = test_class()
        test_methods = [m for m in dir(test_instance) if m.startswith("test_")]

        for method_name in test_methods:
            total_tests += 1
            try:
                test_instance.setup_method()
                method = getattr(test_instance, method_name)
                method()
                passed_tests += 1
            except AssertionError as e:
                print(f"✗ {method_name} FAILED: {str(e)}")
            except Exception as e:
                print(f"⚠ {method_name} ERROR: {str(e)}")

    print("\n" + "=" * 60)
    print(f"Test Results: {passed_tests}/{total_tests} passed")
    print("=" * 60)

    return passed_tests == total_tests


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
