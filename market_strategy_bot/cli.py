#!/usr/bin/env python3
"""
CLI for Market Strategy Bot.

Commands:
  run-engine     Start the 24/7 strategy execution engine
  run-dashboard  Start the Flask web dashboard
  run-tui        Start the read-only terminal UI
  system-check   Validate system readiness
"""

import sys
from pathlib import Path

# Ensure package is importable
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def _run_engine() -> None:
    from market_strategy_bot.runner import main
    main()


def _run_dashboard() -> None:
    from market_strategy_bot.dashboard_app import create_app
    import os
    app = create_app()
    port = int(os.environ.get("DASHBOARD_PORT", 5000))
    host = os.environ.get("DASHBOARD_HOST", "0.0.0.0")
    app.run(host=host, port=port, debug=False)


def _run_tui() -> None:
    from market_strategy_bot.tui import main
    main()


def _system_check(skip_dashboard: bool = False, skip_cycle: bool = False) -> int:
    from market_strategy_bot.system_check import run_checks
    return run_checks(skip_dashboard=skip_dashboard, skip_cycle=skip_cycle)


def main() -> None:
    """Main CLI entry point."""
    args = sys.argv[1:] if len(sys.argv) > 1 else []

    if not args or args[0] in ("-h", "--help"):
        print(__doc__.strip())
        print()
        print("Usage: msb <command> [options]")
        print("  run-engine     Start the trading engine")
        print("  run-dashboard  Start the web dashboard")
        print("  run-tui        Start the TUI monitor")
        print("  system-check   Run system readiness checks")
        print("    --skip-dashboard  Skip dashboard import/routes check")
        print("    --skip-cycle      Skip engine cycle smoke test")
        sys.exit(0 if not args else 0)

    cmd = args[0].lower()

    if cmd == "run-engine":
        _run_engine()
    elif cmd == "run-dashboard":
        _run_dashboard()
    elif cmd == "run-tui":
        _run_tui()
    elif cmd == "system-check":
        skip_dashboard = "--skip-dashboard" in args
        skip_cycle = "--skip-cycle" in args
        sys.exit(_system_check(skip_dashboard=skip_dashboard, skip_cycle=skip_cycle))
    else:
        print(f"Unknown command: {cmd}")
        print("Use: run-engine | run-dashboard | run-tui | system-check")
        sys.exit(1)


if __name__ == "__main__":
    main()
