"""
Evaluation configuration.

Friction and overfitting-guard parameters. No optimistic defaults.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class FrictionConfig:
    """Configurable friction for backtests. No optimistic assumptions."""

    commission_rate: float = 0.001  # 0.1% per side
    spread_bps: float = 5.0  # 5 bps spread (half per side)
    slippage_bps: float = 10.0  # 10 bps slippage (per side)
    partial_fill_rate: float = 0.0  # 0 = full fill; 0.2 = 20% of orders partially filled
    partial_fill_ratio_min: float = 0.5  # min fill ratio when partial (e.g. 50%)
    partial_fill_ratio_max: float = 1.0  # max fill ratio when partial (100%)

    def spread_pct(self) -> float:
        return self.spread_bps / 10000.0

    def slippage_pct(self) -> float:
        return self.slippage_bps / 10000.0


@dataclass
class EvaluationConfig:
    """Global evaluation settings."""

    friction: FrictionConfig = field(default_factory=FrictionConfig)
    risk_free_rate: float = 0.02  # annual
    # Walk-forward
    train_days: int = 252  # ~1 year
    test_days: int = 63  # ~1 quarter
    step_days: int = 63  # roll forward by test window
    # Overfitting guard
    oos_sharpe_drop_threshold: float = 0.5  # flag if IS_sharpe - OOS_sharpe > this
    min_trades_for_metrics: int = 10  # require at least N trades per segment
    # Monte Carlo
    monte_carlo_simulations: int = 500
    slippage_min_bps: float = 5.0
    slippage_max_bps: float = 25.0
    # Rolling / segmentation
    rolling_window_trades: int = 20  # for rolling Sharpe
    volatility_percentile_low: float = 33.0  # low vol segment
    volatility_percentile_high: float = 67.0  # high vol segment
