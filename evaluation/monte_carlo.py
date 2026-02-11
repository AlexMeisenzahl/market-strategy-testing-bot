"""
Phase 4 — Monte Carlo robustness.

- Randomize trade order
- Randomize slippage within bounds
- Estimate distribution of returns
- Compute confidence intervals
- Flag unstable strategies
"""

from __future__ import annotations

import copy
import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from evaluation.config import FrictionConfig
from evaluation.friction import apply_friction_to_trades
from evaluation.metrics import _get_pnl, _returns_from_trades


@dataclass
class MonteCarloResult:
    """Result of Monte Carlo simulation."""

    n_simulations: int = 0
    n_trades: int = 0
    return_mean_pct: float = 0.0
    return_std_pct: float = 0.0
    return_median_pct: float = 0.0
    ci_95_low_pct: float = 0.0
    ci_95_high_pct: float = 0.0
    sharpe_mean: float = 0.0
    sharpe_std: float = 0.0
    sharpe_ci_95_low: float = 0.0
    sharpe_ci_95_high: float = 0.0
    unstable: bool = False  # True if distribution too wide or negative median
    unstable_reason: Optional[str] = None
    # Full distribution (optional; can be large)
    return_distribution_pct: List[float] = field(default_factory=list)
    sharpe_distribution: List[float] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "n_simulations": self.n_simulations,
            "n_trades": self.n_trades,
            "return_mean_pct": self.return_mean_pct,
            "return_std_pct": self.return_std_pct,
            "return_median_pct": self.return_median_pct,
            "ci_95_low_pct": self.ci_95_low_pct,
            "ci_95_high_pct": self.ci_95_high_pct,
            "sharpe_mean": self.sharpe_mean,
            "sharpe_std": self.sharpe_std,
            "sharpe_ci_95_low": self.sharpe_ci_95_low,
            "sharpe_ci_95_high": self.sharpe_ci_95_high,
            "unstable": self.unstable,
            "unstable_reason": self.unstable_reason,
        }


def run_monte_carlo(
    trades: List[Dict[str, Any]],
    n_simulations: int = 500,
    slippage_min_bps: float = 5.0,
    slippage_max_bps: float = 25.0,
    initial_capital: float = 10000.0,
    risk_free_rate: float = 0.02,
    shuffle_order: bool = True,
    store_distributions: bool = False,
    seed: Optional[int] = None,
) -> MonteCarloResult:
    """
    Run Monte Carlo: randomize order and slippage, compute return and Sharpe distribution,
    confidence intervals. Flag unstable if CI is very wide or median return negative.
    Uses bounded memory: only stores summary and optionally two arrays of length n_simulations.
    """
    if seed is not None:
        random.seed(seed)
    result = MonteCarloResult(n_simulations=n_simulations, n_trades=len(trades))
    if not trades:
        result.unstable = True
        result.unstable_reason = "No trades"
        return result

    return_pcts: List[float] = []
    sharpes: List[float] = []

    for i in range(n_simulations):
        # Random slippage for this run
        slippage_bps = random.uniform(slippage_min_bps, slippage_max_bps)
        config = FrictionConfig(
            commission_rate=0.001,
            spread_bps=5.0,
            slippage_bps=slippage_bps,
            partial_fill_rate=0.0,
        )
        applied = apply_friction_to_trades(trades, config, seed=seed + i if seed is not None else None)

        if shuffle_order:
            applied = list(applied)
            random.shuffle(applied)

        returns, equity_curve = _returns_from_trades(applied, initial_capital)
        if not returns or equity_curve[-1] <= 0:
            total_return_pct = -100.0
            sharpe = -10.0  # penalize
        else:
            total_return_pct = (equity_curve[-1] / initial_capital - 1.0) * 100.0
            try:
                import numpy as np
                ret_arr = np.array(returns)
                std = np.std(ret_arr, ddof=1)
                if std > 0:
                    mean_r = np.mean(ret_arr)
                    daily_rf = risk_free_rate / 252.0
                    sharpe = float((mean_r - daily_rf) / std * np.sqrt(252))
                else:
                    sharpe = 0.0
            except Exception:
                sharpe = 0.0
        return_pcts.append(total_return_pct)
        sharpes.append(sharpe)

    # Summarize
    try:
        import numpy as np
        ret_arr = np.array(return_pcts)
        result.return_mean_pct = float(np.mean(ret_arr))
        result.return_std_pct = float(np.std(ret_arr, ddof=1)) if len(ret_arr) > 1 else 0.0
        result.return_median_pct = float(np.median(ret_arr))
        result.ci_95_low_pct = float(np.percentile(ret_arr, 2.5))
        result.ci_95_high_pct = float(np.percentile(ret_arr, 97.5))
        sh_arr = np.array(sharpes)
        result.sharpe_mean = float(np.mean(sh_arr))
        result.sharpe_std = float(np.std(sh_arr, ddof=1)) if len(sh_arr) > 1 else 0.0
        result.sharpe_ci_95_low = float(np.percentile(sh_arr, 2.5))
        result.sharpe_ci_95_high = float(np.percentile(sh_arr, 97.5))
        if store_distributions:
            result.return_distribution_pct = list(ret_arr)
            result.sharpe_distribution = list(sh_arr)
    except ImportError:
        return_pcts_sorted = sorted(return_pcts)
        n = len(return_pcts_sorted)
        result.return_mean_pct = sum(return_pcts) / n
        result.return_median_pct = return_pcts_sorted[n // 2] if n else 0.0
        result.ci_95_low_pct = return_pcts_sorted[int(0.025 * n)] if n else 0.0
        result.ci_95_high_pct = return_pcts_sorted[min(int(0.975 * n), n - 1)] if n else 0.0
        result.sharpe_mean = sum(sharpes) / n
        sharpes_sorted = sorted(sharpes)
        result.sharpe_ci_95_low = sharpes_sorted[int(0.025 * n)] if n else 0.0
        result.sharpe_ci_95_high = sharpes_sorted[min(int(0.975 * n), n - 1)] if n else 0.0
        if store_distributions:
            result.return_distribution_pct = return_pcts
            result.sharpe_distribution = sharpes

    # Flag unstable
    if result.return_median_pct < 0:
        result.unstable = True
        result.unstable_reason = "Median return is negative"
    elif (result.ci_95_high_pct - result.ci_95_low_pct) > 50.0:
        result.unstable = True
        result.unstable_reason = "95% CI width > 50% (high variance)"
    elif result.sharpe_ci_95_high - result.sharpe_ci_95_low > 3.0:
        result.unstable = True
        result.unstable_reason = "Sharpe 95% CI width > 3"
    return result
