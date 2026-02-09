#!/usr/bin/env python3
"""
Test script to verify import fixes work correctly.

This test ensures that:
1. Dashboard app can be imported without ModuleNotFoundError
2. All service modules can be imported
3. Routes can be imported
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))


def test_dashboard_app_import():
    """Test that dashboard.app can be imported"""
    try:
        from dashboard.app import app

        print("✅ dashboard.app imported successfully")
        return True
    except ModuleNotFoundError as e:
        print(f"❌ Failed to import dashboard.app: {e}")
        return False


def test_service_imports():
    """Test that all service modules can be imported"""
    services = [
        ("services.strategy_analytics", "StrategyAnalytics"),
        ("services.market_analytics", "MarketAnalytics"),
        ("services.time_analytics", "TimeAnalytics"),
        ("services.risk_metrics", "RiskMetrics"),
    ]

    all_passed = True
    for module_name, class_name in services:
        try:
            module = __import__(module_name, fromlist=[class_name])
            cls = getattr(module, class_name)
            print(f"✅ {module_name}.{class_name} imported successfully")
        except Exception as e:
            print(f"❌ Failed to import {module_name}.{class_name}: {e}")
            all_passed = False

    return all_passed


def test_route_imports():
    """Test that route modules can be imported"""
    routes = [
        "dashboard.routes.config_api",
        "dashboard.routes.emergency",
        "dashboard.routes.leaderboard",
    ]

    all_passed = True
    for route in routes:
        try:
            __import__(route)
            print(f"✅ {route} imported successfully")
        except Exception as e:
            print(f"❌ Failed to import {route}: {e}")
            all_passed = False

    return all_passed


def main():
    """Run all tests"""
    print("=" * 70)
    print("Testing Import Fixes")
    print("=" * 70)
    print()

    print("Test 1: Dashboard App Import")
    print("-" * 70)
    test1 = test_dashboard_app_import()
    print()

    print("Test 2: Service Imports")
    print("-" * 70)
    test2 = test_service_imports()
    print()

    print("Test 3: Route Imports")
    print("-" * 70)
    test3 = test_route_imports()
    print()

    print("=" * 70)
    if test1 and test2 and test3:
        print("✅ All import tests passed!")
        print("=" * 70)
        return 0
    else:
        print("❌ Some import tests failed")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    sys.exit(main())
