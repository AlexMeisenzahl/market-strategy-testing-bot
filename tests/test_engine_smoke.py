"""
Smoke tests: engine and dashboard can be imported and (optionally) run one cycle.
Minimal tests for production hardening; full behavior is in system_check and integration tests.
"""

import sys
from pathlib import Path

_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import pytest


def test_engine_imports():
    """Engine and related modules import without error."""
    from engine import ExecutionEngine
    from strategy_manager import StrategyManager

    assert ExecutionEngine is not None
    assert StrategyManager is not None


def test_system_check_module_runs():
    """system_check run_checks can be invoked (skip cycle for speed)."""
    from market_strategy_bot.system_check import run_checks

    # Skip cycle to avoid side effects and slowness in pytest
    code = run_checks(skip_cycle=True, skip_dashboard=False)
    assert code == 0, "system_check should pass with skip_cycle=True"