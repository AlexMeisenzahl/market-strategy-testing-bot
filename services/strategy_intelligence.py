"""
Phase 8: Strategy Intelligence facade (read-only).

This module is the ONLY entry point for Strategy Intelligence from the dashboard.
The execution engine (run_bot.py, main.py, paper_trading_engine, etc.) must NOT
import this module. Removing Phase 8 = remove dashboard routes that call this
and remove this module; execution is unchanged.

SAFETY:
- No automatic changes to strategy, config, or code.
- Reads only: logs/trades.csv, logs/activity.json (via DataParser / EngineStateReader).
- Writes only: optional JSON under analysis/reports/ for export; never strategy or config.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import json

# Lazy import of analysis package so execution path can run without it
def _get_analysis():
    from analysis.trade_context import enrich_trades_for_analysis, get_trade_context_audit
    from analysis.diagnostics import StrategyDiagnosticsEngine
    from analysis.suggestions import SuggestionGenerator
    return enrich_trades_for_analysis, get_trade_context_audit, StrategyDiagnosticsEngine, SuggestionGenerator


# In-memory cache of last run (Phase 8D: storage in memory or JSON)
_last_diagnostics: Dict[str, Any] = {}
_last_suggestions: List[Dict[str, Any]] = []
_last_run_at: Optional[str] = None


def run_analysis(data_parser, strategy_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Run diagnostics and suggestion generation. Batch/periodic or on-demand.
    Does not run inline with execution. Returns { "diagnostics": {...}, "suggestions": [...] }.
    """
    global _last_diagnostics, _last_suggestions, _last_run_at
    (
        _enrich,
        _audit_fn,
        StrategyDiagnosticsEngine,
        SuggestionGenerator,
    ) = _get_analysis()

    engine = StrategyDiagnosticsEngine(data_parser)
    diag = engine.run(strategy_name)
    gen = SuggestionGenerator(data_parser)
    suggestions = gen.run(strategy_name)

    _last_diagnostics = diag
    _last_suggestions = suggestions
    _last_run_at = datetime.utcnow().isoformat() + "Z"

    return {"diagnostics": diag, "suggestions": suggestions, "generated_at": _last_run_at}


def get_cached_diagnostics() -> Dict[str, Any]:
    """Return last run diagnostics (read-only)."""
    return _last_diagnostics


def get_cached_suggestions() -> List[Dict[str, Any]]:
    """Return last run suggestions (read-only)."""
    return list(_last_suggestions)


def get_last_run_at() -> Optional[str]:
    """Return ISO timestamp of last analysis run."""
    return _last_run_at


def export_to_reports_dir(
    base_dir: Path,
    diagnostics: Dict[str, Any],
    suggestions: List[Dict[str, Any]],
) -> Optional[Path]:
    """
    Optionally write diagnostics and suggestions to analysis/reports/ as JSON.
    Does NOT write to strategy code or config. Caller passes data (read-only export).
    Returns path to written file or None if skipped.
    """
    try:
        reports_dir = base_dir / "analysis" / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        path = reports_dir / f"strategy_intelligence_{ts}.json"
        payload = {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "diagnostics": diagnostics,
            "suggestions": suggestions,
            "disclaimer": "Read-only report. No automatic changes. Human review required.",
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        return path
    except Exception:
        return None
