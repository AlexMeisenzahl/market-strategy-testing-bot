#!/usr/bin/env python3
"""
Test script for PR #52 Final Integration

Tests that all the integration points are working correctly:
1. SimpleTelegramBot class exists and has correct methods
2. Alert manager integration
3. Settings manager integration
4. Dashboard API endpoints exist
5. Template JavaScript functions exist
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))


def test_telegram_bot_class():
    """Test SimpleTelegramBot class is defined"""
    print("Testing SimpleTelegramBot class...")
    
    with open('run_bot.py', 'r') as f:
        content = f.read()
        
    assert 'class SimpleTelegramBot:' in content, "SimpleTelegramBot class not found"
    assert 'def send_message(self, text: str)' in content, "send_message method not found"
    assert 'def test_connection(self)' in content, "test_connection method not found"
    
    print("✅ SimpleTelegramBot class is properly defined")


def test_telegram_integration_in_run_bot():
    """Test telegram bot is initialized in run_bot.py"""
    print("\nTesting telegram integration in run_bot.py...")
    
    with open('run_bot.py', 'r') as f:
        content = f.read()
    
    assert 'self.telegram_bot = SimpleTelegramBot' in content, "Telegram bot not initialized"
    assert 'telegram_bot.send_message' in content, "Telegram send_message not called"
    assert "os.getenv('TELEGRAM_BOT_TOKEN'" in content, "Environment variable not checked"
    
    print("✅ Telegram bot properly integrated")


def test_alert_integration():
    """Test alert manager integration"""
    print("\nTesting alert manager integration...")
    
    with open('run_bot.py', 'r') as f:
        content = f.read()
    
    assert 'from services.alert_manager import alert_manager' in content, "Alert manager not imported"
    assert 'alert_manager.check_alerts' in content, "Alert checking not integrated"
    
    print("✅ Alert manager properly integrated")


def test_settings_integration():
    """Test settings manager integration"""
    print("\nTesting settings manager integration...")
    
    with open('run_bot.py', 'r') as f:
        content = f.read()
    
    assert 'from services.settings_manager import get_settings_manager' in content, "Settings manager not imported"
    assert 'self.settings_manager = get_settings_manager' in content, "Settings manager not initialized"
    assert 'self.cycle_interval = self.settings_manager.get_setting' in content, "Cycle interval not configured"
    
    print("✅ Settings manager properly integrated")


def test_dashboard_api_endpoints():
    """Test dashboard API endpoints exist"""
    print("\nTesting dashboard API endpoints...")
    
    with open('dashboard/app.py', 'r') as f:
        content = f.read()
    
    required_endpoints = [
        ('/api/alerts/config', 'GET'),
        ('/api/alerts/config', 'POST'),
        ('/api/alerts/test', 'POST'),
        ('/api/settings', 'GET'),
        ('/api/settings', 'POST'),
        ('/api/settings/reset', 'POST'),
        ('/api/keys/test', 'POST'),
        ('/api/analytics/performance', 'GET'),
        ('/api/strategies/<name>/start', 'POST'),
        ('/api/strategies/<name>/stop', 'POST'),
    ]
    
    for path, method in required_endpoints:
        # Check if endpoint is defined
        assert path in content, f"Endpoint {method} {path} not found"
    
    print(f"✅ All {len(required_endpoints)} dashboard API endpoints defined")


def test_template_javascript():
    """Test JavaScript functions in templates"""
    print("\nTesting template JavaScript functions...")
    
    # Check alerts.html
    with open('dashboard/templates/alerts.html', 'r') as f:
        alerts_content = f.read()
    
    assert 'function testAlert()' in alerts_content, "testAlert() function not found in alerts.html"
    assert '/api/alerts/test' in alerts_content, "testAlert() doesn't call correct endpoint"
    
    # Check api_keys.html
    with open('dashboard/templates/api_keys.html', 'r') as f:
        api_keys_content = f.read()
    
    assert 'function testKey(service)' in api_keys_content, "testKey() function not found in api_keys.html"
    assert '/api/keys/test' in api_keys_content, "testKey() doesn't call correct endpoint"
    
    print("✅ Template JavaScript functions properly added")


def test_error_handling():
    """Test proper error handling in endpoints"""
    print("\nTesting error handling...")
    
    with open('dashboard/app.py', 'r') as f:
        content = f.read()
    
    # Check strategy control endpoints exist and handle not implemented case
    assert 'def start_strategy(name):' in content, "start_strategy endpoint not found"
    assert 'def stop_strategy(name):' in content, "stop_strategy endpoint not found"
    
    # Find the new strategy control section (after STRATEGY CONTROL API ENDPOINTS comment)
    marker = '# STRATEGY CONTROL API ENDPOINTS'
    if marker in content:
        # Find all occurrences
        idx = content.find(marker)
        # Look for the last occurrence
        while True:
            next_idx = content.find(marker, idx + 1)
            if next_idx == -1:
                break
            idx = next_idx
        
        # Get section from this marker to next major section or end
        strategy_section = content[idx:idx+2000]  # Look at next 2000 chars
        
        # Look for 501 status code in this section
        assert '501' in strategy_section, "Strategy control should return 501 status"
    else:
        # Fallback: just check if 501 appears after def start_strategy
        start_idx = content.find('def start_strategy(name):')
        if start_idx > 0:
            section = content[start_idx:start_idx+500]
            assert '501' in section, "Strategy control should return 501 status"
    
    # Check error responses are properly sanitized
    assert 'Internal server error' in content, "Generic error messages not used"
    
    print("✅ Error handling properly implemented")


def main():
    """Run all tests"""
    print("=" * 60)
    print("PR #52 Integration Tests")
    print("=" * 60)
    
    try:
        test_telegram_bot_class()
        test_telegram_integration_in_run_bot()
        test_alert_integration()
        test_settings_integration()
        test_dashboard_api_endpoints()
        test_template_javascript()
        test_error_handling()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        return 0
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
