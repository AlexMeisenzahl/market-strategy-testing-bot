"""
Phase 1 — Strategy evaluation metrics.

All metrics are computed on segmented datasets (not full-history only).
- Rolling Sharpe
- Max drawdown
- Profit factor
- Win/loss expectancy
- Volatility-segmented performance
- Return distribution metrics
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


def _get_pnl(t: Dict[str, Any]) -> float:
    """Normalize PnL from trade dict (pnl_usd, profit, pnl)."""
    return float(t.get("pnl_usd", t.get("profit", t.get("pnl", 0.0))))


def _get_time(t: Dict[str, Any]) -> Optional[datetime]:
    """Get trade time (entry_time or timestamp)."""
    raw = t.get("entry_time", t.get("timestamp", t.get("exit_time")))
    if raw is None:
        return None
    if isinstance(raw, datetime):
        return raw
    try:
        s = str(raw).replace("Z", "+00:00")
        return datetime.fromisoformat(s)
    except Exception:
        return None


def _returns_from_trades(
    trades: List[Dict[str, Any]],
    initial_capital: float = 10000.0,
) -> Tuple[List[float], List[float]]:
    """
    Build period returns and equity from trade PnLs.
    Returns (list of period returns as decimals, list of cumulative equity).
    """
    if not trades:
        return [], [initial_capital]
    sorted_trades = sorted(
        [t for t in trades if _get_time(t) is not None],
        key=_get_time,
    )
    equity = initial_capital
    returns: List[float] = []
    equity_curve: List[float] = [equity]
    for t in sorted_trades:
        pnl = _get_pnl(t)
        if equity <= 0:
            equity_curve.append(equity)
            continue
        r = pnl / equity
        returns.append(r)
        equity += pnl
        equity_curve.append(equity)
    return returns, equity_curve


@dataclass
class SegmentMetrics:
    """Metrics for a single segment (e.g. one walk-forward test window)."""

    segment_id: str
    start: Optional[str] = None
    end: Optional[str] = None
    n_trades: int = 0
    sharpe_ratio: float = 0.0
    max_drawdown_pct: float = 0.0
    profit_factor: float = 0.0
    win_rate_pct: float = 0.0
    expectancy: float = 0.0  # $ per trade
    total_return_pct: float = 0.0
    volatility_annual_pct: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0


@dataclass
class StrategyMetrics:
    """
    Full evaluation metrics: full-period and segmented.
    No metric relies solely on in-sample when used with walk-forward.
    """

    strategy_name: str = ""
    n_trades: int = 0
    # Full period (or single segment)
    sharpe_ratio: float = 0.0
    rolling_sharpe_min: Optional[float] = None
    rolling_sharpe_max: Optional[float] = None
    rolling_sharpe_mean: Optional[float] = None
    max_drawdown_pct: float = 0.0
    profit_factor: float = 0.0
    win_rate_pct: float = 0.0
    expectancy: float = 0.0
    total_return_pct: float = 0.0
    volatility_annual_pct: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    # Return distribution
    return_skewness: Optional[float] = None
    return_kurtosis: Optional[float] = None
    return_median: Optional[float] = None
    # Volatility-segmented (low / mid / high vol)
    vol_segment_low: Optional[SegmentMetrics] = None
    vol_segment_mid: Optional[SegmentMetrics] = None
    vol_segment_high: Optional[SegmentMetrics] = None
    # Per-segment list (e.g. walk-forward folds)
    segments: List[SegmentMetrics] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "strategy_name": self.strategy_name,
            "n_trades": self.n_trades,
            "sharpe_ratio": self.sharpe_ratio,
            "max_drawdown_pct": self.max_drawdown_pct,
            "profit_factor": self.profit_factor,
            "win_rate_pct": self.win_rate_pct,
            "expectancy": self.expectancy,
            "total_return_pct": self.total_return_pct,
            "volatility_annual_pct": self.volatility_annual_pct,
            "avg_win": self.avg_win,
            "avg_loss": self.avg_loss,
        }
        if self.rolling_sharpe_min is not None:
            d["rolling_sharpe_min"] = self.rolling_sharpe_min
            d["rolling_sharpe_max"] = self.rolling_sharpe_max
            d["rolling_sharpe_mean"] = self.rolling_sharpe_mean
        if self.return_skewness is not None:
            d["return_skewness"] = self.return_skewness
            d["return_kurtosis"] = self.return_kurtosis
            d["return_median"] = self.return_median
        if self.vol_segment_low:
            d["vol_segment_low"] = _segment_to_dict(self.vol_segment_low)
        if self.vol_segment_mid:
            d["vol_segment_mid"] = _segment_to_dict(self.vol_segment_mid)
        if self.vol_segment_high:
            d["vol_segment_high"] = _segment_to_dict(self.vol_segment_high)
        d["segments"] = [_segment_to_dict(s) for s in self.segments]
        return d


def _segment_to_dict(s: SegmentMetrics) -> Dict[str, Any]:
    return {
        "segment_id": s.segment_id,
        "start": s.start,
        "end": s.end,
        "n_trades": s.n_trades,
        "sharpe_ratio": s.sharpe_ratio,
        "max_drawdown_pct": s.max_drawdown_pct,
        "profit_factor": s.profit_factor,
        "win_rate_pct": s.win_rate_pct,
        "expectancy": s.expectancy,
        "total_return_pct": s.total_return_pct,
        "volatility_annual_pct": s.volatility_annual_pct,
        "avg_win": s.avg_win,
        "avg_loss": s.avg_loss,
    }


def compute_metrics(
    trades: List[Dict[str, Any]],
    strategy_name: str = "",
    initial_capital: float = 10000.0,
    risk_free_rate: float = 0.02,
    rolling_window_trades: int = 20,
    volatility_pct_low: float = 33.0,
    volatility_pct_high: float = 67.0,
) -> StrategyMetrics:
    """
    Compute full metrics on a trade list (segment).
    Includes rolling Sharpe, max drawdown, profit factor, expectancy,
    volatility-segmented performance, and return distribution.
    """
    out = StrategyMetrics(strategy_name=strategy_name, n_trades=len(trades))
    if not trades:
        return out

    returns, equity_curve = _returns_from_trades(trades, initial_capital)
    if not returns:
        return out

    try:
        import numpy as np
    except ImportError:
        logger.warning("numpy not available; some metrics will be omitted")
        np = None

    # Win/loss
    pnls = [_get_pnl(t) for t in trades]
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p < 0]
    n_wins = len(wins)
    n_losses = len(losses)
    out.win_rate_pct = (n_wins / len(trades)) * 100.0 if trades else 0.0
    out.avg_win = (sum(wins) / n_wins) if n_wins else 0.0
    out.avg_loss = (sum(abs(p) for p in losses) / n_losses) if n_losses else 0.0
    gross_profit = sum(wins)
    gross_loss = abs(sum(losses))
    out.profit_factor = gross_profit / gross_loss if gross_loss > 0 else (float("inf") if gross_profit > 0 else 0.0)
    if out.profit_factor == float("inf"):
        out.profit_factor = 999.99  # for JSON
    # Expectancy $ per trade
    out.expectancy = (out.win_rate_pct / 100.0) * out.avg_win - (1 - out.win_rate_pct / 100.0) * out.avg_loss

    # Total return
    total_return = (equity_curve[-1] / initial_capital - 1.0) * 100.0 if equity_curve else 0.0
    out.total_return_pct = total_return

    # Max drawdown %
    peak = equity_curve[0]
    max_dd_pct = 0.0
    for v in equity_curve:
        if v > peak:
            peak = v
        if peak > 0:
            dd = (peak - v) / peak * 100.0
            if dd > max_dd_pct:
                max_dd_pct = dd
    out.max_drawdown_pct = max_dd_pct

    if np is not None:
        ret_arr = np.array(returns)
        n = len(ret_arr)
        if n >= 2:
            std = np.std(ret_arr, ddof=1)
            if std > 0:
                mean_r = np.mean(ret_arr)
                daily_rf = risk_free_rate / 252.0
                out.sharpe_ratio = float((mean_r - daily_rf) / std * np.sqrt(252))
            out.volatility_annual_pct = float(std * np.sqrt(252) * 100.0)
        if n >= 4:
            out.return_median = float(np.median(ret_arr))
            try:
                from scipy import stats
                out.return_skewness = float(stats.skew(ret_arr))
                out.return_kurtosis = float(stats.kurtosis(ret_arr))
            except ImportError:
                pass
        # Rolling Sharpe
        if rolling_window_trades >= 2 and n >= rolling_window_trades:
            rolling_sharpes: List[float] = []
            for i in range(rolling_window_trades, n + 1):
                window = ret_arr[i - rolling_window_trades : i]
                s = np.std(window, ddof=1)
                if s > 0:
                    m = np.mean(window)
                    daily_rf = risk_free_rate / 252.0
                    rs = (m - daily_rf) / s * np.sqrt(252)
                    rolling_sharpes.append(float(rs))
            if rolling_sharpes:
                out.rolling_sharpe_min = min(rolling_sharpes)
                out.rolling_sharpe_max = max(rolling_sharpes)
                out.rolling_sharpe_mean = sum(rolling_sharpes) / len(rolling_sharpes)
    else:
        # Fallback simple Sharpe from full returns
        if len(returns) >= 2:
            mean_r = sum(returns) / len(returns)
            variance = sum((r - mean_r) ** 2 for r in returns) / (len(returns) - 1)
            std = variance ** 0.5 if variance > 0 else 0.0
            if std > 0:
                daily_rf = risk_free_rate / 252.0
                out.sharpe_ratio = (mean_r - daily_rf) / std * (252 ** 0.5)
            out.volatility_annual_pct = std * (252 ** 0.5) * 100.0

    # Volatility-segmented: by |return| percentile of each trade's implied return
    sorted_trades = sorted(
        [t for t in trades if _get_time(t) is not None],
        key=_get_time,
    )
    if len(sorted_trades) >= 6 and np is not None:
        abs_returns = [abs(_get_pnl(t) / initial_capital) for t in sorted_trades]
        p_low = np.percentile(abs_returns, volatility_pct_low)
        p_high = np.percentile(abs_returns, volatility_pct_high)
        low_trades = [t for t, a in zip(sorted_trades, abs_returns) if a <= p_low]
        mid_trades = [t for t, a in zip(sorted_trades, abs_returns) if p_low < a <= p_high]
        high_trades = [t for t, a in zip(sorted_trades, abs_returns) if a > p_high]
        if len(low_trades) >= 3:
            m_low = compute_metrics(low_trades, strategy_name, initial_capital, risk_free_rate, rolling_window_trades=0)
            out.vol_segment_low = SegmentMetrics(
                segment_id="vol_low",
                n_trades=m_low.n_trades,
                sharpe_ratio=m_low.sharpe_ratio,
                max_drawdown_pct=m_low.max_drawdown_pct,
                profit_factor=m_low.profit_factor,
                win_rate_pct=m_low.win_rate_pct,
                expectancy=m_low.expectancy,
                total_return_pct=m_low.total_return_pct,
                volatility_annual_pct=m_low.volatility_annual_pct,
                avg_win=m_low.avg_win,
                avg_loss=m_low.avg_loss,
            )
        if len(mid_trades) >= 3:
            m_mid = compute_metrics(mid_trades, strategy_name, initial_capital, risk_free_rate, rolling_window_trades=0)
            out.vol_segment_mid = SegmentMetrics(
                segment_id="vol_mid",
                n_trades=m_mid.n_trades,
                sharpe_ratio=m_mid.sharpe_ratio,
                max_drawdown_pct=m_mid.max_drawdown_pct,
                profit_factor=m_mid.profit_factor,
                win_rate_pct=m_mid.win_rate_pct,
                expectancy=m_mid.expectancy,
                total_return_pct=m_mid.total_return_pct,
                volatility_annual_pct=m_mid.volatility_annual_pct,
                avg_win=m_mid.avg_win,
                avg_loss=m_mid.avg_loss,
            )
        if len(high_trades) >= 3:
            m_high = compute_metrics(high_trades, strategy_name, initial_capital, risk_free_rate, rolling_window_trades=0)
            out.vol_segment_high = SegmentMetrics(
                segment_id="vol_high",
                n_trades=m_high.n_trades,
                sharpe_ratio=m_high.sharpe_ratio,
                max_drawdown_pct=m_high.max_drawdown_pct,
                profit_factor=m_high.profit_factor,
                win_rate_pct=m_high.win_rate_pct,
                expectancy=m_high.expectancy,
                total_return_pct=m_high.total_return_pct,
                volatility_annual_pct=m_high.volatility_annual_pct,
                avg_win=m_high.avg_win,
                avg_loss=m_high.avg_loss,
            )

    return out
