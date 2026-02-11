"""
Phase 8A: Trade post-mortem context for analysis (read-only).

Enriches trade records with derived context for the diagnostics engine.
Does NOT modify execution or logs; operates on in-memory copies only.
Missing fields from logs are derived where possible and labeled as "derived".
"""

from datetime import datetime
from typing import Any, Dict, List


# Audit: trades.csv columns (from logger.py)
# Available: timestamp, market, yes_price, no_price, sum, profit_pct, profit_usd, status, strategy, arbitrage_type
# DataParser maps: timestamp -> entry_time/exit_time, profit_usd -> pnl_usd, profit_pct -> pnl_pct
# Not in CSV: strategy_version, parameters used, exit_reason, market context (volatility, liquidity, time of day)
# We derive: time_of_day, hour_of_day, volatility_proxy (from profit_pct spread), liquidity_bucket (N/A or derived if we add it later)


def enrich_trades_for_analysis(trades: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Add derived context to trades for diagnostics. Does not mutate originals.

    Derived fields (all labeled in _derived_fields):
    - time_of_day: "morning" | "afternoon" | "evening" | "night"
    - hour_of_day: 0-23
    - volatility_proxy: "low" | "medium" | "high" (from |pnl_pct| heuristic)
    - exit_reason: "inferred_from_pnl" (target/stop/breakeven) or "unknown"
    - _derived_fields: list of keys that were inferred, not from log

    Missing and left as absent or "unknown":
    - strategy_version (not in logs)
    - parameters used (not in logs)
    - market liquidity/volatility at trade time (not in logs; we use proxy from pnl_pct)
    """
    if not trades:
        return []

    result = []
    for t in list(trades):
        row = dict(t)
        derived = []

        # entry_time / timestamp
        ts_str = row.get("entry_time") or row.get("timestamp") or ""
        try:
            if "T" in ts_str:
                dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            else:
                dt = datetime.strptime(ts_str[:19], "%Y-%m-%d %H:%M:%S")
        except (ValueError, TypeError):
            dt = None

        if dt:
            hour = dt.hour
            row["hour_of_day"] = hour
            derived.append("hour_of_day")
            if 6 <= hour < 12:
                row["time_of_day"] = "morning"
            elif 12 <= hour < 18:
                row["time_of_day"] = "afternoon"
            elif 18 <= hour < 24:
                row["time_of_day"] = "evening"
            else:
                row["time_of_day"] = "night"
            derived.append("time_of_day")
        else:
            row["hour_of_day"] = None
            row["time_of_day"] = "unknown"
            derived.extend(["hour_of_day", "time_of_day"])

        # volatility_proxy: use |pnl_pct| as proxy (higher absolute % -> higher volatility environment)
        pnl_pct = float(row.get("pnl_pct") or row.get("profit_pct") or 0)
        abs_pct = abs(pnl_pct)
        if abs_pct < 2.0:
            row["volatility_proxy"] = "low"
        elif abs_pct < 6.0:
            row["volatility_proxy"] = "medium"
        else:
            row["volatility_proxy"] = "high"
        derived.append("volatility_proxy")

        # exit_reason: inferred from P&L only (we don't have target/stop/timeout in CSV)
        pnl_usd = float(row.get("pnl_usd") or row.get("profit_usd") or 0)
        if pnl_usd > 0:
            row["exit_reason"] = "inferred_target_or_profit"
        elif pnl_usd < 0:
            row["exit_reason"] = "inferred_stop_or_loss"
        else:
            row["exit_reason"] = "inferred_breakeven"
        derived.append("exit_reason")

        row["_derived_fields"] = derived
        result.append(row)

    return result


def get_trade_context_audit() -> Dict[str, Any]:
    """
    Return an audit of what trade context is available vs desired for post-mortem.
    Used by diagnostics to know which dimensions are reliable vs derived.
    """
    return {
        "available_from_logs": [
            "timestamp",
            "market",
            "yes_price",
            "no_price",
            "sum",
            "profit_pct",
            "profit_usd",
            "status",
            "strategy",
            "arbitrage_type",
        ],
        "derived_in_analysis": [
            "time_of_day",
            "hour_of_day",
            "volatility_proxy",
            "exit_reason",
        ],
        "not_available": [
            "strategy_version",
            "parameters_used",
            "entry_conditions_detail",
            "exit_reason_exact",
            "market_volatility_at_trade",
            "market_liquidity_at_trade",
        ],
        "note": "exit_reason is inferred from P&L only; volatility/liquidity are proxy from profit_pct.",
    }
