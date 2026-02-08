#!/bin/bash
# Test Update System Script
# Test update system without actually updating
# Usage: bash scripts/test_update_system.sh

echo "🧪 TESTING UPDATE SYSTEM"
echo "========================"
echo ""

PASS=0
FAIL=0

# Check git
echo -n "Git installed: "
if command -v git &> /dev/null; then
    GIT_VERSION=$(git --version | cut -d' ' -f3)
    echo "✅ ($GIT_VERSION)"
    ((PASS++))
else
    echo "❌"
    ((FAIL++))
fi

# Check Python
echo -n "Python 3 installed: "
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    echo "✅ ($PYTHON_VERSION)"
    ((PASS++))
else
    echo "❌"
    ((FAIL++))
fi

# Check write permissions
echo -n "Write permissions: "
if [ -w . ]; then
    echo "✅"
    ((PASS++))
else
    echo "❌"
    ((FAIL++))
fi

# Check disk space
echo -n "Disk space (need >1GB): "
if command -v df &> /dev/null; then
    if [[ "$OSTYPE" == "darwin"* ]]; then
        DISK_FREE=$(df -g . | awk 'NR==2 {print $4}')
        UNIT="GB"
    else
        DISK_FREE=$(df --output=avail -BG . | tail -1 | tr -d 'G ')
        UNIT="GB"
    fi
    
    if [ "$DISK_FREE" -gt 1 ]; then
        echo "✅ ${DISK_FREE}${UNIT} free"
        ((PASS++))
    else
        echo "❌ Only ${DISK_FREE}${UNIT} free"
        ((FAIL++))
    fi
else
    echo "⚠️  Cannot check"
fi

# Check GitHub connectivity
echo -n "GitHub connection: "
if curl -s --connect-timeout 5 https://api.github.com > /dev/null 2>&1; then
    echo "✅"
    ((PASS++))
else
    echo "❌"
    ((FAIL++))
fi

# Check backup directory
echo -n "Can create backup: "
TEST_BACKUP="backups/test_$(date +%s)"
if mkdir -p "$TEST_BACKUP" 2>/dev/null; then
    if [ -f "VERSION" ]; then
        cp VERSION "$TEST_BACKUP/" 2>/dev/null
    else
        echo "test" > "$TEST_BACKUP/test.txt"
    fi
    
    if [ -f "$TEST_BACKUP/VERSION" ] || [ -f "$TEST_BACKUP/test.txt" ]; then
        echo "✅"
        rm -rf "$TEST_BACKUP"
        ((PASS++))
    else
        echo "❌ Cannot write to backup"
        rm -rf "$TEST_BACKUP"
        ((FAIL++))
    fi
else
    echo "❌ Cannot create directory"
    ((FAIL++))
fi

# Simulate update (dry run)
echo -n "Git fetch (dry run): "
if git fetch origin main --dry-run 2>&1 | grep -q "main\|up to date"; then
    echo "✅"
    ((PASS++))
else
    echo "❌"
    ((FAIL++))
fi

# Check Python modules
echo -n "Required Python modules: "
MISSING_MODULES=""
for module in yaml requests psutil; do
    if ! python3 -c "import $module" 2>/dev/null; then
        MISSING_MODULES="$MISSING_MODULES $module"
    fi
done

if [ -z "$MISSING_MODULES" ]; then
    echo "✅"
    ((PASS++))
else
    echo "❌ Missing:$MISSING_MODULES"
    ((FAIL++))
fi

# Check for update lock
echo -n "No update lock: "
if [ -f ".update_lock" ]; then
    echo "⚠️  Lock exists (run unlock_update.sh)"
else
    echo "✅"
    ((PASS++))
fi

# Check version file
echo -n "VERSION file exists: "
if [ -f "VERSION" ]; then
    VERSION=$(cat VERSION)
    echo "✅ ($VERSION)"
    ((PASS++))
else
    echo "⚠️  Not found (will be created)"
fi

echo ""
echo "========================"
echo "Results: $PASS passed, $FAIL failed"
echo "========================"

if [ $FAIL -eq 0 ]; then
    echo "✅ System ready for updates!"
    exit 0
else
    echo "❌ Fix issues before updating"
    exit 1
fi
