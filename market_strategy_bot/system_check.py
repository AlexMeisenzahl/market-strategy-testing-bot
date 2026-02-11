"""
System readiness checks for Market Strategy Bot.

Validates:
- Required directories exist (or auto-create)
- Required files exist or auto-create
- Engine imports successfully
- Dashboard imports successfully
- Flask routes register
- Engine runs one cycle without crashing
"""

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def _ensure_dirs() -> bool:
    """Ensure state/ and logs/ exist."""
    state_dir = _ROOT / "state"
    logs_dir = _ROOT / "logs"
    try:
        state_dir.mkdir(exist_ok=True)
        logs_dir.mkdir(exist_ok=True)
        print("[PASS] Required directories exist (state/, logs/)")
        return True
    except OSError as e:
        print(f"[FAIL] Could not create directories: {e}")
        return False


def _check_config() -> bool:
    """Check config file exists."""
    config = _ROOT / "config.yaml"
    example = _ROOT / "config.example.yaml"
    if config.exists():
        print("[PASS] config.yaml exists")
        return True
    if example.exists():
        print("[WARN] config.yaml not found; config.example.yaml exists")
        return True
    print("[FAIL] No config.yaml or config.example.yaml")
    return False


def _check_engine_import() -> bool:
    """Check engine imports."""
    try:
        from engine import ExecutionEngine
        from strategy_manager import StrategyManager
        from run_bot import main
        print("[PASS] Engine imports successfully")
        return True
    except Exception as e:
        print(f"[FAIL] Engine import: {e}")
        return False


def _check_dashboard_import() -> bool:
    """Check dashboard imports."""
    try:
        from dashboard.app import app
        print("[PASS] Dashboard imports successfully")
        return True
    except Exception as e:
        print(f"[FAIL] Dashboard import: {e}")
        return False


def _check_flask_routes() -> bool:
    """Check Flask routes register."""
    try:
        from dashboard.app import app
        rules = list(app.url_map.iter_rules())
        print(f"[PASS] Flask routes registered ({len(rules)} routes)")
        return True
    except Exception as e:
        print(f"[FAIL] Flask routes: {e}")
        return False


def _check_engine_cycle() -> bool:
    """Check engine can run one cycle (smoke test)."""
    try:
        from run_bot import BotRunner
        bot = BotRunner(config_path="config.yaml")
        bot.run_cycle()
        print("[PASS] Engine ran one cycle successfully")
        return True
    except Exception as e:
        print(f"[FAIL] Engine cycle: {e}")
        return False


def run_checks(skip_cycle: bool = False, skip_dashboard: bool = False) -> int:
    """
    Run all system checks.
    Returns 0 on success, 1 on failure.
    skip_cycle: If True, skip the engine cycle test (slower, may have side effects).
    """
    checks = [
        ("Directories", _ensure_dirs),
        ("Config", _check_config),
        ("Engine import", _check_engine_import),
    ]
    if not skip_dashboard:
        checks.extend([
            ("Dashboard import", _check_dashboard_import),
            ("Flask routes", _check_flask_routes),
        ])
    if not skip_cycle:
        checks.append(("Engine cycle", _check_engine_cycle))

    print("=" * 50)
    print("Market Strategy Bot - System Check")
    print("=" * 50)

    passed = 0
    for name, fn in checks:
        try:
            if fn():
                passed += 1
        except Exception as e:
            print(f"[FAIL] {name}: {e}")

    print("=" * 50)
    if passed == len(checks):
        print(f"All {len(checks)} checks passed.")
        return 0
    print(f"{passed}/{len(checks)} checks passed.")
    return 1


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Market Strategy Bot system checks")
    p.add_argument("--skip-cycle", action="store_true", help="Skip engine cycle smoke test")
    p.add_argument("--skip-dashboard", action="store_true", help="Skip dashboard import and routes")
    args = p.parse_args()
    sys.exit(run_checks(skip_cycle=args.skip_cycle, skip_dashboard=args.skip_dashboard))
