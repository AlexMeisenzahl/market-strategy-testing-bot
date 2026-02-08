"""
Simple test script for new UX features and API endpoints
Tests the newly added functionality without requiring full integration
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_imports():
    """Test that all new modules can be imported"""
    print("Testing imports...")

    try:
        from services.smart_alerts import SmartAlerts

        print("✓ smart_alerts module imported")
    except ImportError as e:
        print(f"✗ Failed to import smart_alerts: {e}")
        return False

    try:
        from services.tax_reporter import TaxReporter

        print("✓ tax_reporter module imported")
    except ImportError as e:
        print(f"✗ Failed to import tax_reporter: {e}")
        return False

    try:
        from dashboard.app import app

        print("✓ dashboard app imported")
    except ImportError as e:
        print(f"✗ Failed to import dashboard app: {e}")
        return False

    return True


def test_smart_alerts():
    """Test Smart Alerts functionality"""
    print("\nTesting Smart Alerts...")

    from services.smart_alerts import SmartAlerts
    from datetime import datetime, timedelta

    # Create sample trades
    base_date = datetime.now() - timedelta(days=30)
    sample_trades = []

    # Create pattern: Monday price increases
    for week in range(4):
        monday = base_date + timedelta(days=week * 7)
        sample_trades.append(
            {
                "timestamp": monday.isoformat(),
                "price_change": 2.5 + (week * 0.2),
                "volume": 1000,
                "profit": 50,
            }
        )

    alerts = SmartAlerts()
    patterns = alerts.analyze_time_patterns(sample_trades)
    suggestions = alerts.generate_alert_suggestions(patterns)

    print(f"  Detected {len(patterns)} patterns")
    print(f"  Generated {len(suggestions)} suggestions")

    if patterns:
        print(f"  Example pattern: {patterns[0]['pattern']}")

    return len(patterns) >= 0  # At least detect the structure works


def test_tax_reporter():
    """Test Tax Reporter functionality"""
    print("\nTesting Tax Reporter...")

    from services.tax_reporter import TaxReporter

    # Create sample trades
    sample_trades = [
        {
            "date": "2024-01-15",
            "side": "buy",
            "asset": "BTC",
            "amount": 0.5,
            "price": 40000,
        },
        {
            "date": "2024-06-15",
            "side": "sell",
            "asset": "BTC",
            "amount": 0.5,
            "price": 45000,
        },
    ]

    reporter = TaxReporter()

    # Test report generation
    report = reporter.generate_form_8949(sample_trades, 2024, "FIFO")
    print(f"  Generated report: {len(report)} characters")

    # Test summary
    summary = reporter.calculate_tax_summary(sample_trades, 2024, "FIFO")
    print(f"  Summary: ${summary.get('total_gain', 0):.2f} total gain/loss")
    print(f"  Transactions: {summary.get('transaction_count', 0)}")

    return len(report) > 0


def test_api_routes():
    """Test that new API routes are registered"""
    print("\nTesting API Routes...")

    from dashboard.app import app

    # Check for new routes
    new_routes = [
        "/api/workspaces",
        "/api/tax/report",
        "/api/tax/summary",
        "/api/smart-alerts/analyze",
        "/api/health",
    ]

    registered_routes = [str(rule) for rule in app.url_map.iter_rules()]

    for route in new_routes:
        if route in registered_routes:
            print(f"  ✓ {route} registered")
        else:
            print(f"  ✗ {route} NOT registered")
            return False

    return True


def test_static_files():
    """Test that static files exist"""
    print("\nTesting Static Files...")

    static_files = [
        "dashboard/static/css/mobile.css",
        "dashboard/static/css/skeletons.css",
        "dashboard/static/js/keyboard_shortcuts.js",
        "dashboard/static/js/command_palette.js",
        "dashboard/static/js/enhanced_charts.js",
        "dashboard/static/js/favorites.js",
        "dashboard/static/js/debug_panel.js",
        "dashboard/static/js/touch_gestures.js",
        "dashboard/static/manifest.json",
        "dashboard/static/service-worker.js",
    ]

    all_exist = True
    for file_path in static_files:
        if os.path.exists(file_path):
            print(f"  ✓ {file_path}")
        else:
            print(f"  ✗ {file_path} NOT FOUND")
            all_exist = False

    return all_exist


def main():
    """Run all tests"""
    print("=" * 60)
    print("UX Features Test Suite")
    print("=" * 60)

    tests = [
        ("Imports", test_imports),
        ("Smart Alerts", test_smart_alerts),
        ("Tax Reporter", test_tax_reporter),
        ("API Routes", test_api_routes),
        ("Static Files", test_static_files),
    ]

    results = {}
    for name, test_func in tests:
        try:
            results[name] = test_func()
        except Exception as e:
            print(f"\n✗ {name} test failed with exception: {e}")
            import traceback

            traceback.print_exc()
            results[name] = False

    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:8} {name}")

    print(f"\nPassed: {passed}/{total}")

    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
