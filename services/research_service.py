"""
Research Service — Phase 7E

Provides research-grade backtest comparison, parameter sweep access,
and regime-based slicing for analytics. Read-only; no execution impact.
"""

import uuid
from collections import deque
from datetime import datetime
from typing import Any, Dict, List, Optional

# In-memory store for last N backtest runs (no DB required)
_MAX_BACKTEST_RUNS = 50
_backtest_runs: deque = deque(maxlen=_MAX_BACKTEST_RUNS)
_run_by_id: Dict[str, Dict] = {}


def store_backtest_run(result: Dict[str, Any]) -> str:
    """
    Store a backtest result and return a run_id.
    Called after each /api/backtest/run so comparisons can use real data.
    """
    run_id = str(uuid.uuid4())[:8]
    entry = {
        "run_id": run_id,
        "stored_at": datetime.utcnow().isoformat() + "Z",
        "strategy": result.get("strategy", "unknown"),
        "period": result.get("period", {}),
        "success": result.get("success", False),
        "metrics": result.get("metrics", {}),
        "equity_curve": result.get("equity_curve", []),
        "trades_count": len(result.get("trades", [])),
    }
    _backtest_runs.append(entry)
    _run_by_id[run_id] = entry
    return run_id


def get_backtest_runs(limit: int = 20) -> List[Dict]:
    """List recent backtest runs (newest first)."""
    runs = list(_backtest_runs)
    runs.reverse()
    return runs[:limit]


def get_backtest_run(run_id: str) -> Optional[Dict]:
    """Get a single backtest run by id."""
    return _run_by_id.get(run_id)


def get_run_ids_for_comparison(run_ids: List[str]) -> List[Dict]:
    """Return full run records for given run_ids; missing ids omitted."""
    out = []
    for rid in run_ids:
        r = get_backtest_run(rid)
        if r:
            out.append(r)
    return out


def filter_trades_by_regime(
    trades: List[Dict],
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    volatility_regime: Optional[str] = None,
    event_window_start: Optional[str] = None,
    event_window_end: Optional[str] = None,
) -> List[Dict]:
    """
    Filter trades by time and optional regime (volatility, event window).
    Used by analytics endpoints to support regime-based slicing.
    """
    if not trades:
        return trades

    def parse_iso(s: str) -> datetime:
        try:
            if s.endswith("Z"):
                s = s[:-1] + "+00:00"
            return datetime.fromisoformat(s)
        except Exception:
            return datetime.min

    # Time range (on entry_time)
    if start_date:
        start_dt = parse_iso(start_date)
        trades = [t for t in trades if parse_iso(t.get("entry_time", "")) >= start_dt]
    if end_date:
        end_dt = parse_iso(end_date)
        trades = [t for t in trades if parse_iso(t.get("entry_time", "")) <= end_dt]

    # Volatility regime: classify by |pnl| percentile (low/med/high)
    if volatility_regime and trades:
        pnls = [abs(float(t.get("pnl_usd", 0))) for t in trades]
        pnls.sort()
        n = len(pnls)
        p33 = pnls[n // 3] if n >= 3 else pnls[0]
        p67 = pnls[(2 * n) // 3] if n >= 3 else pnls[-1]
        low, med, high = volatility_regime.lower() in ("low", "l"), \
                         volatility_regime.lower() in ("med", "medium", "m"), \
                         volatility_regime.lower() in ("high", "h")
        def in_regime(t):
            a = abs(float(t.get("pnl_usd", 0)))
            if low:
                return a <= p33
            if high:
                return a >= p67
            if med:
                return p33 < a <= p67
            return True
        trades = [t for t in trades if in_regime(t)]

    # Event window: keep only trades whose entry_time falls in [event_window_start, event_window_end]
    if event_window_start and event_window_end:
        start_ev = parse_iso(event_window_start)
        end_ev = parse_iso(event_window_end)
        trades = [
            t for t in trades
            if start_ev <= parse_iso(t.get("entry_time", "")) <= end_ev
        ]

    return trades
