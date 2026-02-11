"""
Phase 3 — Walk-forward validation.

- Train on window A, test on window B
- Roll forward
- Aggregate out-of-sample performance only for reporting.
No metric relies solely on in-sample.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from evaluation.metrics import SegmentMetrics, compute_metrics, _get_time


def _parse_dt(s: Any) -> Optional[datetime]:
    if s is None:
        return None
    if isinstance(s, datetime):
        return s
    try:
        return datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except Exception:
        return None


@dataclass
class WalkForwardResult:
    """Result of walk-forward validation."""

    strategy_name: str = ""
    train_days: int = 0
    test_days: int = 0
    step_days: int = 0
    folds: List[Dict[str, Any]] = field(default_factory=list)  # each: train_trades, test_trades, in_sample_metrics, oos_metrics
    oos_aggregate: Optional[SegmentMetrics] = None  # aggregated OOS only
    oos_trades_all: List[Dict[str, Any]] = field(default_factory=list)
    success: bool = True
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "strategy_name": self.strategy_name,
            "train_days": self.train_days,
            "test_days": self.test_days,
            "step_days": self.step_days,
            "success": self.success,
            "error": self.error,
            "n_folds": len(self.folds),
            "oos_trades_count": len(self.oos_trades_all),
        }
        if self.oos_aggregate:
            d["oos_aggregate"] = {
                "n_trades": self.oos_aggregate.n_trades,
                "sharpe_ratio": self.oos_aggregate.sharpe_ratio,
                "max_drawdown_pct": self.oos_aggregate.max_drawdown_pct,
                "profit_factor": self.oos_aggregate.profit_factor,
                "win_rate_pct": self.oos_aggregate.win_rate_pct,
                "expectancy": self.oos_aggregate.expectancy,
                "total_return_pct": self.oos_aggregate.total_return_pct,
            }
        d["folds"] = []
        for f in self.folds:
            fold_d = {
                "train_start": f.get("train_start"),
                "train_end": f.get("train_end"),
                "test_start": f.get("test_start"),
                "test_end": f.get("test_end"),
                "train_trades": len(f.get("train_trades", [])),
                "test_trades": len(f.get("test_trades", [])),
                "oos_sharpe": f.get("oos_metrics", {}).get("sharpe_ratio"),
                "oos_return_pct": f.get("oos_metrics", {}).get("total_return_pct"),
            }
            d["folds"].append(fold_d)
        return d


def run_walk_forward(
    trades: List[Dict[str, Any]],
    strategy_name: str = "",
    train_days: int = 252,
    test_days: int = 63,
    step_days: int = 63,
    initial_capital: float = 10000.0,
    risk_free_rate: float = 0.02,
    min_trades_test: int = 5,
) -> WalkForwardResult:
    """
    Split trades by time into train/test windows, roll forward, aggregate OOS.
    Returns OOS-only aggregate metrics; in-sample is per-fold only (not used for final score).
    """
    result = WalkForwardResult(
        strategy_name=strategy_name,
        train_days=train_days,
        test_days=test_days,
        step_days=step_days,
    )
    sorted_trades = sorted(
        [t for t in trades if _get_time(t) is not None],
        key=_get_time,
    )
    if not sorted_trades:
        result.success = False
        result.error = "No trades with valid timestamps"
        return result

    t_min = _get_time(sorted_trades[0])
    t_max = _get_time(sorted_trades[-1])
    if t_min is None or t_max is None:
        result.success = False
        result.error = "Could not determine date range"
        return result

    def _naive(d: Optional[datetime]) -> Optional[datetime]:
        if d is None:
            return None
        return d.replace(tzinfo=None) if d.tzinfo else d

    start = _naive(t_min) or t_min
    end = _naive(t_max) or t_max
    total_days = (end - start).days
    if total_days < train_days + test_days:
        result.success = False
        result.error = f"Not enough history: need at least {train_days + test_days} days, got {total_days}"
        return result

    all_oos_trades: List[Dict[str, Any]] = []
    fold_results: List[Dict[str, Any]] = []

    train_end = start + timedelta(days=train_days)
    test_end = train_end + timedelta(days=test_days)

    while test_end <= end + timedelta(days=1):
        train_trades = [
            t for t in sorted_trades
            if _get_time(t) is not None and start <= _naive(_get_time(t)) < train_end
        ]
        test_trades = [
            t for t in sorted_trades
            if _get_time(t) is not None and train_end <= _naive(_get_time(t)) < test_end
        ]

        if len(test_trades) < min_trades_test and test_trades:
            # Still record if we have some OOS trades
            pass
        if not test_trades:
            # Roll forward
            train_end = train_end + timedelta(days=step_days)
            test_end = test_end + timedelta(days=step_days)
            continue

        is_metrics = compute_metrics(
            train_trades,
            strategy_name=strategy_name,
            initial_capital=initial_capital,
            risk_free_rate=risk_free_rate,
            rolling_window_trades=0,
        )
        oos_metrics = compute_metrics(
            test_trades,
            strategy_name=strategy_name,
            initial_capital=initial_capital,
            risk_free_rate=risk_free_rate,
            rolling_window_trades=0,
        )

        fold_results.append({
            "train_start": start.isoformat(),
            "train_end": train_end.isoformat(),
            "test_start": train_end.isoformat(),
            "test_end": test_end.isoformat(),
            "train_trades": train_trades,
            "test_trades": test_trades,
            "in_sample_metrics": is_metrics.to_dict(),
            "oos_metrics": {
                "sharpe_ratio": oos_metrics.sharpe_ratio,
                "max_drawdown_pct": oos_metrics.max_drawdown_pct,
                "profit_factor": oos_metrics.profit_factor,
                "win_rate_pct": oos_metrics.win_rate_pct,
                "expectancy": oos_metrics.expectancy,
                "total_return_pct": oos_metrics.total_return_pct,
                "n_trades": oos_metrics.n_trades,
            },
        })
        all_oos_trades.extend(test_trades)

        train_end = train_end + timedelta(days=step_days)
        test_end = test_end + timedelta(days=step_days)

    result.folds = fold_results
    result.oos_trades_all = all_oos_trades

    if all_oos_trades:
        agg = compute_metrics(
            all_oos_trades,
            strategy_name=strategy_name,
            initial_capital=initial_capital,
            risk_free_rate=risk_free_rate,
            rolling_window_trades=0,
        )
        result.oos_aggregate = SegmentMetrics(
            segment_id="oos_aggregate",
            n_trades=agg.n_trades,
            sharpe_ratio=agg.sharpe_ratio,
            max_drawdown_pct=agg.max_drawdown_pct,
            profit_factor=agg.profit_factor,
            win_rate_pct=agg.win_rate_pct,
            expectancy=agg.expectancy,
            total_return_pct=agg.total_return_pct,
            volatility_annual_pct=agg.volatility_annual_pct,
            avg_win=agg.avg_win,
            avg_loss=agg.avg_loss,
        )
    return result
