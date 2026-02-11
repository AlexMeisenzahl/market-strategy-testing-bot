"""
Phase 5 — Overfitting guard.

If out-of-sample Sharpe drops more than configurable threshold from in-sample,
flag as unstable. Add robustness score.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class OverfittingGuardResult:
    """Result of overfitting check and robustness score."""

    is_stable: bool = True
    in_sample_sharpe: float = 0.0
    out_of_sample_sharpe: float = 0.0
    sharpe_drop: float = 0.0
    threshold: float = 0.5
    flagged_reason: Optional[str] = None
    robustness_score: float = 0.0  # 0-100; higher = more robust

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_stable": self.is_stable,
            "in_sample_sharpe": self.in_sample_sharpe,
            "out_of_sample_sharpe": self.out_of_sample_sharpe,
            "sharpe_drop": self.sharpe_drop,
            "threshold": self.threshold,
            "flagged_reason": self.flagged_reason,
            "robustness_score": self.robustness_score,
        }


def check_overfitting(
    in_sample_sharpe: float,
    out_of_sample_sharpe: float,
    oos_sharpe_drop_threshold: float = 0.5,
    # Optional: Monte Carlo and walk-forward signals
    monte_carlo_unstable: bool = False,
    oos_trades_count: int = 0,
) -> OverfittingGuardResult:
    """
    Flag if OOS Sharpe drops more than threshold from IS.
    Compute robustness score from IS/OOS Sharpe and stability flags.
    """
    sharpe_drop = in_sample_sharpe - out_of_sample_sharpe
    if sharpe_drop < 0:
        sharpe_drop = 0.0  # OOS better than IS is not overfitting
    is_stable = True
    reason: Optional[str] = None
    if sharpe_drop > oos_sharpe_drop_threshold:
        is_stable = False
        reason = f"OOS Sharpe dropped {sharpe_drop:.2f} from IS (threshold {oos_sharpe_drop_threshold})"
    if monte_carlo_unstable:
        is_stable = False
        reason = (reason or "") + "; Monte Carlo flagged unstable"
    # Robustness score: blend of OOS Sharpe (positive is good) and stability
    # Scale OOS Sharpe to 0-50 (e.g. Sharpe 2 -> 50), then add 50 if stable
    oos_component = min(50.0, max(0.0, (out_of_sample_sharpe + 1.0) * 25.0))  # -1 -> 0, 1 -> 50
    stability_component = 50.0 if is_stable else 0.0
    robustness_score = min(100.0, oos_component + stability_component)
    # Penalize if very few OOS trades
    if oos_trades_count > 0 and oos_trades_count < 20:
        robustness_score *= 0.8
    return OverfittingGuardResult(
        is_stable=is_stable,
        in_sample_sharpe=in_sample_sharpe,
        out_of_sample_sharpe=out_of_sample_sharpe,
        sharpe_drop=sharpe_drop,
        threshold=oos_sharpe_drop_threshold,
        flagged_reason=reason,
        robustness_score=round(robustness_score, 2),
    )
