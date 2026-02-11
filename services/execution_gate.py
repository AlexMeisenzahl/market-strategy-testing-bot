"""
Execution Gate - Single canonical check before any trade may execute.

Phase 7A: No trade can execute when the system is paused, killed, or not paper-only.
This module is the ONLY place that defines "may we execute a trade?".
All execution paths MUST call may_execute_trade() before executing.

Canonical kill switch: config kill_switch (YAML) OR emergency kill switch (DB).
Pause: state/control.json "pause": true (temporary, resumable).
"""

from pathlib import Path
from typing import Dict, Any, Tuple
import json

# Lazy import to avoid circular deps and allow gate to be used before DB init
def _emergency_kill_active() -> bool:
    """True if emergency kill switch is active. Deny on error (fail-safe)."""
    try:
        from services.emergency_kill_switch import kill_switch
        return kill_switch.is_active()
    except Exception:
        return True  # Assume active on error so we do not execute


def _is_paused(control_path: Path) -> bool:
    """True if engine is paused via state/control.json. False on missing/invalid (fail-open for pause)."""
    try:
        if not control_path.exists():
            return False
        with open(control_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict) and "pause" in data:
            return bool(data["pause"])
        return False
    except (json.JSONDecodeError, OSError, TypeError):
        return False


def may_execute_trade(
    config: Dict[str, Any],
    control_path: Path = None,
) -> Tuple[bool, str]:
    """
    Canonical execution gate. Call before every trade execution path.

    Returns:
        (True, "") if execution is allowed.
        (False, reason) if execution must not proceed (paused, killed, or not paper-only).

    Checks (all must pass):
        1. paper_trading must be True (no live trading).
        2. config kill_switch must not be True.
        3. Emergency kill switch (DB) must not be active.
        4. Engine must not be paused (state/control.json).
    """
    if config is None:
        return False, "execution_gate: no config"

    # 1. Paper trading only
    if not config.get("paper_trading", True):
        return False, "execution_gate: paper_trading is disabled"

    # 2. Config kill switch (YAML)
    if config.get("kill_switch", False):
        return False, "execution_gate: config kill_switch is active"

    # 3. Emergency kill switch (DB)
    if _emergency_kill_active():
        return False, "execution_gate: emergency kill switch is active"

    # 4. Paused (control.json)
    if control_path is None:
        control_path = Path(__file__).resolve().parent.parent / "state" / "control.json"
    if _is_paused(control_path):
        return False, "execution_gate: engine is paused"

    return True, ""


def get_gate_status(
    config: Dict[str, Any],
    control_path: Path = None,
) -> Dict[str, Any]:
    """
    Read-only status for dashboard display. Does not execute anything.
    Returns dict with allowed, reason, and per-check flags for UI.
    """
    if control_path is None:
        control_path = Path(__file__).resolve().parent.parent / "state" / "control.json"
    paper_trading = bool(config.get("paper_trading", True) if config else True)
    kill_switch = bool(config.get("kill_switch", False) if config else False)
    emergency_kill = _emergency_kill_active()
    paused = _is_paused(control_path)

    allowed, reason = may_execute_trade(config, control_path)
    return {
        "allowed": allowed,
        "reason": reason or ("OK" if allowed else "Unknown"),
        "paper_trading": paper_trading,
        "kill_switch": kill_switch,
        "emergency_kill": emergency_kill,
        "paused": paused,
    }
