"""
Market Strategy Bot - Canonical package for the trading bot system.

This package provides:
- run_engine: Start the 24/7 strategy execution engine
- run_dashboard: Start the Flask web dashboard
- run_tui: Start the read-only terminal UI
- system_check: Validate system readiness

Use the CLI for convenience:
    msb run-engine
    msb run-dashboard
    msb run-tui
    msb system-check
"""

from pathlib import Path

# Project root: parent of this package
PROJECT_ROOT = Path(__file__).resolve().parent.parent

__version__ = "1.0.0"
__all__ = ["PROJECT_ROOT", "run_engine", "run_dashboard", "run_tui", "system_check"]


def run_engine() -> None:
    """Run the trading engine (main bot loop)."""
    from market_strategy_bot.runner import main
    main()


def run_dashboard(host: str = "0.0.0.0", port: int = 5000) -> None:
    """Run the Flask dashboard."""
    from market_strategy_bot.dashboard_app import create_app
    app = create_app()
    app.run(host=host, port=port, debug=False)


def run_tui() -> None:
    """Run the read-only TUI monitor."""
    from market_strategy_bot.tui import main as tui_main
    tui_main()


def system_check() -> int:
    """Run system readiness checks. Returns 0 on success, 1 on failure."""
    from market_strategy_bot.system_check import run_checks
    return run_checks()
