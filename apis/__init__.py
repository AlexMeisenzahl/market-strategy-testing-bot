"""
APIs Module - Free data sources for crypto and prediction markets

This module provides clients for:
- Binance: Real-time crypto prices (free, unlimited via WebSocket)
- CoinGecko: Fallback crypto prices (free, 50 req/min)
- Polymarket Subgraph: On-chain prediction market data (free, GraphQL)
- Price Aggregator: Multi-source consensus pricing
"""

from .binance_client import BinanceClient
from .coingecko_client import CoinGeckoClient
from .polymarket_subgraph import PolymarketSubgraph
from .price_aggregator import PriceAggregator

__all__ = ["BinanceClient", "CoinGeckoClient", "PolymarketSubgraph", "PriceAggregator"]
