"""
Free API clients for crypto and prediction market data
No API keys required - 100% free public data sources
"""

from .binance_client import BinanceClient
from .coingecko_client import CoinGeckoClient
from .polymarket_subgraph import PolymarketSubgraph
from .data_aggregator import FreeDataAggregator

__all__ = [
    'BinanceClient',
    'CoinGeckoClient', 
    'PolymarketSubgraph',
    'FreeDataAggregator'
]
