"""
Strategies Module - Trading strategy implementations

Available strategies:
- ArbitrageStrategy: Original arbitrage logic (YES + NO < $1.00)
- MomentumStrategy: Trend-following momentum trading
- NewsStrategy: Event-based rapid trading
- StatisticalArbStrategy: Correlation-based mean reversion
- MeanReversionStrategy: Trades price deviations from moving average
- VolatilityBreakoutStrategy: Trades breakouts from consolidation periods
- PairsTradingStrategy: Simplified pairs trading on correlated markets

Tracking and Orchestration:
- ArbitrageTracker: Performance metrics tracking for arbitrage
- ArbitrageOrchestrator: Orchestrates arbitrage with integrated tracking
"""

from .arbitrage_strategy import ArbitrageStrategy
from .momentum_strategy import MomentumStrategy
from .news_strategy import NewsStrategy
from .statistical_arb_strategy import StatisticalArbStrategy
from .mean_reversion_strategy import MeanReversionStrategy
from .volatility_breakout_strategy import VolatilityBreakoutStrategy
from .pairs_trading_strategy import PairsTradingStrategy
from .arbitrage_tracker import ArbitrageTracker
from .arbitrage_orchestrator import ArbitrageOrchestrator

__all__ = [
    "ArbitrageStrategy",
    "MomentumStrategy",
    "NewsStrategy",
    "StatisticalArbStrategy",
    "MeanReversionStrategy",
    "VolatilityBreakoutStrategy",
    "PairsTradingStrategy",
    "ArbitrageTracker",
    "ArbitrageOrchestrator",
]
