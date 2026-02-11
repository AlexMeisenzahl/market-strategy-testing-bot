"""
Phase 8C: Strategy Suggestion Generator (read-only, safe).

Produces ranked, explainable improvement suggestions. Suggestions are
recommendations only; never code patches, never file writes, never auto-apply.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
import math

from analysis.diagnostics import StrategyDiagnosticsEngine
from analysis.trade_context import enrich_trades_for_analysis


# Minimum sample sizes for generating suggestions
MIN_SAMPLE_FOR_SUGGESTION = 20
MIN_SAMPLE_FOR_REGIME_SUGGESTION = 30


def _chi_square_p_value(observed_win_a: int, total_a: int, observed_win_b: int, total_b: int) -> float:
    """Approximate p-value for difference in win rates (two proportions). Simple chi-square."""
    if total_a < 1 or total_b < 1:
        return 1.0
    p1 = observed_win_a / total_a
    p2 = observed_win_b / total_b
    p_pool = (observed_win_a + observed_win_b) / (total_a + total_b)
    if p_pool <= 0 or p_pool >= 1:
        return 1.0
    se = math.sqrt(p_pool * (1 - p_pool) * (1 / total_a + 1 / total_b))
    if se <= 0:
        return 1.0
    z = (p1 - p2) / se
    # Two-tailed normal approx
    try:
        from math import erfc
        p = 2 * (1 - 0.5 * (1 + math.erf(z / math.sqrt(2))))
        return max(0.0, min(1.0, p))
    except Exception:
        return 0.5


class SuggestionGenerator:
    """
    Generates ranked suggestions from diagnostics. Read-only; never modifies strategy or config.
    """

    def __init__(self, data_parser):
        self.data_parser = data_parser
        self.diagnostics_engine = StrategyDiagnosticsEngine(data_parser)

    def run(
        self,
        strategy_name: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Run diagnostics and generate suggestions. Returns list of suggestion objects.
        No trades -> no suggestions. Small sample -> low confidence / warnings.
        Contradictory data -> no recommendation for that dimension.
        """
        diagnostics = self.diagnostics_engine.run(strategy_name)
        trades_data = self.data_parser.get_trades(strategy=strategy_name, per_page=10000)
        trades = trades_data.get("trades") or []
        if not trades:
            return []

        enriched = enrich_trades_for_analysis(trades)
        strategy = strategy_name or diagnostics.get("strategy", "all")
        suggestions = []

        # 1) Low edge (profit_pct) underperforms in high volatility
        by_vol = diagnostics.get("performance", {}).get("win_rate_by_volatility") or {}
        if len(enriched) >= MIN_SAMPLE_FOR_REGIME_SUGGESTION and by_vol:
            high_vol_trades = [t for t in enriched if t.get("volatility_proxy") == "high"]
            low_edge_trades = [t for t in enriched if abs(float(t.get("pnl_pct") or t.get("profit_pct") or 0)) < 1.5]
            high_vol_low_edge = [t for t in enriched if t.get("volatility_proxy") == "high" and abs(float(t.get("pnl_pct") or t.get("profit_pct") or 0)) < 1.5]
            if len(high_vol_low_edge) >= 10 and len(high_vol_trades) >= 15:
                wr_low_edge_high_vol = sum(1 for t in high_vol_low_edge if (float(t.get("pnl_usd") or t.get("profit_usd") or 0) > 0)) / len(high_vol_low_edge)
                wr_rest = []
                for t in enriched:
                    if t not in high_vol_low_edge:
                        wr_rest.append(1 if float(t.get("pnl_usd") or t.get("profit_usd") or 0) > 0 else 0)
                wr_rest_rate = sum(wr_rest) / len(wr_rest) if wr_rest else 0
                if wr_rest_rate > 0 and wr_low_edge_high_vol < wr_rest_rate - 0.1:
                    wins_l = sum(1 for t in high_vol_low_edge if float(t.get("pnl_usd") or t.get("profit_usd") or 0) > 0)
                    wins_r = sum(wr_rest)
                    p_val = _chi_square_p_value(wins_l, len(high_vol_low_edge), int(wins_r), len(wr_rest))
                    confidence = max(0.3, min(0.95, 1.0 - p_val))
                    suggestions.append({
                        "strategy": strategy,
                        "issue_detected": "Low edge trades underperform in high volatility",
                        "suggested_change": "Consider increasing minimum edge (e.g. min profit %) during high-volatility regimes, or reducing size for small-edge trades in those regimes",
                        "confidence": round(confidence, 2),
                        "evidence": {
                            "sample_size": len(high_vol_low_edge),
                            "win_rate_before": round(wr_low_edge_high_vol, 2),
                            "win_rate_after_threshold": round(wr_rest_rate, 2),
                            "p_value": round(p_val, 4),
                        },
                        "risk": "May reduce trade frequency in high volatility",
                        "validation_required": [
                            "Backtest with higher min edge in high-vol regime",
                            "Paper run for ≥ 100 trades before any change",
                        ],
                    })

        # 2) Time-of-day underperformance
        by_tod = diagnostics.get("performance", {}).get("win_rate_by_time_of_day") or {}
        if len(enriched) >= MIN_SAMPLE_FOR_REGIME_SUGGESTION and len(by_tod) >= 2:
            worst_tod = min(by_tod.items(), key=lambda x: x[1])
            best_tod = max(by_tod.items(), key=lambda x: x[1])
            if worst_tod[1] < best_tod[1] - 0.15:
                count_worst = len([t for t in enriched if t.get("time_of_day") == worst_tod[0]])
                if count_worst >= 15:
                    suggestions.append({
                        "strategy": strategy,
                        "issue_detected": f"Win rate is lower during '{worst_tod[0]}' than other times",
                        "suggested_change": f"Consider reducing size or skipping trades during {worst_tod[0]} until more data confirms, or review strategy logic for that window",
                        "confidence": 0.65,
                        "evidence": {
                            "sample_size": count_worst,
                            "win_rate_before": round(worst_tod[1], 2),
                            "win_rate_after_threshold": round(best_tod[1], 2),
                            "p_value": None,
                        },
                        "risk": "May reduce opportunities in that time window",
                        "validation_required": [
                            "Backtest with time filter",
                            "Paper run for ≥ 100 trades",
                        ],
                    })

        # 3) Consecutive loss streaks
        failure = diagnostics.get("failure_analysis") or {}
        max_streak = failure.get("max_consecutive_losses", 0)
        if len(enriched) >= MIN_SAMPLE_FOR_SUGGESTION and max_streak >= 4:
            suggestions.append({
                "strategy": strategy,
                "issue_detected": f"Observed consecutive losing streak of {max_streak} trades",
                "suggested_change": "Consider adding or tightening a daily loss limit or max consecutive loss rule to reduce drawdown severity (no automatic change; review risk parameters manually)",
                "confidence": 0.6,
                "evidence": {
                    "sample_size": len(enriched),
                    "max_consecutive_losses": max_streak,
                    "win_rate_overall": diagnostics.get("performance", {}).get("win_rate_overall"),
                },
                "risk": "Tighter limits may cap upside in recovering periods",
                "validation_required": [
                    "Backtest with proposed limit",
                    "Paper run to validate",
                ],
            })

        # 4) Low win rate in a profit_pct bucket (single worst bucket with enough sample)
        by_param = diagnostics.get("performance", {}).get("win_rate_by_param_range") or {}
        if len(enriched) >= MIN_SAMPLE_FOR_SUGGESTION and by_param:
            def _count_in_bucket(bucket: str) -> int:
                pct_vals = [float(t.get("pnl_pct") or t.get("profit_pct") or 0) for t in enriched]
                if bucket == "0-1%":
                    return sum(1 for p in pct_vals if 0 <= p < 1)
                if bucket == "1-3%":
                    return sum(1 for p in pct_vals if 1 <= p < 3)
                if bucket == "3-6%":
                    return sum(1 for p in pct_vals if 3 <= p < 6)
                if bucket == "6%+":
                    return sum(1 for p in pct_vals if p >= 6)
                return 0
            candidates = [(b, wr) for b, wr in by_param.items() if b != "negative" and _count_in_bucket(b) >= 20 and wr < 0.45]
            if candidates:
                bucket, wr = min(candidates, key=lambda x: x[1])
                count_b = _count_in_bucket(bucket)
                suggestions.append({
                    "strategy": strategy,
                    "issue_detected": f"Win rate in edge bucket '{bucket}' is low ({wr:.0%})",
                    "suggested_change": f"Consider raising minimum edge threshold to avoid the {bucket} bucket, or reduce position size for that range (validate with backtest first)",
                    "confidence": 0.55,
                    "evidence": {
                        "sample_size": count_b,
                        "win_rate_before": round(wr, 2),
                        "win_rate_after_threshold": None,
                        "p_value": None,
                    },
                    "risk": "May reduce trade count",
                    "validation_required": [
                        "Backtest with new threshold",
                        "Paper run for ≥ 100 trades",
                    ],
                })

        # Rank: by confidence then by impact (sample size)
        suggestions.sort(key=lambda s: (s["confidence"], s["evidence"].get("sample_size") or 0), reverse=True)

        return suggestions
