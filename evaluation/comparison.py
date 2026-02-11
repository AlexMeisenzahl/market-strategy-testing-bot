"""
Phase 6 — Strategy comparison.

Compare multiple strategies side-by-side.
Rank by robustness score (not just Sharpe).
Show in-sample vs out-of-sample clearly.
No auto-deploy to live engine.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from evaluation.metrics import StrategyMetrics
from evaluation.walk_forward import WalkForwardResult
from evaluation.monte_carlo import MonteCarloResult
from evaluation.overfitting_guard import OverfittingGuardResult


@dataclass
class StrategyComparisonResult:
    """Side-by-side comparison of multiple strategies."""

    strategies: List[str] = field(default_factory=list)
    # Per-strategy: full metrics, OOS aggregate, Monte Carlo, overfitting guard
    metrics: Dict[str, StrategyMetrics] = field(default_factory=dict)
    walk_forward: Dict[str, WalkForwardResult] = field(default_factory=dict)
    monte_carlo: Dict[str, MonteCarloResult] = field(default_factory=dict)
    overfitting: Dict[str, OverfittingGuardResult] = field(default_factory=dict)
    # Ranked by robustness (descending)
    ranking_by_robustness: List[str] = field(default_factory=list)
    # Table-friendly: in_sample vs out_of_sample
    comparison_table: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "strategies": self.strategies,
            "ranking_by_robustness": self.ranking_by_robustness,
            "comparison_table": self.comparison_table,
            "metrics": {s: m.to_dict() for s, m in self.metrics.items()},
            "walk_forward": {s: w.to_dict() for s, w in self.walk_forward.items()},
            "monte_carlo": {s: m.to_dict() for s, m in self.monte_carlo.items()},
            "overfitting": {s: o.to_dict() for s, o in self.overfitting.items()},
        }


def compare_strategies(
    strategy_trades: Dict[str, List[Dict[str, Any]]],
    config: Optional[Any] = None,
    initial_capital: float = 10000.0,
    risk_free_rate: float = 0.02,
    train_days: int = 252,
    test_days: int = 63,
    step_days: int = 63,
    oos_sharpe_drop_threshold: float = 0.5,
    monte_carlo_sims: int = 500,
    min_trades_for_wf: int = 20,
) -> StrategyComparisonResult:
    """
    Compare multiple strategies: run metrics, walk-forward, Monte Carlo, overfitting guard.
    Rank by robustness score. Build comparison_table with in_sample vs out_of_sample.
    """
    from evaluation.config import EvaluationConfig
    from evaluation.metrics import compute_metrics
    from evaluation.walk_forward import run_walk_forward
    from evaluation.monte_carlo import run_monte_carlo
    from evaluation.overfitting_guard import check_overfitting
    from evaluation.friction import apply_friction_to_trades

    cfg = config or EvaluationConfig()
    result = StrategyComparisonResult(strategies=list(strategy_trades.keys()))

    for name, trades in strategy_trades.items():
        if not trades:
            result.metrics[name] = compute_metrics([], strategy_name=name)
            result.comparison_table.append({
                "strategy": name,
                "in_sample_sharpe": None,
                "out_of_sample_sharpe": None,
                "robustness_score": 0.0,
                "rank": 0,
                "unstable": True,
            })
            continue
        # Friction-applied for fairness
        applied = apply_friction_to_trades(trades, cfg.friction)
        full_metrics = compute_metrics(
            applied,
            strategy_name=name,
            initial_capital=initial_capital,
            risk_free_rate=risk_free_rate,
            rolling_window_trades=cfg.rolling_window_trades,
        )
        result.metrics[name] = full_metrics

        wf = run_walk_forward(
            applied,
            strategy_name=name,
            train_days=train_days,
            test_days=test_days,
            step_days=step_days,
            initial_capital=initial_capital,
            risk_free_rate=risk_free_rate,
            min_trades_test=5,
        )
        result.walk_forward[name] = wf

        mc = run_monte_carlo(
            applied,
            n_simulations=min(monte_carlo_sims, 500),
            slippage_min_bps=cfg.slippage_min_bps,
            slippage_max_bps=cfg.slippage_max_bps,
            initial_capital=initial_capital,
            risk_free_rate=risk_free_rate,
            store_distributions=False,
        )
        result.monte_carlo[name] = mc

        is_sharpe = full_metrics.sharpe_ratio
        oos_sharpe = wf.oos_aggregate.sharpe_ratio if wf.oos_aggregate else 0.0
        oos_count = len(wf.oos_trades_all)
        of = check_overfitting(
            in_sample_sharpe=is_sharpe,
            out_of_sample_sharpe=oos_sharpe,
            oos_sharpe_drop_threshold=oos_sharpe_drop_threshold,
            monte_carlo_unstable=mc.unstable,
            oos_trades_count=oos_count,
        )
        result.overfitting[name] = of

        result.comparison_table.append({
            "strategy": name,
            "in_sample_sharpe": round(is_sharpe, 4),
            "out_of_sample_sharpe": round(oos_sharpe, 4),
            "robustness_score": of.robustness_score,
            "unstable": not of.is_stable or mc.unstable,
            "oos_trades": oos_count,
            "total_trades": full_metrics.n_trades,
        })

    # Rank by robustness (desc)
    table = result.comparison_table
    table.sort(key=lambda x: (x["robustness_score"], x.get("out_of_sample_sharpe") or 0), reverse=True)
    result.ranking_by_robustness = [r["strategy"] for r in table]
    for i, r in enumerate(table, 1):
        r["rank"] = i
    result.comparison_table = table
    return result
