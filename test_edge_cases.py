#!/usr/bin/env python3
"""
Test edge cases for CSV parsing with empty values
"""
import sys
from pathlib import Path
import tempfile
import csv

# Add project root to Python path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from dashboard.services.data_parser import DataParser

def test_empty_values():
    """Test that empty CSV values are handled gracefully"""
    test_dir = Path(tempfile.mkdtemp())
    csv_file = test_dir / "trades.csv"
    
    # Write CSV with empty values
    with open(csv_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['timestamp', 'market', 'profit_usd', 'profit_pct', 'status', 'strategy', 'duration_minutes', 'entry_price', 'exit_price'])
        # Row with empty values
        writer.writerow(['2026-02-07 15:16:47', 'BTC', '', '', 'executed', 'Test', '', '', ''])
        # Row with some values
        writer.writerow(['2026-02-08 10:00:00', 'ETH', '1.50', '2.5', 'executed', 'Test2', '60', '100', '102.5'])
    
    parser = DataParser(test_dir)
    trades = parser.get_all_trades()
    
    assert len(trades) == 2, f"Expected 2 trades, got {len(trades)}"
    
    # First trade with empty values should have defaults
    trade1 = trades[0]
    assert trade1['pnl_usd'] == 0.0, f"Expected 0.0 for empty pnl_usd, got {trade1['pnl_usd']}"
    assert trade1['pnl_pct'] == 0.0, f"Expected 0.0 for empty pnl_pct, got {trade1['pnl_pct']}"
    assert trade1['duration_minutes'] == 0, f"Expected 0 for empty duration_minutes, got {trade1['duration_minutes']}"
    assert trade1['entry_price'] == 0.0, f"Expected 0.0 for empty entry_price, got {trade1['entry_price']}"
    assert trade1['exit_price'] == 0.0, f"Expected 0.0 for empty exit_price, got {trade1['exit_price']}"
    assert trade1['outcome'] == 'breakeven', f"Expected 'breakeven' for 0 pnl, got {trade1['outcome']}"
    
    # Second trade with values should parse correctly
    trade2 = trades[1]
    assert trade2['pnl_usd'] == 1.50, f"Expected 1.50, got {trade2['pnl_usd']}"
    assert trade2['pnl_pct'] == 2.5, f"Expected 2.5, got {trade2['pnl_pct']}"
    assert trade2['duration_minutes'] == 60, f"Expected 60, got {trade2['duration_minutes']}"
    assert trade2['entry_price'] == 100.0, f"Expected 100.0, got {trade2['entry_price']}"
    assert trade2['exit_price'] == 102.5, f"Expected 102.5, got {trade2['exit_price']}"
    assert trade2['outcome'] == 'win', f"Expected 'win', got {trade2['outcome']}"
    
    print("✅ All edge case tests passed!")
    return True

if __name__ == "__main__":
    try:
        test_empty_values()
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
