#!/bin/bash
# Force Stop Script
# Force stop all bot processes
# Usage: bash scripts/force_stop.sh

echo "🛑 FORCE STOPPING ALL PROCESSES"
echo "================================"

# Kill bot processes
echo "Stopping bot.py..."
pkill -9 -f "python.*bot.py" 2>/dev/null && echo "  ✅ Bot stopped" || echo "  (not running)"

# Kill dashboard processes
echo "Stopping dashboard..."
pkill -9 -f "python.*dashboard" 2>/dev/null && echo "  ✅ Dashboard stopped" || echo "  (not running)"
pkill -9 -f "python.*start_dashboard" 2>/dev/null || true

# Remove PID files
echo "Cleaning up PID files..."
rm -f .bot.pid
rm -f .dashboard.pid

echo ""
echo "================================"
echo "✅ All processes stopped"
echo "================================"
echo ""
echo "To restart:"
echo "  python3 start_dashboard.py"
