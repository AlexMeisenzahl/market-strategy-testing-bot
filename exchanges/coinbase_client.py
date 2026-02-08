"""
Coinbase API Client - Free public price data

Provides:
- Spot prices for cryptocurrencies
- No API key required for public endpoints
- Rate limit: 10,000 requests/minute (very generous)
"""

import requests
import time
from typing import Dict, Optional
from datetime import datetime
from decimal import Decimal


class CoinbaseClient:
    """
    Free Coinbase API client for crypto prices

    Features:
    - Spot prices for major cryptocurrencies
    - No authentication required
    - High rate limits (10,000 req/min)
    - Simple REST API
    """

    BASE_URL = "https://api.coinbase.com"

    # Symbol mapping for Coinbase currency pairs
    SYMBOL_TO_PAIR = {
        "BTC": "BTC-USD",
        "ETH": "ETH-USD",
        "SOL": "SOL-USD",
        "XRP": "XRP-USD",
        "ADA": "ADA-USD",
        "DOT": "DOT-USD",
        "AVAX": "AVAX-USD",
        "MATIC": "MATIC-USD",
        "DOGE": "DOGE-USD",
        "LTC": "LTC-USD",
        "LINK": "LINK-USD",
        "UNI": "UNI-USD",
        "ATOM": "ATOM-USD",
        "XLM": "XLM-USD",
        "ALGO": "ALGO-USD",
    }

    def __init__(self, logger=None, cache_duration=30):
        """
        Initialize Coinbase client

        Args:
            logger: Optional logger instance
            cache_duration: Cache duration in seconds (default: 30)
        """
        self.logger = logger
        self.session = requests.Session()
        self.cache = {}
        self.cache_duration = cache_duration
        self.last_request_time = 0
        self.min_request_interval = 0.006  # 10,000 req/min = 0.006s between requests

    def _rate_limit(self) -> None:
        """Enforce rate limiting"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            sleep_time = self.min_request_interval - elapsed
            time.sleep(sleep_time)
        self.last_request_time = time.time()

    def _symbol_to_pair(self, symbol: str) -> str:
        """Convert symbol to Coinbase currency pair"""
        symbol = symbol.upper().replace("USDT", "").replace("USD", "")
        return self.SYMBOL_TO_PAIR.get(symbol, f"{symbol}-USD")

    def _get_cached_price(self, currency_pair: str) -> Optional[Dict]:
        """Get price from cache if still valid"""
        if currency_pair in self.cache:
            cached_data, cached_time = self.cache[currency_pair]
            if time.time() - cached_time < self.cache_duration:
                return cached_data
        return None

    def _cache_price(self, currency_pair: str, data: Dict) -> None:
        """Cache price data"""
        self.cache[currency_pair] = (data, time.time())

    def get_price(self, symbol: str) -> Optional[Decimal]:
        """
        Get current spot price for a cryptocurrency

        Args:
            symbol: Symbol (e.g., 'BTC', 'ETH') or currency pair (e.g., 'BTC-USD')

        Returns:
            Current price as Decimal, or None on error

        Example:
            >>> client = CoinbaseClient()
            >>> btc_price = client.get_price('BTC')
            >>> print(f"BTC: ${btc_price}")
        """
        # Convert symbol to currency pair if needed
        if "-" not in symbol:
            currency_pair = self._symbol_to_pair(symbol)
        else:
            currency_pair = symbol.upper()

        # Check cache first
        cached = self._get_cached_price(currency_pair)
        if cached:
            if self.logger:
                self.logger.log_info(
                    f"Coinbase: {currency_pair} = ${cached['price']} (cached)"
                )
            return cached["price"]

        self._rate_limit()

        try:
            url = f"{self.BASE_URL}/v2/prices/{currency_pair}/spot"

            response = self.session.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()

                if "data" in data and "amount" in data["data"]:
                    price = Decimal(data["data"]["amount"])

                    # Cache the result
                    price_data = {
                        "price": price,
                        "currency": data["data"].get("currency", "USD"),
                        "timestamp": datetime.now().isoformat(),
                        "source": "Coinbase",
                    }
                    self._cache_price(currency_pair, price_data)

                    if self.logger:
                        self.logger.log_info(f"Coinbase: {currency_pair} = ${price}")

                    return price
                else:
                    if self.logger:
                        self.logger.log_warning(
                            f"Coinbase: No price data for {currency_pair}"
                        )
                    return None
            else:
                if self.logger:
                    self.logger.log_error(
                        f"Coinbase API error: HTTP {response.status_code}"
                    )
                return None

        except requests.exceptions.RequestException as e:
            if self.logger:
                self.logger.log_error(f"Coinbase connection error: {str(e)}")
            return None
        except (KeyError, ValueError, Exception) as e:
            if self.logger:
                self.logger.log_error(f"Coinbase response parsing error: {str(e)}")
            return None

    def get_market_data(self, symbol: str) -> Optional[Dict]:
        """
        Get market data for a cryptocurrency (spot price only for Coinbase)

        Args:
            symbol: Symbol or currency pair

        Returns:
            Dictionary with price and metadata
        """
        # Convert symbol to currency pair if needed
        if "-" not in symbol:
            currency_pair = self._symbol_to_pair(symbol)
            symbol_clean = symbol.upper().replace("USDT", "").replace("USD", "")
        else:
            currency_pair = symbol.upper()
            symbol_clean = currency_pair.split("-")[0]

        price = self.get_price(currency_pair)

        if price:
            return {
                "symbol": symbol_clean,
                "currency_pair": currency_pair,
                "price_usd": price,
                "last_updated": datetime.now().isoformat(),
                "source": "Coinbase",
            }
        return None

    def health_check(self) -> bool:
        """
        Check if Coinbase API is accessible

        Returns:
            True if API is healthy
        """
        try:
            # Try to get BTC price as a health check
            url = f"{self.BASE_URL}/v2/prices/BTC-USD/spot"
            response = self.session.get(url, timeout=5)
            return response.status_code == 200
        except:
            return False
