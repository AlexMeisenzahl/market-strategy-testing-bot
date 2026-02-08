"""
Price Aggregator - Multi-source consensus pricing

Combines multiple free data sources for reliable pricing:
- Binance (primary)
- CoinGecko (fallback)
- Median calculation
- Outlier detection
- Automatic failover
"""

import statistics
from typing import Dict, Optional, List, Tuple
from datetime import datetime

from .binance_client import BinanceClient
from .coingecko_client import CoinGeckoClient


class PriceAggregator:
    """
    Aggregate prices from multiple free sources

    Features:
    - Multi-source price fetching
    - Consensus pricing (median)
    - Outlier detection
    - Automatic failover
    - Source health tracking
    """

    def __init__(self, logger=None):
        """
        Initialize price aggregator

        Args:
            logger: Optional logger instance
        """
        self.logger = logger
        self.binance = BinanceClient(logger=logger)
        self.coingecko = CoinGeckoClient(logger=logger)

        # Track source health
        self.source_health = {"binance": True, "coingecko": True}

        # Configuration
        self.outlier_threshold = 0.05  # 5% price deviation threshold
        self.min_sources = 1  # Minimum sources required for consensus

    def get_best_price(self, symbol: str) -> Optional[Dict]:
        """
        Get best price using multi-source consensus

        Args:
            symbol: Trading symbol (e.g., 'BTC', 'BTCUSDT')

        Returns:
            Dictionary with price, sources used, and confidence

        Example:
            >>> aggregator = PriceAggregator()
            >>> result = aggregator.get_best_price('BTC')
            >>> print(f"BTC: ${result['price']:,.2f} (confidence: {result['confidence']})")
        """
        symbol_clean = symbol.upper().replace("USDT", "").replace("USD", "")

        # Collect prices from all sources
        prices = {}

        # Try Binance
        if self.source_health["binance"]:
            binance_symbol = f"{symbol_clean}USDT"
            binance_price = self.binance.get_price(binance_symbol)

            if binance_price:
                prices["binance"] = binance_price
            else:
                self.source_health["binance"] = False
                if self.logger:
                    self.logger.log_warning("Binance source unavailable")

        # Try CoinGecko
        if self.source_health["coingecko"]:
            coingecko_price = self.coingecko.get_price(symbol_clean)

            if coingecko_price:
                prices["coingecko"] = coingecko_price
            else:
                self.source_health["coingecko"] = False
                if self.logger:
                    self.logger.log_warning("CoinGecko source unavailable")

        # Check if we have enough data
        if len(prices) < self.min_sources:
            if self.logger:
                self.logger.log_error(f"Insufficient price sources for {symbol}")
            return None

        # Calculate consensus price
        consensus_result = self._calculate_consensus(prices, symbol_clean)

        if self.logger and consensus_result:
            self.logger.log_info(
                f"Price consensus for {symbol_clean}: "
                f"${consensus_result['price']:,.2f} from {len(prices)} sources"
            )

        return consensus_result

    def get_multiple_prices(self, symbols: List[str]) -> Dict[str, Dict]:
        """
        Get consensus prices for multiple symbols

        Args:
            symbols: List of trading symbols

        Returns:
            Dictionary mapping symbols to price data
        """
        results = {}

        for symbol in symbols:
            price_data = self.get_best_price(symbol)
            if price_data:
                results[symbol] = price_data

        return results

    def _calculate_consensus(
        self, prices: Dict[str, float], symbol: str
    ) -> Optional[Dict]:
        """
        Calculate consensus price from multiple sources

        Args:
            prices: Dictionary of source -> price
            symbol: Symbol name

        Returns:
            Consensus price data
        """
        if not prices:
            return None

        price_values = list(prices.values())

        # Single source - just use it
        if len(price_values) == 1:
            source = list(prices.keys())[0]
            return {
                "symbol": symbol,
                "price": price_values[0],
                "sources": [source],
                "consensus_method": "single_source",
                "confidence": 0.8,  # Lower confidence with single source
                "timestamp": datetime.now().isoformat(),
            }

        # Multiple sources - check for outliers and calculate median
        price_values_sorted = sorted(price_values)
        median_price = statistics.median(price_values_sorted)

        # Detect outliers
        valid_sources = []
        valid_prices = []

        for source, price in prices.items():
            deviation = abs(price - median_price) / median_price

            if deviation <= self.outlier_threshold:
                valid_sources.append(source)
                valid_prices.append(price)
            else:
                if self.logger:
                    self.logger.log_warning(
                        f"Outlier detected: {source} price ${price:,.2f} "
                        f"deviates {deviation*100:.1f}% from median"
                    )

        # If no valid prices, use all (better than nothing)
        if not valid_prices:
            valid_sources = list(prices.keys())
            valid_prices = price_values

        # Recalculate median with valid prices
        final_price = statistics.median(valid_prices)

        # Calculate confidence based on agreement
        if len(valid_prices) > 1:
            price_range = max(valid_prices) - min(valid_prices)
            price_spread = price_range / final_price
            confidence = max(0.5, 1.0 - (price_spread * 10))  # Spread-based confidence
        else:
            confidence = 0.8

        return {
            "symbol": symbol,
            "price": final_price,
            "sources": valid_sources,
            "consensus_method": "median",
            "confidence": min(1.0, confidence),
            "price_range": {
                "min": min(valid_prices),
                "max": max(valid_prices),
                "spread_percent": (max(valid_prices) - min(valid_prices))
                / final_price
                * 100,
            },
            "timestamp": datetime.now().isoformat(),
        }

    def get_price_comparison(self, symbol: str) -> Optional[Dict]:
        """
        Get detailed price comparison across all sources

        Args:
            symbol: Trading symbol

        Returns:
            Detailed comparison data
        """
        symbol_clean = symbol.upper().replace("USDT", "").replace("USD", "")

        comparison = {
            "symbol": symbol_clean,
            "sources": {},
            "timestamp": datetime.now().isoformat(),
        }

        # Get Binance price
        binance_symbol = f"{symbol_clean}USDT"
        binance_price = self.binance.get_price(binance_symbol)
        if binance_price:
            comparison["sources"]["binance"] = {
                "price": binance_price,
                "available": True,
            }
        else:
            comparison["sources"]["binance"] = {"available": False}

        # Get CoinGecko price
        coingecko_price = self.coingecko.get_price(symbol_clean)
        if coingecko_price:
            comparison["sources"]["coingecko"] = {
                "price": coingecko_price,
                "available": True,
            }
        else:
            comparison["sources"]["coingecko"] = {"available": False}

        # Calculate statistics if we have data
        prices = [
            s["price"]
            for s in comparison["sources"].values()
            if s.get("available") and "price" in s
        ]

        if prices:
            comparison["statistics"] = {
                "median": statistics.median(prices),
                "mean": statistics.mean(prices),
                "min": min(prices),
                "max": max(prices),
                "spread": max(prices) - min(prices),
                "spread_percent": (max(prices) - min(prices))
                / statistics.median(prices)
                * 100,
            }

        return comparison

    def health_check(self) -> Dict[str, bool]:
        """
        Check health of all price sources

        Returns:
            Dictionary of source health status
        """
        health = {}

        # Check Binance
        try:
            health["binance"] = self.binance.health_check()
        except:
            health["binance"] = False

        # Check CoinGecko
        try:
            health["coingecko"] = self.coingecko.health_check()
        except:
            health["coingecko"] = False

        # Update internal tracking
        self.source_health.update(health)

        if self.logger:
            healthy_sources = sum(1 for v in health.values() if v)
            self.logger.log_info(
                f"Price sources health check: {healthy_sources}/{len(health)} healthy"
            )

        return health

    def get_source_priority(self) -> List[str]:
        """
        Get list of sources in priority order

        Returns:
            List of source names, healthy sources first
        """
        priority = []

        # Add healthy sources first
        if self.source_health.get("binance"):
            priority.append("binance")
        if self.source_health.get("coingecko"):
            priority.append("coingecko")

        # Add unhealthy sources (for retry)
        if not self.source_health.get("binance"):
            priority.append("binance")
        if not self.source_health.get("coingecko"):
            priority.append("coingecko")

        return priority
