"""
Data Client Modules

This package contains all data client implementations for fetching
market and crypto data from various sources (both real and mock).
"""

from .base_client import BaseClient
from .polymarket_client import PolymarketClient
from .coingecko_client import CoinGeckoClient
from .mock_market_client import MockMarketClient
from .mock_crypto_client import MockCryptoClient

__all__ = [
    "BaseClient",
    "PolymarketClient",
    "CoinGeckoClient",
    "MockMarketClient",
    "MockCryptoClient",
]
