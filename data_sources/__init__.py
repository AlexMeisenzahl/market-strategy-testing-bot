"""
Data Sources Package
Provides free, high-performance data sources for crypto and Polymarket data
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
