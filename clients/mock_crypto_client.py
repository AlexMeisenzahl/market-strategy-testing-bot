"""
Mock Crypto Client

Generates fake cryptocurrency prices for testing without API keys.
"""

import random
from typing import Dict, List, Any
from .base_client import BaseClient


class MockCryptoClient(BaseClient):
    """Client for generating mock cryptocurrency prices"""

    # Base prices for major cryptocurrencies
    BASE_PRICES = {
        "BTC": 45000.0,
        "ETH": 2500.0,
        "SOL": 100.0,
        "XRP": 0.50,
    }

    def __init__(self):
        """Initialize mock crypto client"""
        super().__init__()
        self._current_prices = None

    def connect(self) -> bool:
        """
        Mock connection (always succeeds)

        Returns:
            Always True
        """
        self._connected = True
        return True

    def test_connection(self) -> Dict[str, Any]:
        """
        Test mock connection (always succeeds)

        Returns:
            Success response with mock message
        """
        return {
            "success": True,
            "message": "Mock crypto client ready (no API required)",
            "error": "",
        }

    def _generate_prices(self, symbols: List[str]) -> Dict[str, float]:
        """
        Generate mock prices with ±2% random variation

        Args:
            symbols: List of crypto symbols

        Returns:
            Dictionary of symbol to price
        """
        prices = {}

        for symbol in symbols:
            symbol_upper = symbol.upper()
            if symbol_upper in self.BASE_PRICES:
                base_price = self.BASE_PRICES[symbol_upper]
                # Add random ±2% variation
                variation = random.uniform(-0.02, 0.02)
                price = base_price * (1 + variation)
                prices[symbol_upper] = round(price, 2)

        return prices

    def get_prices(self, symbols: List[str]) -> Dict[str, float]:
        """
        Get mock crypto prices

        Args:
            symbols: List of crypto symbols (e.g., ['BTC', 'ETH', 'SOL', 'XRP'])

        Returns:
            Dictionary mapping symbols to mock prices
        """
        if not self.is_connected():
            self.connect()

        # Generate new prices with random variation each call
        return self._generate_prices(symbols)

    def disconnect(self) -> None:
        """Mock disconnect"""
        super().disconnect()
        self._current_prices = None
