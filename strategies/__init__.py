"""
Strategies Module - Trading strategy implementations

Available strategies:
- ArbitrageStrategy: Original arbitrage logic (YES + NO < $1.00)
- MomentumStrategy: Trend-following momentum trading
- NewsStrategy: Event-based rapid trading
- StatisticalArbStrategy: Correlation-based mean reversion
"""

from .arbitrage_strategy import ArbitrageStrategy
from .momentum_strategy import MomentumStrategy
from .news_strategy import NewsStrategy
from .statistical_arb_strategy import StatisticalArbStrategy

__all__ = [
    'ArbitrageStrategy',
    'MomentumStrategy',
    'NewsStrategy',
    'StatisticalArbStrategy'
]
