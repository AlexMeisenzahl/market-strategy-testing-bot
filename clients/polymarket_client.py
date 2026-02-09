"""
Polymarket Client

Fetches real market data from Polymarket CLOB API.
"""

import requests
from typing import Dict, List, Any, Optional
from .base_client import BaseClient


class PolymarketClient(BaseClient):
    """Client for fetching real Polymarket market data"""

    def __init__(
        self, endpoint: str = "https://clob.polymarket.com", api_key: Optional[str] = None
    ):
        """
        Initialize Polymarket client

        Args:
            endpoint: Polymarket CLOB API endpoint
            api_key: Optional API key for authenticated requests
        """
        super().__init__()
        self.endpoint = endpoint.rstrip("/")
        self.api_key = api_key
        self.session = requests.Session()
        if api_key:
            self.session.headers.update({"Authorization": f"Bearer {api_key}"})

    def connect(self) -> bool:
        """
        Establish connection to Polymarket

        Returns:
            True if connection successful
        """
        result = self.test_connection()
        self._connected = result["success"]
        return self._connected

    def test_connection(self) -> Dict[str, Any]:
        """
        Test connection to Polymarket API

        Returns:
            Dictionary with success status and message
        """
        try:
            # Try to fetch a small sample of markets
            response = self.session.get(
                f"{self.endpoint}/markets",
                params={"limit": 1},
                timeout=10
            )
            
            if response.status_code == 401:
                return {
                    "success": False,
                    "message": "",
                    "error": "Authentication failed. Invalid API key."
                }
            
            if response.status_code == 403:
                return {
                    "success": False,
                    "message": "",
                    "error": "Access forbidden. Check API key permissions."
                }
            
            response.raise_for_status()
            
            return {
                "success": True,
                "message": "Successfully connected to Polymarket API",
                "error": ""
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
                "error": "Cannot connect to Polymarket. Please check your internet connection."
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

    def get_markets(
        self, min_volume: float = 1000, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Fetch markets from Polymarket

        Args:
            min_volume: Minimum 24h volume filter
            limit: Maximum number of markets to return

        Returns:
            List of market dictionaries with standardized fields
        """
        if not self.is_connected():
            self.connect()

        try:
            response = self.session.get(
                f"{self.endpoint}/markets",
                params={"limit": limit},
                timeout=30
            )
            response.raise_for_status()
            
            raw_markets = response.json()
            
            # Transform to standardized format
            markets = []
            for market in raw_markets:
                # Filter by volume
                volume_24h = float(market.get("volume24hr", 0))
                if volume_24h < min_volume:
                    continue
                
                # Extract prices (Polymarket returns yes/no prices)
                yes_price = float(market.get("yesPrice", 0.5))
                no_price = float(market.get("noPrice", 0.5))
                
                markets.append({
                    "market_id": market.get("id", ""),
                    "market_name": market.get("question", "Unknown Market"),
                    "yes_price": yes_price,
                    "no_price": no_price,
                    "volume_24h": volume_24h,
                    "liquidity": float(market.get("liquidity", 0))
                })
            
            return markets
            
        except Exception as e:
            print(f"Error fetching Polymarket markets: {e}")
            return []

    def disconnect(self) -> None:
        """Close the session"""
        self.session.close()
        super().disconnect()
