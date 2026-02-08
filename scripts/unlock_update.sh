#!/bin/bash
# Unlock Update Script
# Clear stuck update locks
# Usage: bash scripts/unlock_update.sh

echo "🔓 UNLOCKING UPDATE SYSTEM"
echo "=========================="
echo ""

if [ ! -f ".update_lock" ]; then
    echo "No lock file found - system is not locked"
    exit 0
fi

echo "Lock file found, checking..."

# Get lock age (macOS and Linux compatible)
if [[ "$OSTYPE" == "darwin"* ]]; then
    LOCK_TIME=$(stat -f %m .update_lock)
else
    LOCK_TIME=$(stat -c %Y .update_lock)
fi

CURRENT_TIME=$(date +%s)
AGE=$((CURRENT_TIME - LOCK_TIME))
AGE_MIN=$((AGE / 60))

echo "Lock age: $AGE_MIN minutes"
echo ""

# Check if stale (>30 min)
if [ $AGE -gt 1800 ]; then
    echo "Lock is stale (>30 min), removing..."
    rm .update_lock
    echo "✅ Lock removed"
else
    echo "⚠️  Lock is recent, update may be in progress"
    echo ""
    read -p "Force remove? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm .update_lock
        echo "✅ Lock removed"
    else
        echo "Lock kept"
        exit 1
    fi
fi

echo ""
echo "=========================="
echo "Update system is now unlocked"
