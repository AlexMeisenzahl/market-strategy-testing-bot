"""
CoinGecko Client

Fetches real cryptocurrency prices from CoinGecko's free API.
"""

import requests
from typing import Dict, List, Any, Optional
from .base_client import BaseClient


class CoinGeckoClient(BaseClient):
    """Client for fetching real crypto prices from CoinGecko"""

    # Map common symbols to CoinGecko IDs
    SYMBOL_MAP = {
        "BTC": "bitcoin",
        "ETH": "ethereum",
        "SOL": "solana",
        "XRP": "ripple",
    }

    def __init__(
        self,
        endpoint: str = "https://api.coingecko.com/api/v3",
        api_key: Optional[str] = None
    ):
        """
        Initialize CoinGecko client

        Args:
            endpoint: CoinGecko API endpoint
            api_key: Optional API key for higher rate limits (not required for basic tier)
        """
        super().__init__()
        self.endpoint = endpoint.rstrip("/")
        self.api_key = api_key
        self.session = requests.Session()
        
        # Add API key to headers if provided
        if api_key:
            self.session.headers.update({"x-cg-pro-api-key": api_key})

    def connect(self) -> bool:
        """
        Establish connection to CoinGecko

        Returns:
            True if connection successful
        """
        result = self.test_connection()
        self._connected = result["success"]
        return self._connected

    def test_connection(self) -> Dict[str, Any]:
        """
        Test connection to CoinGecko API by fetching BTC price

        Returns:
            Dictionary with success status and message
        """
        try:
            # Try to fetch Bitcoin price as a connection test
            response = self.session.get(
                f"{self.endpoint}/simple/price",
                params={"ids": "bitcoin", "vs_currencies": "usd"},
                timeout=10
            )
            
            if response.status_code == 429:
                return {
                    "success": False,
                    "message": "",
                    "error": "Rate limit exceeded. Free tier allows 50 calls/min. Please wait or upgrade."
                }
            
            response.raise_for_status()
            data = response.json()
            
            if "bitcoin" in data and "usd" in data["bitcoin"]:
                btc_price = data["bitcoin"]["usd"]
                return {
                    "success": True,
                    "message": f"Successfully connected to CoinGecko API (BTC: ${btc_price:,.2f})",
                    "error": ""
                }
            else:
                return {
                    "success": False,
                    "message": "",
                    "error": "Unexpected response format from CoinGecko"
                }
            
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "message": "",
                "error": "Connection timeout. Please check your internet connection."
            }
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "message": "",
                "error": "Cannot connect to CoinGecko. Please check your internet connection."
            }
        except requests.exceptions.HTTPError as e:
            return {
                "success": False,
                "message": "",
                "error": f"HTTP error: {e.response.status_code}"
            }
        except Exception as e:
            return {
                "success": False,
                "message": "",
                "error": f"Unexpected error: {str(e)}"
            }

    def get_prices(self, symbols: List[str]) -> Dict[str, float]:
        """
        Fetch current prices for given crypto symbols

        Args:
            symbols: List of crypto symbols (e.g., ['BTC', 'ETH', 'SOL', 'XRP'])

        Returns:
            Dictionary mapping symbols to prices (e.g., {"BTC": 45000.0, ...})
        """
        if not self.is_connected():
            self.connect()

        try:
            # Convert symbols to CoinGecko IDs
            coin_ids = []
            for symbol in symbols:
                coin_id = self.SYMBOL_MAP.get(symbol.upper())
                if coin_id:
                    coin_ids.append(coin_id)
            
            if not coin_ids:
                return {}
            
            # Fetch prices
            response = self.session.get(
                f"{self.endpoint}/simple/price",
                params={
                    "ids": ",".join(coin_ids),
                    "vs_currencies": "usd"
                },
                timeout=15
            )
            
            # Handle rate limiting gracefully
            if response.status_code == 429:
                print("CoinGecko rate limit exceeded. Returning empty prices.")
                return {}
            
            response.raise_for_status()
            data = response.json()
            
            # Convert back to symbol format
            prices = {}
            for symbol in symbols:
                coin_id = self.SYMBOL_MAP.get(symbol.upper())
                if coin_id and coin_id in data and "usd" in data[coin_id]:
                    prices[symbol.upper()] = float(data[coin_id]["usd"])
            
            return prices
            
        except Exception as e:
            print(f"Error fetching CoinGecko prices: {e}")
            return {}

    def disconnect(self) -> None:
        """Close the session"""
        self.session.close()
        super().disconnect()
