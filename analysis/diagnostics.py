"""
Phase 8B: Strategy Diagnostics Engine (read-only).

Computes performance breakdowns, risk-adjusted metrics, failure analysis,
and simple regime detection. No ML; all heuristics are explainable.
Consumes only trade data (and enriched context from Phase 8A).
"""

from collections import Counter, defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
import math

from analysis.trade_context import enrich_trades_for_analysis, get_trade_context_audit


def _win_rate(trades: List[Dict[str, Any]]) -> float:
    if not trades:
        return 0.0
    wins = sum(1 for t in trades if float(t.get("pnl_usd") or t.get("profit_usd") or 0) > 0)
    return wins / len(trades)


def _pnl_list(trades: List[Dict[str, Any]]) -> List[float]:
    return [float(t.get("pnl_usd") or t.get("profit_usd") or 0) for t in trades]


def _sharpe_if_possible(returns: List[float], risk_free: float = 0.0) -> Optional[float]:
    if len(returns) < 2:
        return None
    mean_r = sum(returns) / len(returns)
    variance = sum((x - mean_r) ** 2 for x in returns) / (len(returns) - 1)
    std = math.sqrt(variance)
    if std <= 0:
        return None
    return (mean_r - risk_free) / std


def _max_drawdown(cumulative: List[float]) -> Tuple[float, float]:
    if not cumulative:
        return 0.0, 0.0
    peak = cumulative[0]
    max_dd = 0.0
    for v in cumulative:
        peak = max(peak, v)
        dd = peak - v
        if dd > max_dd:
            max_dd = dd
    peak_at_dd = peak if cumulative else 0
    pct = (max_dd / peak_at_dd * 100) if peak_at_dd else 0
    return max_dd, pct


class StrategyDiagnosticsEngine:
    """
    Read-only diagnostics: performance breakdowns, risk metrics, failure analysis, regime detection.
    """

    def __init__(self, data_parser):
        self.data_parser = data_parser
        self._audit = get_trade_context_audit()

    def run(self, strategy_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Run full diagnostics on trades (optionally filtered by strategy).
        Returns a single dict with diagnostics; does not write any files.
        """
        trades_data = self.data_parser.get_trades(
            strategy=strategy_name,
            per_page=10000,
        )
        trades = trades_data.get("trades") or []
        if not trades:
            return self._empty_diagnostics(strategy_name)

        enriched = enrich_trades_for_analysis(trades)
        pnls = _pnl_list(enriched)
        cumulative = []
        s = 0.0
        for p in pnls:
            s += p
            cumulative.append(s)

        max_dd, max_dd_pct = _max_drawdown(cumulative)
        sharpe = _sharpe_if_possible(pnls)

        # Performance breakdowns: win rate by dimension
        by_param_range = self._win_rate_by_param_ranges(enriched)
        by_volatility = self._win_rate_by_volatility(enriched)
        by_time_of_day = self._win_rate_by_time_of_day(enriched)
        by_arbitrage_type = self._win_rate_by_key(enriched, "arbitrage_type")

        # Tail loss: frequency of losses beyond 1 std
        mean_pnl = sum(pnls) / len(pnls) if pnls else 0
        variance = sum((x - mean_pnl) ** 2 for x in pnls) / (len(pnls) - 1) if len(pnls) > 1 else 0
        std_pnl = math.sqrt(variance) if variance > 0 else 0
        tail_losses = sum(1 for p in pnls if p < mean_pnl - std_pnl) if std_pnl > 0 else 0
        tail_loss_frequency = tail_losses / len(pnls) if pnls else 0

        # Losing trade clusters: consecutive losing streaks
        streaks = self._losing_streaks(pnls)
        max_streak = max(streaks) if streaks else 0

        # Regime detection (simple)
        volatility_regime = self._volatility_regime(enriched)
        trending_vs_mean_reverting = self._trending_vs_mean_reverting(pnls)

        return {
            "strategy": strategy_name or "all",
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "trade_context_audit": self._audit,
            "sample_size": len(enriched),
            "performance": {
                "win_rate_overall": round(_win_rate(enriched), 4),
                "total_pnl": round(sum(pnls), 2),
                "mean_pnl_per_trade": round(mean_pnl, 2),
                "win_rate_by_param_range": by_param_range,
                "win_rate_by_volatility": by_volatility,
                "win_rate_by_time_of_day": by_time_of_day,
                "win_rate_by_arbitrage_type": by_arbitrage_type,
            },
            "risk_adjusted": {
                "sharpe_ratio": round(sharpe, 4) if sharpe is not None else None,
                "max_drawdown_usd": round(max_dd, 2),
                "max_drawdown_pct": round(max_dd_pct, 2),
                "tail_loss_frequency": round(tail_loss_frequency, 4),
            },
            "failure_analysis": {
                "losing_streaks": streaks,
                "max_consecutive_losses": max_streak,
                "conditions_correlated_with_drawdown": self._drawdown_conditions(enriched, cumulative),
            },
            "regime": {
                "volatility_regime": volatility_regime,
                "trending_vs_mean_reverting": trending_vs_mean_reverting,
            },
        }

    def _empty_diagnostics(self, strategy_name: Optional[str]) -> Dict[str, Any]:
        return {
            "strategy": strategy_name or "all",
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "trade_context_audit": self._audit,
            "sample_size": 0,
            "performance": {},
            "risk_adjusted": {},
            "failure_analysis": {},
            "regime": {},
        }

    def _win_rate_by_param_ranges(self, trades: List[Dict[str, Any]]) -> Dict[str, float]:
        """Win rate by profit_pct buckets (edge proxy)."""
        buckets = defaultdict(list)
        for t in trades:
            pct = float(t.get("pnl_pct") or t.get("profit_pct") or 0)
            if pct < 0:
                bucket = "negative"
            elif pct < 1:
                bucket = "0-1%"
            elif pct < 3:
                bucket = "1-3%"
            elif pct < 6:
                bucket = "3-6%"
            else:
                bucket = "6%+"
            buckets[bucket].append(t)
        return {k: round(_win_rate(v), 4) for k, v in buckets.items()}

    def _win_rate_by_volatility(self, trades: List[Dict[str, Any]]) -> Dict[str, float]:
        """Win rate by derived volatility_proxy."""
        by_v = defaultdict(list)
        for t in trades:
            v = t.get("volatility_proxy", "unknown")
            by_v[v].append(t)
        return {k: round(_win_rate(v), 4) for k, v in by_v.items()}

    def _win_rate_by_time_of_day(self, trades: List[Dict[str, Any]]) -> Dict[str, float]:
        """Win rate by time_of_day."""
        by_t = defaultdict(list)
        for t in trades:
            tod = t.get("time_of_day", "unknown")
            by_t[tod].append(t)
        return {k: round(_win_rate(v), 4) for k, v in by_t.items()}

    def _win_rate_by_key(self, trades: List[Dict[str, Any]], key: str) -> Dict[str, float]:
        by_k = defaultdict(list)
        for t in trades:
            k = t.get(key) or "unknown"
            by_k[str(k)].append(t)
        return {k: round(_win_rate(v), 4) for k, v in by_k.items()}

    def _losing_streaks(self, pnls: List[float]) -> List[int]:
        streaks = []
        current = 0
        for p in pnls:
            if p < 0:
                current += 1
            else:
                if current > 0:
                    streaks.append(current)
                current = 0
        if current > 0:
            streaks.append(current)
        return streaks

    def _drawdown_conditions(
        self, trades: List[Dict[str, Any]], cumulative: List[float]
    ) -> List[Dict[str, Any]]:
        """Simple: which conditions appear during drawdown periods (peak-to-trough)."""
        if len(trades) != len(cumulative) or len(cumulative) < 2:
            return []
        peak = cumulative[0]
        peak_idx = 0
        conditions = []
        for i in range(1, len(cumulative)):
            if cumulative[i] >= peak:
                peak = cumulative[i]
                peak_idx = i
            else:
                dd = peak - cumulative[i]
                if dd > 0 and peak_idx < len(trades) and i < len(trades):
                    t = trades[i]
                    conditions.append({
                        "during_drawdown": True,
                        "volatility_proxy": t.get("volatility_proxy"),
                        "time_of_day": t.get("time_of_day"),
                        "strategy": t.get("strategy"),
                    })
        # Aggregate: count (volatility_proxy, time_of_day) during drawdown
        if not conditions:
            return []
        combo = [(c.get("volatility_proxy"), c.get("time_of_day")) for c in conditions]
        counts = Counter(combo)
        return [
            {"volatility_proxy": v, "time_of_day": t, "count": n}
            for (v, t), n in counts.most_common(5)
        ]

    def _volatility_regime(self, trades: List[Dict[str, Any]]) -> str:
        """Simple: majority of trades in which volatility_proxy bucket."""
        if not trades:
            return "unknown"
        v = [t.get("volatility_proxy") for t in trades if t.get("volatility_proxy")]
        if not v:
            return "unknown"
        most = Counter(v).most_common(1)[0][0]
        return most

    def _trending_vs_mean_reverting(self, pnls: List[float]) -> str:
        """Very simple: positive autocorrelation -> trending; negative -> mean reverting."""
        if len(pnls) < 3:
            return "insufficient_data"
        x = pnls[:-1]
        y = pnls[1:]
        n = len(x)
        mx = sum(x) / n
        my = sum(y) / n
        cov = sum((x[i] - mx) * (y[i] - my) for i in range(n))
        varx = sum((a - mx) ** 2 for a in x)
        vary = sum((b - my) ** 2 for b in y)
        if varx <= 0 or vary <= 0:
            return "insufficient_data"
        corr = cov / (math.sqrt(varx) * math.sqrt(vary))
        if corr > 0.1:
            return "trending"
        if corr < -0.1:
            return "mean_reverting"
        return "neutral"

