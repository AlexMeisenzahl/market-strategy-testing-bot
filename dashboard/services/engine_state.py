"""
Engine State Reader - Read-only access to engine state files

Reads state/bot_state.json and logs/activity.json with graceful handling
of missing or partial data. Never raises; returns empty/default values on error.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


def _read_json(path: Path, default: Any) -> Any:
    """Read JSON file. Returns default on missing/invalid."""
    try:
        if not path.exists():
            return default
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError, TypeError):
        return default


class EngineStateReader:
    """
    Read-only reader for engine state.
    Tolerates missing or partial state files.
    """

    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self.state_path = self.base_dir / "state" / "bot_state.json"
        self.activity_path = self.base_dir / "logs" / "activity.json"

    def get_bot_state(self) -> Dict[str, Any]:
        """Read state/bot_state.json. Returns {} on missing/invalid."""
        return _read_json(self.state_path, {})

    def get_activity(self) -> List[Dict[str, Any]]:
        """Read logs/activity.json. Returns [] on missing/invalid."""
        data = _read_json(self.activity_path, [])
        return data if isinstance(data, list) else []

    def has_engine_state(self) -> bool:
        """True if bot_state.json exists and has expected structure."""
        state = self.get_bot_state()
        return isinstance(state, dict) and ("status" in state or "trading" in state)

    def get_overview_from_engine(self) -> Optional[Dict[str, Any]]:
        """
        Build overview stats from engine state.
        Returns None if no valid engine state.
        """
        state = self.get_bot_state()
        if not isinstance(state, dict):
            return None
        trading = state.get("trading", {})
        if not isinstance(trading, dict):
            return None

        balance = float(state.get("balance", 0) or 0)
        paper_profit = float(trading.get("paper_profit", 0) or 0)
        opps = int(trading.get("opportunities_found", 0) or 0)
        trades_count = int(trading.get("trades_executed", 0) or 0)
        positions = state.get("positions", [])
        positions = positions if isinstance(positions, list) else []

        return {
            "total_pnl": paper_profit,
            "pnl_change_pct": 0,
            "win_rate": (100.0 if trades_count > 0 and paper_profit > 0 else 0),
            "active_trades": len([p for p in positions if p.get("quantity", 0)]),
            "today_opportunities": opps,
            "total_trades": trades_count,
            "profit_factor": 0,
            "avg_trade_duration": 0,
            "best_strategy": "N/A",
            "gross_profit": max(0, paper_profit),
            "gross_loss": abs(min(0, paper_profit)),
            "largest_win": 0,
            "largest_loss": 0,
            "avg_win": 0,
            "avg_loss": 0,
            "win_loss_ratio": 0,
            "sharpe_ratio": 0,
            "max_drawdown": 0,
            "max_drawdown_pct": 0,
            "balance": balance,
            "status": state.get("status", "unknown"),
            "last_update": state.get("last_update", ""),
            "source": "engine",
        }

    def get_bot_status_from_engine(self) -> Optional[Dict[str, Any]]:
        """Build bot status from engine state. Returns None if no valid state."""
        state = self.get_bot_state()
        if not isinstance(state, dict) or "status" not in state:
            return None
        status = state.get("status", "unknown")
        runtime = int(state.get("runtime_seconds", 0) or 0)
        if status == "running":
            emoji, text = "🟢", "Running"
        elif status == "paused":
            emoji, text = "🟡", "Paused"
        elif status == "stopped":
            emoji, text = "🔴", "Stopped"
        else:
            emoji, text = "🟡", str(status)
        return {
            "running": status == "running",
            "paused": status == "paused",
            "status_emoji": emoji,
            "status_text": text,
            "uptime": runtime,
            "last_update": state.get("last_update", ""),
            "source": "engine",
        }

    def get_positions_from_engine(self) -> List[Dict[str, Any]]:
        """Get positions from engine state. Returns [] on missing/invalid."""
        state = self.get_bot_state()
        if not isinstance(state, dict):
            return []
        positions = state.get("positions", [])
        return positions if isinstance(positions, list) else []

    def get_portfolio_from_engine(self) -> Optional[Dict[str, Any]]:
        """Build portfolio from engine state. Returns None if no valid state."""
        state = self.get_bot_state()
        if not isinstance(state, dict):
            return None
        balance = float(state.get("balance", 0) or 0)
        positions = state.get("positions", [])
        positions = positions if isinstance(positions, list) else []
        position_value = sum(
            float(p.get("current_value", 0) or p.get("quantity", 0) * p.get("avg_price", 0))
            for p in positions
        )
        return {
            "balance": balance,
            "position_value": position_value,
            "total_value": balance + position_value,
            "positions": positions,
            "source": "engine",
        }
