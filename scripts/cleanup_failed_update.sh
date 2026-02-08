#!/bin/bash
# Cleanup Failed Update Script
# Clean up after failed update
# Usage: bash scripts/cleanup_failed_update.sh

echo "🧹 CLEANING UP FAILED UPDATE"
echo "============================"
echo ""

# Remove lock
if [ -f ".update_lock" ]; then
    echo "Removing update lock..."
    rm .update_lock
    echo "  ✅ Lock removed"
fi

# Clean git state
echo ""
echo "Cleaning git state..."
git reset --hard HEAD 2>/dev/null && echo "  ✅ Git reset" || echo "  ⚠️  Git reset failed"
git clean -fd 2>/dev/null && echo "  ✅ Untracked files cleaned" || true

# Check for stashed changes
echo ""
if git stash list 2>/dev/null | grep -q "auto-update\|manual-update"; then
    echo "Found stashed changes from update:"
    git stash list | grep "auto-update\|manual-update"
    echo ""
    read -p "Drop stashed changes? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Find and drop the stash
        STASH_INDEX=$(git stash list | grep -m1 "auto-update\|manual-update" | cut -d: -f1)
        if [ -n "$STASH_INDEX" ]; then
            git stash drop "$STASH_INDEX"
            echo "  ✅ Stashed changes dropped"
        fi
    else
        echo "  Stashed changes kept"
    fi
fi

# Remove progress file
if [ -f "logs/update_progress.json" ]; then
    echo ""
    echo "Removing progress file..."
    rm logs/update_progress.json
    echo "  ✅ Progress file removed"
fi

echo ""
echo "============================"
echo "✅ Cleanup complete"
echo "============================"
echo ""

# Run health check
if [ -f "scripts/health_check.sh" ]; then
    echo "Running health check..."
    echo ""
    bash scripts/health_check.sh
fi
