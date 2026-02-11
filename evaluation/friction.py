"""
Phase 2 — Realistic friction modeling.

Backtests use configurable:
- Commission rate
- Spread estimate
- Slippage parameter
- Partial fill modeling

Friction is parameterized and applied to trade lists (no change to live engine).
"""

from __future__ import annotations

import copy
import random
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from evaluation.config import FrictionConfig


def _get_pnl(t: Dict[str, Any]) -> float:
    return float(t.get("pnl_usd", t.get("profit", t.get("pnl", 0.0))))


def _get_notional(t: Dict[str, Any]) -> float:
    """Approximate notional for commission/spread (entry notional or from size)."""
    size = t.get("size", t.get("position_size", t.get("quantity", 0.0)))
    if size and float(size) > 0:
        return abs(float(size))
    entry = float(t.get("entry_price", 0.0))
    # Infer from PnL and return if available
    pnl = _get_pnl(t)
    ret_pct = t.get("return_pct", t.get("pnl_pct", 0.0))
    if ret_pct and float(ret_pct) != 0 and pnl != 0:
        notional = abs(pnl) / (abs(float(ret_pct)) / 100.0)
        return notional
    if entry > 0:
        # Guess: notional ~ 2 * |pnl| as rough size
        return max(abs(pnl) * 5.0, 100.0) if pnl != 0 else 100.0
    return 100.0


def apply_friction_to_trades(
    trades: List[Dict[str, Any]],
    config: FrictionConfig,
    seed: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Apply configurable friction to a copy of the trade list.
    Returns new list; does not mutate input.
    - Commission: commission_rate * notional per side (open + close)
    - Spread: spread_bps applied to notional (cost per round-trip)
    - Slippage: slippage_bps applied to notional (cost per side, so 2x for round-trip)
    - Partial fill: with probability partial_fill_rate, scale fill and PnL by [min, max] ratio
    """
    if seed is not None:
        random.seed(seed)
    out: List[Dict[str, Any]] = []
    for t in trades:
        row = copy.deepcopy(t)
        notional = _get_notional(row)
        pnl = _get_pnl(row)

        # Partial fill: sometimes reduce fill and PnL
        fill_ratio = 1.0
        if config.partial_fill_rate > 0 and random.random() < config.partial_fill_rate:
            fill_ratio = random.uniform(
                config.partial_fill_ratio_min,
                config.partial_fill_ratio_max,
            )
        notional_eff = notional * fill_ratio
        pnl_eff = pnl * fill_ratio

        # Commission: open + close = 2 sides
        commission = 2.0 * config.commission_rate * notional_eff
        # Spread: round-trip
        spread_cost = config.spread_pct() * notional_eff
        # Slippage: round-trip (entry + exit)
        slippage_cost = 2.0 * config.slippage_pct() * notional_eff

        new_pnl = pnl_eff - commission - spread_cost - slippage_cost

        # Write back normalized keys
        if "pnl_usd" in row:
            row["pnl_usd"] = round(new_pnl, 4)
        if "profit" in row:
            row["profit"] = round(new_pnl, 4)
        if "pnl" in row:
            row["pnl"] = round(new_pnl, 4)
        row["_friction_commission"] = round(commission, 4)
        row["_friction_spread"] = round(spread_cost, 4)
        row["_friction_slippage"] = round(slippage_cost, 4)
        row["_friction_fill_ratio"] = fill_ratio
        out.append(row)
    return out
