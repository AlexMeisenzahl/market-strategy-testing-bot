#!/bin/bash
# Comprehensive Health Check Script
# Usage: bash scripts/health_check_enhanced.sh

echo "🔍 SYSTEM HEALTH CHECK"
echo "====================="
echo ""

# Check processes
echo "Process Status:"
echo -n "  Bot Process: "
if pgrep -f "python.*bot.py" > /dev/null; then
    PID=$(pgrep -f "python.*bot.py" | head -1)
    echo "✅ Running (PID: $PID)"
else
    echo "❌ Not running"
fi

echo -n "  Dashboard Process: "
if pgrep -f "python.*dashboard" > /dev/null; then
    PID=$(pgrep -f "python.*dashboard" | head -1)
    echo "✅ Running (PID: $PID)"
else
    echo "❌ Not running"
fi

# Check ports
echo ""
echo "Network Status:"
echo -n "  Dashboard Port (5000): "
if command -v lsof &> /dev/null; then
    if lsof -i:5000 > /dev/null 2>&1; then
        echo "✅ Open"
    else
        echo "❌ Not listening"
    fi
else
    echo "⚠️  Cannot check (lsof not available)"
fi

# Check git status
echo ""
echo "Git Status:"
if git status > /dev/null 2>&1; then
    GIT_STATUS=$(git status --porcelain)
    if [ -z "$GIT_STATUS" ]; then
        echo "  ✅ Working directory clean"
    else
        CHANGED_FILES=$(echo "$GIT_STATUS" | wc -l | tr -d ' ')
        echo "  ⚠️  $CHANGED_FILES file(s) modified"
    fi
    
    BRANCH=$(git branch --show-current)
    echo "  Branch: $BRANCH"
    
    COMMITS_BEHIND=$(git rev-list HEAD..origin/main --count 2>/dev/null || echo "0")
    if [ "$COMMITS_BEHIND" -gt 0 ]; then
        echo "  ⚠️  $COMMITS_BEHIND commit(s) behind origin/main"
    else
        echo "  ✅ Up to date with remote"
    fi
else
    echo "  ❌ Not a git repository or git error"
fi

# Check disk space
echo ""
echo "Disk Space:"
DISK_FREE=$(df -h . | awk 'NR==2 {print $4}')
DISK_USED=$(df -h . | awk 'NR==2 {print $5}')
echo "  Free: $DISK_FREE"
echo "  Used: $DISK_USED"

# Check for stuck updates
echo ""
echo "Update System:"
if [ -f ".update_lock" ]; then
    echo "  ⚠️  Update lock file exists"
    echo "  Run: bash scripts/unlock_update.sh"
else
    echo "  ✅ No active update lock"
fi

# Check version
if [ -f "VERSION" ]; then
    VERSION=$(cat VERSION)
    echo "  Current version: $VERSION"
fi

# Check backups
if [ -d "backups" ]; then
    BACKUP_COUNT=$(ls -1 backups/ 2>/dev/null | wc -l | tr -d ' ')
    echo "  Backups available: $BACKUP_COUNT"
    if [ $BACKUP_COUNT -gt 0 ]; then
        LATEST_BACKUP=$(ls -t backups/ | head -1)
        echo "  Latest backup: $LATEST_BACKUP"
    fi
fi

# Check recent errors in logs
echo ""
echo "Recent Log Errors:"
if [ -f "logs/errors.log" ]; then
    ERROR_COUNT=$(tail -100 logs/errors.log 2>/dev/null | grep -c "ERROR" || echo "0")
    WARNING_COUNT=$(tail -100 logs/errors.log 2>/dev/null | grep -c "WARNING" || echo "0")
    echo "  Last 100 lines: $ERROR_COUNT errors, $WARNING_COUNT warnings"
    
    if [ $ERROR_COUNT -gt 0 ]; then
        echo ""
        echo "  Recent errors:"
        tail -100 logs/errors.log | grep "ERROR" | tail -3 | sed 's/^/    /'
    fi
else
    echo "  No error log found"
fi

# Check log file sizes
echo ""
echo "Log Files:"
if [ -d "logs" ]; then
    for log in logs/*.log logs/*.csv; do
        if [ -f "$log" ]; then
            SIZE=$(du -h "$log" | cut -f1)
            echo "  $(basename $log): $SIZE"
        fi
    done
fi

# Check Python environment
echo ""
echo "Python Environment:"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo "  $PYTHON_VERSION"
    
    # Check key modules
    echo -n "  Flask: "
    python3 -c "import flask; print(flask.__version__)" 2>/dev/null || echo "❌ Not installed"
    
    echo -n "  PyYAML: "
    python3 -c "import yaml; print('✅ Installed')" 2>/dev/null || echo "❌ Not installed"
    
    echo -n "  Requests: "
    python3 -c "import requests; print(requests.__version__)" 2>/dev/null || echo "❌ Not installed"
fi

echo ""
echo "====================="
echo "Health check complete"
echo ""

# Overall status
ISSUES=0

if ! pgrep -f "python.*bot.py" > /dev/null; then
    ((ISSUES++))
fi

if ! pgrep -f "python.*dashboard" > /dev/null; then
    ((ISSUES++))
fi

if [ -f ".update_lock" ]; then
    ((ISSUES++))
fi

if [ $ISSUES -eq 0 ]; then
    echo "✅ System Status: HEALTHY"
    exit 0
else
    echo "⚠️  System Status: $ISSUES issue(s) detected"
    exit 1
fi
