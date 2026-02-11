"""
Evaluation orchestrator.

Run full strategy evaluation (metrics, friction, walk-forward, Monte Carlo, overfitting guard).
Input: trade lists per strategy. No coupling to live execution.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from evaluation.config import EvaluationConfig, FrictionConfig
from evaluation.metrics import StrategyMetrics, compute_metrics
from evaluation.friction import apply_friction_to_trades
from evaluation.walk_forward import WalkForwardResult, run_walk_forward
from evaluation.monte_carlo import MonteCarloResult, run_monte_carlo
from evaluation.overfitting_guard import OverfittingGuardResult, check_overfitting
from evaluation.comparison import compare_strategies, StrategyComparisonResult


@dataclass
class EvaluationReport:
    """Full evaluation report for one or more strategies."""

    config: Dict[str, Any] = field(default_factory=dict)
    strategies: List[str] = field(default_factory=list)
    # Single-strategy full report
    metrics: Optional[StrategyMetrics] = None
    walk_forward: Optional[WalkForwardResult] = None
    monte_carlo: Optional[MonteCarloResult] = None
    overfitting: Optional[OverfittingGuardResult] = None
    # Multi-strategy comparison (if more than one)
    comparison: Optional[StrategyComparisonResult] = None
    success: bool = True
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "config": self.config,
            "strategies": self.strategies,
            "success": self.success,
            "error": self.error,
        }
        if self.metrics:
            d["metrics"] = self.metrics.to_dict()
        if self.walk_forward:
            d["walk_forward"] = self.walk_forward.to_dict()
        if self.monte_carlo:
            d["monte_carlo"] = self.monte_carlo.to_dict()
        if self.overfitting:
            d["overfitting"] = self.overfitting.to_dict()
        if self.comparison:
            d["comparison"] = self.comparison.to_dict()
        return d


def run_evaluation(
    strategy_trades: Dict[str, List[Dict[str, Any]]],
    config: Optional[EvaluationConfig] = None,
    initial_capital: float = 10000.0,
    run_walk_forward_flag: bool = True,
    run_monte_carlo_flag: bool = True,
    run_comparison: bool = True,
) -> EvaluationReport:
    """
    Run full evaluation on one or more strategies' trade lists.
    - Applies friction to all trades
    - Computes metrics (including rolling Sharpe, vol-segmented)
    - Walk-forward validation (OOS aggregate)
    - Monte Carlo (bounded memory: no storing full distributions by default)
    - Overfitting guard and robustness score
    - If multiple strategies: comparison and ranking by robustness

    Does NOT modify live execution. Input is trade data only.
    """
    cfg = config or EvaluationConfig()
    report = EvaluationReport(
        config={
            "commission_rate": cfg.friction.commission_rate,
            "spread_bps": cfg.friction.spread_bps,
            "slippage_bps": cfg.friction.slippage_bps,
            "train_days": cfg.train_days,
            "test_days": cfg.test_days,
            "oos_sharpe_drop_threshold": cfg.oos_sharpe_drop_threshold,
            "monte_carlo_simulations": cfg.monte_carlo_simulations,
        },
        strategies=list(strategy_trades.keys()),
    )
    if not strategy_trades:
        report.success = False
        report.error = "No strategy trades provided"
        return report

    # Single strategy path
    if len(strategy_trades) == 1:
        name = list(strategy_trades.keys())[0]
        trades = strategy_trades[name]
        applied = apply_friction_to_trades(trades, cfg.friction)
        report.metrics = compute_metrics(
            applied,
            strategy_name=name,
            initial_capital=initial_capital,
            risk_free_rate=cfg.risk_free_rate,
            rolling_window_trades=cfg.rolling_window_trades,
            volatility_pct_low=cfg.volatility_percentile_low,
            volatility_pct_high=cfg.volatility_percentile_high,
        )
        if run_walk_forward_flag and len(applied) >= cfg.min_trades_for_metrics:
            report.walk_forward = run_walk_forward(
                applied,
                strategy_name=name,
                train_days=cfg.train_days,
                test_days=cfg.test_days,
                step_days=cfg.step_days,
                initial_capital=initial_capital,
                risk_free_rate=cfg.risk_free_rate,
                min_trades_test=5,
            )
            oos_sharpe = report.walk_forward.oos_aggregate.sharpe_ratio if report.walk_forward.oos_aggregate else 0.0
            oos_count = len(report.walk_forward.oos_trades_all)
        else:
            oos_sharpe = 0.0
            oos_count = 0
        if run_monte_carlo_flag and len(applied) >= 5:
            report.monte_carlo = run_monte_carlo(
                applied,
                n_simulations=cfg.monte_carlo_simulations,
                slippage_min_bps=cfg.slippage_min_bps,
                slippage_max_bps=cfg.slippage_max_bps,
                initial_capital=initial_capital,
                risk_free_rate=cfg.risk_free_rate,
                store_distributions=False,
            )
            report.overfitting = check_overfitting(
                in_sample_sharpe=report.metrics.sharpe_ratio,
                out_of_sample_sharpe=oos_sharpe,
                oos_sharpe_drop_threshold=cfg.oos_sharpe_drop_threshold,
                monte_carlo_unstable=report.monte_carlo.unstable if report.monte_carlo else False,
                oos_trades_count=oos_count,
            )
        else:
            report.overfitting = check_overfitting(
                in_sample_sharpe=report.metrics.sharpe_ratio,
                out_of_sample_sharpe=oos_sharpe,
                oos_sharpe_drop_threshold=cfg.oos_sharpe_drop_threshold,
                monte_carlo_unstable=False,
                oos_trades_count=oos_count,
            )
        return report

    # Multi-strategy: use comparison
    if run_comparison:
        report.comparison = compare_strategies(
            strategy_trades,
            config=cfg,
            initial_capital=initial_capital,
            risk_free_rate=cfg.risk_free_rate,
            train_days=cfg.train_days,
            test_days=cfg.test_days,
            step_days=cfg.step_days,
            oos_sharpe_drop_threshold=cfg.oos_sharpe_drop_threshold,
            monte_carlo_sims=cfg.monte_carlo_simulations,
            min_trades_for_wf=cfg.min_trades_for_metrics,
        )
        # Also set first strategy's metrics for backward compatibility
        first = report.comparison.strategies[0] if report.comparison.strategies else None
        if first and first in report.comparison.metrics:
            report.metrics = report.comparison.metrics[first]
        if first and first in report.comparison.overfitting:
            report.overfitting = report.comparison.overfitting[first]
    return report
