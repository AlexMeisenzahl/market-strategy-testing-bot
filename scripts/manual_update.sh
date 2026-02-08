#!/bin/bash
# Manual Update Script
# Step-by-step update with confirmation prompts
# Usage: bash scripts/manual_update.sh

set -e

echo "📦 MANUAL UPDATE PROCESS"
echo "========================"
echo ""

# Pre-flight checks
echo "Running pre-flight checks..."
echo ""

# Check Python
if command -v python3 &> /dev/null; then
    echo "  ✅ Python: $(python3 --version)"
else
    echo "  ❌ Python3 not found"
    exit 1
fi

# Check git
if command -v git &> /dev/null; then
    echo "  ✅ Git: $(git --version)"
else
    echo "  ❌ Git not found"
    exit 1
fi

# Check internet
if curl -s --connect-timeout 5 https://api.github.com > /dev/null; then
    echo "  ✅ Internet connection"
else
    echo "  ❌ No internet connection"
    exit 1
fi

# Check disk space
DISK_FREE=$(df -h . | awk 'NR==2 {print $4}')
echo "  ✅ Disk space: $DISK_FREE free"

# Check git status
GIT_STATUS=$(git status --porcelain)
if [ -z "$GIT_STATUS" ]; then
    echo "  ✅ Git: Working directory clean"
else
    echo "  ⚠️  Git: Local changes detected (will be stashed)"
fi

# Check for running processes
if pgrep -f "python.*bot.py" > /dev/null; then
    echo "  ⚠️  Bot is currently running"
fi

if pgrep -f "python.*dashboard" > /dev/null; then
    echo "  ⚠️  Dashboard is currently running"
fi

echo ""
read -p "Continue with update? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Update cancelled"
    exit 1
fi

# Create backup
echo ""
echo "📦 Creating backup..."
BACKUP_NAME="backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "backups/$BACKUP_NAME"

# Backup files
cp -r *.py "backups/$BACKUP_NAME/" 2>/dev/null || true
cp VERSION "backups/$BACKUP_NAME/" 2>/dev/null || true
cp config.yaml "backups/$BACKUP_NAME/" 2>/dev/null || true

# Backup directories
for dir in services dashboard database state; do
    if [ -d "$dir" ]; then
        cp -r "$dir" "backups/$BACKUP_NAME/"
    fi
done

BACKUP_SIZE=$(du -sh "backups/$BACKUP_NAME" | cut -f1)
echo "✅ Backup created: $BACKUP_NAME ($BACKUP_SIZE)"

echo ""
read -p "Proceed with download? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Update cancelled"
    exit 1
fi

# Stash local changes if any
if [ -n "$GIT_STATUS" ]; then
    echo ""
    echo "📥 Stashing local changes..."
    git stash save "manual-update-$(date +%Y%m%d_%H%M%S)"
    echo "✅ Changes stashed"
fi

# Download update
echo ""
echo "📥 Downloading from GitHub..."
git fetch origin main
git pull origin main
echo "✅ Download complete"

# Show what changed
CHANGED_FILES=$(git diff --name-only HEAD@{1} HEAD 2>/dev/null | wc -l)
echo ""
echo "📝 Changed files: $CHANGED_FILES"
git diff --stat HEAD@{1} HEAD 2>/dev/null || true

echo ""
read -p "Install dependencies? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Skipping dependencies"
else
    # Install dependencies
    echo ""
    echo "📦 Installing dependencies..."
    python3 -m pip install -r requirements.txt --quiet
    echo "✅ Dependencies installed"
fi

echo ""
read -p "Restart bot? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "⚠️  Update downloaded but bot not restarted"
    echo "To restart manually:"
    echo "  python3 start_dashboard.py"
    exit 0
fi

# Restart
echo ""
echo "🔄 Restarting bot..."
pkill -f "python.*bot.py" 2>/dev/null || true
pkill -f "python.*dashboard" 2>/dev/null || true
sleep 3
python3 start_dashboard.py &

echo ""
echo "========================"
echo "✅ UPDATE COMPLETE"
echo "========================"
echo ""
echo "Dashboard: http://localhost:5000"
echo "Backup saved: $BACKUP_NAME"
echo ""
echo "To rollback if needed:"
echo "  bash scripts/emergency_rollback.sh $BACKUP_NAME"
