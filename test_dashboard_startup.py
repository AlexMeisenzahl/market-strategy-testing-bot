#!/usr/bin/env python3
"""
Comprehensive test for dashboard startup after import fixes.

This validates that all the import inconsistencies have been fixed.
"""

import sys
from pathlib import Path
import subprocess

# Add project root
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))


def test_scenario_1():
    """Test: Import dashboard.app from project root"""
    print("Scenario 1: Import dashboard.app from project root")
    try:
        # Clean slate
        for module in list(sys.modules.keys()):
            if "dashboard" in module or "services" in module:
                del sys.modules[module]

        from dashboard.app import app

        print("  ✅ Successfully imported dashboard.app")
        print("  ✅ Flask app created")
        return True
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        return False


def test_scenario_2():
    """Test: Import all services independently"""
    print("\nScenario 2: Import services independently")
    services = [
        "services.strategy_analytics",
        "services.market_analytics",
        "services.time_analytics",
        "services.risk_metrics",
    ]

    all_ok = True
    for service in services:
        try:
            __import__(service)
            print(f"  ✅ {service}")
        except Exception as e:
            print(f"  ❌ {service}: {e}")
            all_ok = False

    return all_ok


def test_scenario_3():
    """Test: Import routes independently"""
    print("\nScenario 3: Import routes independently")
    routes = [
        "dashboard.routes.emergency",
        "dashboard.routes.leaderboard",
        "dashboard.routes.config_api",
    ]

    all_ok = True
    for route in routes:
        try:
            # Clear previous imports
            if route in sys.modules:
                del sys.modules[route]
            __import__(route)
            print(f"  ✅ {route}")
        except Exception as e:
            print(f"  ❌ {route}: {e}")
            all_ok = False

    return all_ok


def test_scenario_4():
    """Test: start_dashboard.py functions work"""
    print("\nScenario 4: start_dashboard.py can import dashboard.app")
    try:
        # This simulates what start_dashboard.py does
        from dashboard.app import app

        print("  ✅ start_dashboard.py can import dashboard.app")
        return True
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        return False


def main():
    print("=" * 70)
    print("Dashboard Startup Test - After Import Fixes")
    print("=" * 70)

    results = []
    results.append(test_scenario_1())
    results.append(test_scenario_2())
    results.append(test_scenario_3())
    results.append(test_scenario_4())

    print("\n" + "=" * 70)
    if all(results):
        print("✅ ALL TESTS PASSED - Dashboard is ready to start!")
        print("=" * 70)
        print("\nYou can now run: python3 start_dashboard.py")
        return 0
    else:
        print("❌ SOME TESTS FAILED - See errors above")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    sys.exit(main())
