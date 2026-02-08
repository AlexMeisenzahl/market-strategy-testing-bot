"""
CoinGecko API Client - Free fallback price source

Provides:
- Crypto prices for 10,000+ coins
- Market cap and volume data
- Free tier: 50 requests/minute
- No API key required
"""

import requests
import time
from typing import Dict, Optional, List
from datetime import datetime


class CoinGeckoClient:
    """
    Free CoinGecko API client for crypto prices

    Features:
    - 10,000+ cryptocurrencies
    - Market data and statistics
    - 50 requests/minute (free tier)
    - No authentication required
    """

    BASE_URL = "https://api.coingecko.com/api/v3"

    # Symbol to CoinGecko ID mapping for common coins
    SYMBOL_TO_ID = {
        "BTC": "bitcoin",
        "ETH": "ethereum",
        "USDT": "tether",
        "BNB": "binancecoin",
        "SOL": "solana",
        "USDC": "usd-coin",
        "XRP": "ripple",
        "ADA": "cardano",
        "AVAX": "avalanche-2",
        "DOGE": "dogecoin",
        "DOT": "polkadot",
        "MATIC": "matic-network",
        "LTC": "litecoin",
        "LINK": "chainlink",
        "UNI": "uniswap",
        "ATOM": "cosmos",
        "XLM": "stellar",
        "ALGO": "algorand",
        "VET": "vechain",
        "ICP": "internet-computer",
    }

    def __init__(self, logger=None):
        """
        Initialize CoinGecko client

        Args:
            logger: Optional logger instance
        """
        self.logger = logger
        self.session = requests.Session()
        self.last_request_time = 0
        self.min_request_interval = 1.2  # 50 req/min = 1.2s between requests

    def _rate_limit(self) -> None:
        """Enforce rate limiting"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            sleep_time = self.min_request_interval - elapsed
            time.sleep(sleep_time)
        self.last_request_time = time.time()

    def _symbol_to_id(self, symbol: str) -> str:
        """Convert symbol to CoinGecko ID"""
        symbol = symbol.upper().replace("USDT", "").replace("USD", "")
        return self.SYMBOL_TO_ID.get(symbol, symbol.lower())

    def get_price(self, coin_id: str, vs_currency: str = "usd") -> Optional[float]:
        """
        Get current price for a cryptocurrency

        Args:
            coin_id: CoinGecko coin ID (e.g., 'bitcoin') or symbol (e.g., 'BTC')
            vs_currency: Currency to price against (default: 'usd')

        Returns:
            Current price as float, or None on error

        Example:
            >>> client = CoinGeckoClient()
            >>> btc_price = client.get_price('bitcoin')
            >>> # or use symbol
            >>> btc_price = client.get_price('BTC')
            >>> print(f"BTC: ${btc_price:,.2f}")
        """
        # Convert symbol to ID if needed
        if coin_id.upper() in self.SYMBOL_TO_ID:
            coin_id = self.SYMBOL_TO_ID[coin_id.upper()]

        self._rate_limit()

        try:
            url = f"{self.BASE_URL}/simple/price"
            params = {"ids": coin_id, "vs_currencies": vs_currency}

            response = self.session.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()

                if coin_id in data and vs_currency in data[coin_id]:
                    price = float(data[coin_id][vs_currency])

                    if self.logger:
                        self.logger.log_info(f"CoinGecko: {coin_id} = ${price:,.2f}")

                    return price
                else:
                    if self.logger:
                        self.logger.log_warning(
                            f"CoinGecko: No price data for {coin_id}"
                        )
                    return None
            else:
                if self.logger:
                    self.logger.log_error(
                        f"CoinGecko API error: HTTP {response.status_code}"
                    )
                return None

        except requests.exceptions.RequestException as e:
            if self.logger:
                self.logger.log_error(f"CoinGecko connection error: {str(e)}")
            return None
        except (KeyError, ValueError) as e:
            if self.logger:
                self.logger.log_error(f"CoinGecko response parsing error: {str(e)}")
            return None

    def get_multiple_prices(
        self, coin_ids: List[str], vs_currency: str = "usd"
    ) -> Dict[str, float]:
        """
        Get prices for multiple cryptocurrencies

        Args:
            coin_ids: List of coin IDs or symbols
            vs_currency: Currency to price against

        Returns:
            Dictionary mapping coin IDs to prices

        Example:
            >>> client = CoinGeckoClient()
            >>> prices = client.get_multiple_prices(['BTC', 'ETH', 'SOL'])
            >>> for coin, price in prices.items():
            ...     print(f"{coin}: ${price:,.2f}")
        """
        # Convert symbols to IDs
        converted_ids = []
        for coin in coin_ids:
            if coin.upper() in self.SYMBOL_TO_ID:
                converted_ids.append(self.SYMBOL_TO_ID[coin.upper()])
            else:
                converted_ids.append(coin.lower())

        self._rate_limit()

        try:
            url = f"{self.BASE_URL}/simple/price"
            params = {"ids": ",".join(converted_ids), "vs_currencies": vs_currency}

            response = self.session.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()

                result = {}
                for coin_id in converted_ids:
                    if coin_id in data and vs_currency in data[coin_id]:
                        result[coin_id] = float(data[coin_id][vs_currency])

                if self.logger:
                    self.logger.log_info(f"CoinGecko: Fetched {len(result)} prices")

                return result
            else:
                if self.logger:
                    self.logger.log_error(
                        f"CoinGecko API error: HTTP {response.status_code}"
                    )
                return {}

        except Exception as e:
            if self.logger:
                self.logger.log_error(f"CoinGecko error: {str(e)}")
            return {}

    def get_market_data(self, coin_id: str, vs_currency: str = "usd") -> Optional[Dict]:
        """
        Get detailed market data for a cryptocurrency

        Args:
            coin_id: CoinGecko coin ID or symbol
            vs_currency: Currency to price against

        Returns:
            Dictionary with price, market cap, volume, and change data
        """
        # Convert symbol to ID if needed
        if coin_id.upper() in self.SYMBOL_TO_ID:
            coin_id = self.SYMBOL_TO_ID[coin_id.upper()]

        self._rate_limit()

        try:
            url = f"{self.BASE_URL}/simple/price"
            params = {
                "ids": coin_id,
                "vs_currencies": vs_currency,
                "include_market_cap": "true",
                "include_24hr_vol": "true",
                "include_24hr_change": "true",
                "include_last_updated_at": "true",
            }

            response = self.session.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()

                if coin_id in data:
                    coin_data = data[coin_id]

                    return {
                        "coin_id": coin_id,
                        "price": float(coin_data.get(vs_currency, 0)),
                        "market_cap": float(
                            coin_data.get(f"{vs_currency}_market_cap", 0)
                        ),
                        "volume_24h": float(coin_data.get(f"{vs_currency}_24h_vol", 0)),
                        "change_24h": float(
                            coin_data.get(f"{vs_currency}_24h_change", 0)
                        ),
                        "last_updated": coin_data.get("last_updated_at", None),
                        "timestamp": datetime.now().isoformat(),
                    }
                return None
            else:
                if self.logger:
                    self.logger.log_error(
                        f"CoinGecko API error: HTTP {response.status_code}"
                    )
                return None

        except Exception as e:
            if self.logger:
                self.logger.log_error(f"CoinGecko market data error: {str(e)}")
            return None

    def search_coins(self, query: str) -> List[Dict]:
        """
        Search for cryptocurrencies by name or symbol

        Args:
            query: Search term

        Returns:
            List of matching coins with ID, name, and symbol
        """
        self._rate_limit()

        try:
            url = f"{self.BASE_URL}/search"
            params = {"query": query}

            response = self.session.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()

                if "coins" in data:
                    return [
                        {
                            "id": coin["id"],
                            "name": coin["name"],
                            "symbol": coin["symbol"].upper(),
                        }
                        for coin in data["coins"][:10]  # Limit to top 10
                    ]
                return []
            else:
                return []

        except Exception as e:
            if self.logger:
                self.logger.log_error(f"CoinGecko search error: {str(e)}")
            return []

    def health_check(self) -> bool:
        """
        Check if CoinGecko API is accessible

        Returns:
            True if API is healthy
        """
        try:
            url = f"{self.BASE_URL}/ping"
            response = self.session.get(url, timeout=5)
            return response.status_code == 200
        except:
            return False
