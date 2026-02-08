#!/bin/bash
# Backup Restoration Script
# Usage: bash scripts/restore_backup.sh [backup_name]

echo "💾 BACKUP RESTORATION"
echo "===================="
echo ""

# List backups if none specified
if [ -z "$1" ]; then
    if [ ! -d "backups" ] || [ -z "$(ls -A backups 2>/dev/null)" ]; then
        echo "❌ No backups available"
        exit 1
    fi
    
    echo "Available backups:"
    echo ""
    ls -lh backups/ | tail -n +2 | awk '{print "  " $9 " (" $5 ", " $6 " " $7 ")"}'
    echo ""
    read -p "Enter backup name: " BACKUP
else
    BACKUP=$1
fi

# Validate backup
if [ ! -d "backups/$BACKUP" ]; then
    echo "❌ Backup not found: $BACKUP"
    exit 1
fi

echo ""
echo "Restoring from: $BACKUP"
echo ""

# Show backup contents
if [ -f "backups/$BACKUP/VERSION" ]; then
    VERSION=$(cat "backups/$BACKUP/VERSION")
    echo "Backup version: $VERSION"
fi

BACKUP_SIZE=$(du -sh "backups/$BACKUP" | cut -f1)
echo "Backup size: $BACKUP_SIZE"

echo ""
read -p "This will overwrite current files. Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Restoration cancelled"
    exit 1
fi

# Stop bot
echo ""
echo "🛑 Stopping processes..."
pkill -f "python.*bot.py" 2>/dev/null || true
pkill -f "python.*dashboard" 2>/dev/null || true
sleep 3

# Restore
echo ""
echo "📂 Restoring files..."

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

# Restart
echo ""
echo "🔄 Restarting bot..."
python3 start_dashboard.py &

echo ""
echo "===================="
echo "✅ RESTORATION COMPLETE"
echo "===================="
echo ""
echo "Dashboard: http://localhost:5000"
