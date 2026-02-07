#!/usr/bin/env python3
"""
Dashboard Validation Test

Tests the key improvements from the dashboard overhaul:
- Health endpoint
- Advanced metrics calculation
- Chart data generation
- Data parser CSV reading
"""

import sys
import time
import requests
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from dashboard.services.data_parser import DataParser
from dashboard.services.analytics import AnalyticsService


def test_data_parser():
    """Test DataParser reads data correctly"""
    print("\n📊 Testing DataParser...")
    
    logs_dir = Path(__file__).parent / 'logs'
    parser = DataParser(logs_dir)
    
    # Test getting trades
    trades = parser.get_all_trades()
    assert len(trades) > 0, "No trades found"
    print(f"  ✅ Found {len(trades)} trades")
    
    # Test getting opportunities
    opportunities = parser.get_all_opportunities()
    assert len(opportunities) > 0, "No opportunities found"
    print(f"  ✅ Found {len(opportunities)} opportunities")
    
    # Test filtered trades
    filtered = parser.get_trades(outcome='win', page=1, per_page=10)
    assert 'trades' in filtered, "Filtered trades missing 'trades' key"
    assert 'total_count' in filtered, "Filtered trades missing 'total_count' key"
    print(f"  ✅ Filtered trades working (found {filtered['total_count']} wins)")
    
    print("  ✅ DataParser tests passed")


def test_analytics_service():
    """Test AnalyticsService calculates metrics correctly"""
    print("\n📈 Testing AnalyticsService...")
    
    logs_dir = Path(__file__).parent / 'logs'
    parser = DataParser(logs_dir)
    analytics = AnalyticsService(parser)
    
    # Test overview stats
    stats = analytics.get_overview_stats()
    
    # Check required metrics exist
    required_metrics = [
        'total_pnl', 'win_rate', 'sharpe_ratio', 
        'max_drawdown', 'profit_factor', 'win_loss_ratio'
    ]
    
    for metric in required_metrics:
        assert metric in stats, f"Missing metric: {metric}"
        print(f"  ✅ {metric}: {stats[metric]}")
    
    # Validate metric values
    assert stats['win_rate'] >= 0 and stats['win_rate'] <= 100, "Invalid win rate"
    assert stats['sharpe_ratio'] != 0, "Sharpe ratio should not be 0 with data"
    assert stats['profit_factor'] >= 0, "Profit factor should be non-negative"
    
    print("  ✅ AnalyticsService tests passed")


def test_health_endpoint(base_url="http://localhost:5000"):
    """Test health endpoint"""
    print("\n🏥 Testing Health Endpoint...")
    
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        assert response.status_code == 200, f"Health check failed: {response.status_code}"
        
        data = response.json()
        assert data['status'] == 'healthy', "Server not healthy"
        assert 'services' in data, "Missing services info"
        
        print(f"  ✅ Health check passed")
        print(f"  ✅ Status: {data['status']}")
        print(f"  ✅ Services: {', '.join(data['services'].keys())}")
        
        return True
    except requests.RequestException as e:
        print(f"  ⚠️  Health endpoint not accessible: {e}")
        print(f"  ℹ️  Start dashboard with: cd dashboard && python3 app.py")
        return False


def test_overview_endpoint(base_url="http://localhost:5000"):
    """Test overview endpoint with advanced metrics"""
    print("\n📊 Testing Overview Endpoint...")
    
    try:
        response = requests.get(f"{base_url}/api/overview", timeout=5)
        assert response.status_code == 200, f"Overview failed: {response.status_code}"
        
        data = response.json()
        
        # Check advanced metrics
        advanced_metrics = ['sharpe_ratio', 'max_drawdown', 'profit_factor']
        for metric in advanced_metrics:
            assert metric in data, f"Missing advanced metric: {metric}"
            print(f"  ✅ {metric}: {data[metric]}")
        
        print("  ✅ Overview endpoint tests passed")
        return True
    except requests.RequestException as e:
        print(f"  ⚠️  Overview endpoint not accessible: {e}")
        return False


def test_chart_endpoints(base_url="http://localhost:5000"):
    """Test chart endpoints"""
    print("\n📈 Testing Chart Endpoints...")
    
    endpoints = [
        '/api/charts/cumulative-pnl?range=1M',
        '/api/charts/daily-pnl',
        '/api/charts/strategy-performance'
    ]
    
    try:
        for endpoint in endpoints:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            assert response.status_code == 200, f"Chart endpoint failed: {endpoint}"
            
            data = response.json()
            assert 'data' in data or 'strategies' in data, f"Missing data in {endpoint}"
            
            print(f"  ✅ {endpoint}")
        
        print("  ✅ Chart endpoints tests passed")
        return True
    except requests.RequestException as e:
        print(f"  ⚠️  Chart endpoints not accessible: {e}")
        return False


def main():
    """Run all tests"""
    print("="*70)
    print("  Dashboard Validation Test Suite")
    print("="*70)
    
    # Test data layer (always works)
    test_data_parser()
    test_analytics_service()
    
    # Test API endpoints (requires running server)
    print("\n" + "="*70)
    print("  API Endpoint Tests (requires running dashboard)")
    print("="*70)
    
    server_running = test_health_endpoint()
    
    if server_running:
        test_overview_endpoint()
        test_chart_endpoints()
    else:
        print("\n  ℹ️  Skipping API tests (server not running)")
        print("  ℹ️  To run API tests, start the dashboard in another terminal:")
        print("     cd dashboard && python3 app.py")
    
    print("\n" + "="*70)
    print("  ✅ All Tests Completed")
    print("="*70)
    print()


if __name__ == '__main__':
    main()
