"""
Dashboard Trade Lifecycle Adapter (read-only).

Normalizes all trade data for display into canonical states:
  OPEN, CLOSED, CANCELLED, ERROR

Data sources: logs/trades.csv (via DataParser), state/bot_state.json positions (via EngineStateReader).
Handles missing exit fields, paper trades, mock markets, partial fills.
Never mutates logs or state. Single source of truth for dashboard trade display.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


# Canonical lifecycle states for UI
LIFECYCLE_OPEN = "OPEN"
LIFECYCLE_CLOSED = "CLOSED"
LIFECYCLE_CANCELLED = "CANCELLED"
LIFECYCLE_ERROR = "ERROR"


def _safe_float(v: Any, default: float = 0.0) -> float:
    if v is None:
        return default
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _safe_str(v: Any, default: str = "") -> str:
    if v is None:
        return default
    s = str(v).strip()
    return s if s else default


def _normalize_closed_trade(row: Dict[str, Any], index: int) -> Dict[str, Any]:
    """Normalize one trade from CSV (or similar) to dashboard schema. Treat as CLOSED."""
    ts = _safe_str(row.get("timestamp") or row.get("entry_time") or row.get("exit_time"))
    entry_ts = _safe_str(row.get("entry_time") or row.get("timestamp"))
    exit_ts = _safe_str(row.get("exit_time") or row.get("timestamp"))
    pnl_usd = _safe_float(row.get("pnl_usd") or row.get("profit_usd"))
    pnl_pct = _safe_float(row.get("pnl_pct") or row.get("profit_pct"))
    status_raw = _safe_str(row.get("status"), "closed").lower()

    # Map raw status to lifecycle; default CLOSED for completed trades
    if status_raw in ("cancelled", "canceled"):
        lifecycle = LIFECYCLE_CANCELLED
    elif status_raw in ("error", "failed", "rejected"):
        lifecycle = LIFECYCLE_ERROR
    else:
        lifecycle = LIFECYCLE_CLOSED

    return {
        "lifecycle": lifecycle,
        "id": row.get("id") or index,
        "symbol": _safe_str(row.get("symbol") or row.get("market")),
        "strategy": _safe_str(row.get("strategy"), "Unknown"),
        "entry_time": entry_ts or ts,
        "exit_time": exit_ts or ts,
        "entry_price": _safe_float(row.get("entry_price")),
        "exit_price": _safe_float(row.get("exit_price")),
        "pnl_usd": round(pnl_usd, 2),
        "pnl_pct": round(pnl_pct, 2),
        "exit_reason": _safe_str(row.get("exit_reason") or row.get("reason")),
        "duration_minutes": int(_safe_float(row.get("duration_minutes"))),
        "outcome": "win" if pnl_usd > 0 else ("loss" if pnl_usd < 0 else "breakeven"),
        "paper": True,  # Dashboard assumes paper; label if needed
    }


def _normalize_open_position(pos: Dict[str, Any], index: int) -> Dict[str, Any]:
    """Normalize one open position from engine state to dashboard schema. OPEN."""
    symbol = _safe_str(pos.get("symbol") or pos.get("market") or pos.get("asset"))
    qty = _safe_float(pos.get("quantity") or pos.get("size"))
    avg_price = _safe_float(pos.get("avg_price") or pos.get("entry_price") or pos.get("price"))
    current_value = _safe_float(pos.get("current_value"))
    if current_value == 0 and qty and avg_price:
        current_value = qty * avg_price

    return {
        "lifecycle": LIFECYCLE_OPEN,
        "id": pos.get("id") or f"open-{index}",
        "symbol": symbol or "—",
        "strategy": _safe_str(pos.get("strategy"), "Unknown"),
        "entry_time": _safe_str(pos.get("entry_time") or pos.get("opened_at")),
        "exit_time": "",
        "entry_price": avg_price,
        "exit_price": 0.0,
        "quantity": qty,
        "current_value": round(current_value, 2),
        "pnl_usd": None,  # open
        "pnl_pct": None,
        "exit_reason": "",
        "duration_minutes": None,
        "outcome": None,
        "paper": True,
    }


def get_normalized_trades(
    data_parser,
    engine_state_reader,
) -> Dict[str, Any]:
    """
    Return normalized trades for dashboard: open (from engine) + closed (from CSV).
    All items have lifecycle in (OPEN, CLOSED, CANCELLED, ERROR).
    """
    open_trades: List[Dict[str, Any]] = []
    closed_trades: List[Dict[str, Any]] = []

    # Open positions from engine state
    try:
        positions = engine_state_reader.get_positions_from_engine()
        if isinstance(positions, list):
            for i, p in enumerate(positions):
                if p.get("quantity") or p.get("size"):
                    open_trades.append(_normalize_open_position(p, i))
    except Exception:
        pass

    # Closed trades from CSV via data_parser
    try:
        all_rows = data_parser.get_all_trades()
        if all_rows:
            for idx, row in enumerate(all_rows):
                norm = _normalize_closed_trade(row, idx)
                closed_trades.append(norm)
    except Exception:
        pass

    # Sort closed by exit/entry time descending (newest first)
    def _sort_key(t: Dict[str, Any]) -> str:
        return t.get("exit_time") or t.get("entry_time") or ""

    closed_trades.sort(key=_sort_key, reverse=True)

    all_list = open_trades + closed_trades

    return {
        "open": open_trades,
        "closed": closed_trades,
        "all": all_list,
        "count_open": len(open_trades),
        "count_closed": len(closed_trades),
    }
