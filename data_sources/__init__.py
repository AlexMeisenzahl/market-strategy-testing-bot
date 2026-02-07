"""
Data Sources Package - Free, high-performance data sources
Includes Binance WebSocket, CoinGecko API, and Polymarket Subgraph
"""

from .binance_client import BinanceClient
from .coingecko_client import CoinGeckoClient
from .polymarket_subgraph import PolymarketSubgraph
from .price_aggregator import PriceAggregator

__all__ = [
    'BinanceClient',
    'CoinGeckoClient',
    'PolymarketSubgraph',
    'PriceAggregator'
]
