#!/usr/bin/env python3
"""
Integration test for column name mismatch fix

Tests that the API endpoints work correctly with the actual CSV format
"""
import sys
from pathlib import Path
import tempfile
import csv

# Add project root to Python path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from dashboard.services.data_parser import DataParser
from dashboard.services.chart_data import ChartDataService

def create_test_csv():
    """Create a test CSV with the actual format"""
    test_dir = Path(tempfile.mkdtemp())
    csv_file = test_dir / "trades.csv"
    
    # Write CSV with actual format
    with open(csv_file, 'w', newline='') as f:
        writer = csv.writer(f)
        # Header with actual column names
        writer.writerow(['timestamp', 'market', 'yes_price', 'no_price', 'sum', 'profit_pct', 'profit_usd', 'status', 'strategy', 'arbitrage_type'])
        # Sample data
        writer.writerow(['2026-02-07 15:16:47', 'BTC-above-100k', '0.468', '0.476', '0.944', '5.9', '0.56', 'executed', 'Unknown', 'Unknown'])
        writer.writerow(['2026-02-08 09:15:33', 'ETH-above-5k', '0.520', '0.495', '1.015', '3.2', '0.42', 'executed', 'Momentum', 'Type-A'])
        writer.writerow(['2026-02-09 10:33:12', 'BTC-above-100k', '0.455', '0.460', '0.915', '8.1', '1.23', 'executed', 'RSI Scalp', 'Unknown'])
    
    return test_dir

def test_cumulative_pnl_api():
    """Test the cumulative P&L API endpoint logic"""
    print("\n" + "=" * 70)
    print("TEST: Cumulative P&L API")
    print("=" * 70)
    
    test_dir = create_test_csv()
    
    try:
        # Initialize services (simulates what the API endpoint does)
        parser = DataParser(test_dir)
        chart_service = ChartDataService(parser)
        
        # Call the service method (simulates API call)
        result = chart_service.get_cumulative_pnl("1M")
        
        # Validate response structure
        assert "data" in result, "Missing 'data' key"
        assert "total_pnl" in result, "Missing 'total_pnl' key"
        assert "start_date" in result, "Missing 'start_date' key"
        assert "end_date" in result, "Missing 'end_date' key"
        
        # Validate data
        assert len(result["data"]) > 0, "No data points returned"
        assert result["total_pnl"] > 0, f"Expected positive P&L, got {result['total_pnl']}"
        
        print(f"✓ API returned {len(result['data'])} data points")
        print(f"✓ Total P&L: ${result['total_pnl']}")
        print("✓ Test passed!")
        
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_daily_pnl_api():
    """Test the daily P&L API endpoint logic"""
    print("\n" + "=" * 70)
    print("TEST: Daily P&L API")
    print("=" * 70)
    
    test_dir = create_test_csv()
    
    try:
        # Initialize services (simulates what the API endpoint does)
        parser = DataParser(test_dir)
        chart_service = ChartDataService(parser)
        
        # Call the service method (simulates API call)
        result = chart_service.get_daily_pnl()
        
        # Validate response structure
        assert "data" in result, "Missing 'data' key"
        assert "total_days" in result, "Missing 'total_days' key"
        assert "profitable_days" in result, "Missing 'profitable_days' key"
        assert "loss_days" in result, "Missing 'loss_days' key"
        
        # Validate data
        assert len(result["data"]) > 0, "No data points returned"
        assert result["total_days"] > 0, f"Expected positive days, got {result['total_days']}"
        
        print(f"✓ API returned {len(result['data'])} days")
        print(f"✓ Total days: {result['total_days']}")
        print(f"✓ Profitable days: {result['profitable_days']}")
        print("✓ Test passed!")
        
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_column_mapping():
    """Test that CSV columns are properly mapped"""
    print("\n" + "=" * 70)
    print("TEST: Column Mapping")
    print("=" * 70)
    
    test_dir = create_test_csv()
    
    try:
        parser = DataParser(test_dir)
        trades = parser.get_all_trades()
        
        assert len(trades) > 0, "No trades loaded"
        
        trade = trades[0]
        
        # Check timestamp is mapped correctly
        assert "timestamp" in trade, "Missing 'timestamp' field"
        assert trade["timestamp"] == "2026-02-07 15:16:47", f"Incorrect timestamp: {trade['timestamp']}"
        
        # Check legacy support
        assert "entry_time" in trade, "Missing 'entry_time' field"
        assert trade["entry_time"] == trade["timestamp"], "entry_time should equal timestamp"
        assert "exit_time" in trade, "Missing 'exit_time' field"
        assert trade["exit_time"] == trade["timestamp"], "exit_time should equal timestamp"
        
        # Check market → symbol mapping
        assert "symbol" in trade, "Missing 'symbol' field"
        assert trade["symbol"] == "BTC-above-100k", f"Incorrect symbol: {trade['symbol']}"
        
        # Check profit_usd → pnl_usd mapping
        assert "pnl_usd" in trade, "Missing 'pnl_usd' field"
        assert trade["pnl_usd"] == 0.56, f"Incorrect pnl_usd: {trade['pnl_usd']}"
        
        # Check profit_pct → pnl_pct mapping
        assert "pnl_pct" in trade, "Missing 'pnl_pct' field"
        assert trade["pnl_pct"] == 5.9, f"Incorrect pnl_pct: {trade['pnl_pct']}"
        
        print("✓ timestamp field correctly read")
        print("✓ entry_time/exit_time legacy support works")
        print("✓ market → symbol mapping works")
        print("✓ profit_usd → pnl_usd mapping works")
        print("✓ profit_pct → pnl_pct mapping works")
        print("✓ Test passed!")
        
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all integration tests"""
    print("\n🧪 Integration Tests for Column Name Mismatch Fix\n")
    
    results = []
    
    # Test 1: Column mapping
    results.append(("Column Mapping", test_column_mapping()))
    
    # Test 2: Cumulative P&L API
    results.append(("Cumulative P&L API", test_cumulative_pnl_api()))
    
    # Test 3: Daily P&L API
    results.append(("Daily P&L API", test_daily_pnl_api()))
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
        if not passed:
            all_passed = False
    
    print("=" * 70)
    
    if all_passed:
        print("\n✅ All integration tests passed!")
        return 0
    else:
        print("\n❌ Some integration tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
