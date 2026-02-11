"""
Phase 8: Strategy Intelligence & Diagnostics (read-only).

This package provides offline analysis of trade history. It does NOT
modify execution, strategy code, or config. Consumes only:
- logs/trades.csv (via DataParser)
- logs/activity.json (read-only)
- existing backtest outputs (if present)

SAFETY: No automatic changes. All outputs are suggestions for human review.
"""

from analysis.trade_context import enrich_trades_for_analysis
from analysis.diagnostics import StrategyDiagnosticsEngine
from analysis.suggestions import SuggestionGenerator

__all__ = [
    "enrich_trades_for_analysis",
    "StrategyDiagnosticsEngine",
    "SuggestionGenerator",
]
