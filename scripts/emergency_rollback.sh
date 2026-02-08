#!/bin/bash
# Emergency Rollback Script
# Works even if dashboard is dead
# Usage: bash scripts/emergency_rollback.sh [backup_name]

set -e

echo "🚨 EMERGENCY ROLLBACK STARTING..."
echo "================================="

# Find latest backup or use specified
if [ -z "$1" ]; then
    if [ ! -d "backups" ]; then
        echo "❌ No backups directory found"
        exit 1
    fi
    
    BACKUP=$(ls -t backups/ 2>/dev/null | head -1)
    if [ -z "$BACKUP" ]; then
        echo "❌ No backups found"
        exit 1
    fi
    echo "📦 Using latest backup: $BACKUP"
else
    BACKUP=$1
    if [ ! -d "backups/$BACKUP" ]; then
        echo "❌ Backup not found: $BACKUP"
        echo "Available backups:"
        ls -1 backups/ 2>/dev/null || echo "  (none)"
        exit 1
    fi
    echo "📦 Using specified backup: $BACKUP"
fi

# Stop all bot processes
echo ""
echo "🛑 Stopping processes..."
pkill -f "python.*bot.py" 2>/dev/null || true
pkill -f "python.*dashboard" 2>/dev/null || true
pkill -f "python.*start_dashboard" 2>/dev/null || true
sleep 3

# Restore files
echo ""
echo "📂 Restoring files from backup..."
if [ ! -d "backups/$BACKUP" ]; then
    echo "❌ Backup directory not found: backups/$BACKUP"
    exit 1
fi

# Restore Python files
cp -v backups/$BACKUP/*.py . 2>/dev/null || true

# Restore VERSION
cp -v backups/$BACKUP/VERSION . 2>/dev/null || true

# Restore config
cp -v backups/$BACKUP/config.yaml . 2>/dev/null || true

# Restore directories
for dir in services dashboard database state; do
    if [ -d "backups/$BACKUP/$dir" ]; then
        echo "Restoring $dir/..."
        rm -rf "$dir"
        cp -r "backups/$BACKUP/$dir" .
    fi
done

echo "✅ Files restored"

# Restart bot
echo ""
echo "🔄 Restarting bot..."
python3 start_dashboard.py &
sleep 3

echo ""
echo "================================="
echo "✅ ROLLBACK COMPLETE"
echo "================================="
echo ""
echo "Check dashboard at http://localhost:5000"
echo ""
echo "If problems persist, check logs:"
echo "  cat logs/bot.log"
echo "  cat logs/errors.log"
