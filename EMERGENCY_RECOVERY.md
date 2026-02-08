# Emergency Recovery Guide

This guide helps you recover from critical failures during or after an update.

## Quick Recovery Commands

```bash
# Emergency rollback to last backup
bash scripts/emergency_rollback.sh

# Force stop all processes
bash scripts/force_stop.sh

# Unlock stuck update
bash scripts/unlock_update.sh

# Check system health
bash scripts/health_check_enhanced.sh
```

---

## Common Emergency Scenarios

### 1. Bot Won't Start After Update

**Symptoms:**
- Dashboard shows "Bot not running"
- Can't access http://localhost:5000
- Process exits immediately

**Recovery Steps:**

```bash
# Step 1: Check system health
bash scripts/health_check_enhanced.sh

# Step 2: Try emergency rollback
bash scripts/emergency_rollback.sh

# Step 3: If rollback doesn't work, check logs
cat logs/errors.log | tail -50
cat logs/bot.log | tail -50

# Step 4: If specific backup needed
bash scripts/restore_backup.sh backup_20240208_101533
```

**If Still Broken:**
1. Check Python version: `python3 --version` (need 3.8+)
2. Reinstall dependencies: `pip3 install -r requirements.txt`
3. Check config file: `cat config.yaml` (look for syntax errors)

---

### 2. Dashboard is Dead

**Symptoms:**
- Can't access dashboard at all
- No response from http://localhost:5000
- Terminal shows errors

**Recovery Steps (Terminal Only):**

```bash
# Force stop everything
bash scripts/force_stop.sh

# Wait a moment
sleep 3

# Check if port is in use
lsof -i:5000
# If something is using it: kill -9 <PID>

# Try starting dashboard
python3 start_dashboard.py

# If that fails, try emergency rollback
bash scripts/emergency_rollback.sh
```

**Alternative - Restore Specific Backup:**

```bash
# List available backups
ls -lh backups/

# Restore specific backup
bash scripts/restore_backup.sh backup_20240208_101533
```

---

### 3. Update Stuck or Frozen

**Symptoms:**
- Update progress stopped moving
- Dashboard shows "Updating..." for >10 minutes
- Update lock exists but nothing happening

**Recovery Steps:**

```bash
# Step 1: Check if update is actually stuck
bash scripts/health_check_enhanced.sh

# Step 2: Check update lock age
ls -lh .update_lock
# If >30 minutes old, it's stuck

# Step 3: Unlock and cleanup
bash scripts/unlock_update.sh
bash scripts/cleanup_failed_update.sh

# Step 4: Rollback to last backup
bash scripts/emergency_rollback.sh

# Step 5: Verify system
bash scripts/health_check_enhanced.sh
```

---

### 4. Git Conflicts / Local Changes Error

**Symptoms:**
- Update fails with "local changes" error
- Git says "uncommitted changes"
- Can't pull from GitHub

**Recovery Steps:**

```bash
# Option 1: Save your changes
git stash save "my-changes-$(date +%Y%m%d)"
git pull origin main
git stash pop  # Apply changes back (may have conflicts)

# Option 2: Discard local changes
git reset --hard HEAD
git clean -fd
git pull origin main

# Option 3: Full cleanup
bash scripts/cleanup_failed_update.sh
```

---

### 5. Lost Data / Config After Update

**Symptoms:**
- Config settings reset
- Lost custom configurations
- Data directory empty

**Recovery Steps:**

```bash
# Step 1: Find latest backup with your data
ls -lh backups/

# Step 2: Check what's in the backup
ls -lh backups/backup_20240208_101533/

# Step 3: Restore full backup
bash scripts/restore_backup.sh backup_20240208_101533

# OR restore specific files only
cp backups/backup_20240208_101533/config.yaml .
cp -r backups/backup_20240208_101533/data/ .
cp -r backups/backup_20240208_101533/state/ .
```

---

### 6. Mac Restarted During Update

**Symptoms:**
- System rebooted mid-update
- Bot not running after restart
- Update lock file exists

**Recovery Steps:**

```bash
# Step 1: Check what state we're in
bash scripts/health_check_enhanced.sh

# Step 2: Remove stale lock
bash scripts/unlock_update.sh

# Step 3: Check if files are corrupted
python3 -c "import bot; import dashboard.app; print('✅ Files OK')"

# Step 4a: If files OK, just restart
python3 start_dashboard.py

# Step 4b: If files corrupted, rollback
bash scripts/emergency_rollback.sh

# Step 5: Cleanup git state if needed
bash scripts/cleanup_failed_update.sh
```

---

### 7. Everything is Broken - Nuclear Option

**When to Use:**
- Multiple recovery attempts failed
- System is completely unresponsive
- You have recent backups

**Nuclear Recovery:**

```bash
# ⚠️ WARNING: This will reset everything ⚠️

# Step 1: Stop everything
bash scripts/force_stop.sh

# Step 2: Clean git completely
git fetch origin main
git reset --hard origin/main
git clean -fdx

# Step 3: Reinstall dependencies
pip3 install -r requirements.txt --force-reinstall

# Step 4: Restore data from backup
bash scripts/restore_backup.sh

# Step 5: Restart
python3 start_dashboard.py
```

**If Even Nuclear Option Fails:**
1. Clone fresh copy: `git clone <repo_url> market-bot-fresh`
2. Copy your backups: `cp -r market-bot-old/backups/ market-bot-fresh/`
3. Copy your config: `cp market-bot-old/config.yaml market-bot-fresh/`
4. Install deps: `cd market-bot-fresh && pip3 install -r requirements.txt`
5. Start fresh: `python3 start_dashboard.py`

---

## Prevention Tips

### Before ANY Update:

1. **Manual Backup (Extra Safety):**
   ```bash
   tar -czf manual_backup_$(date +%Y%m%d).tar.gz \
       *.py config.yaml services/ dashboard/ database/ state/ logs/
   ```

2. **Check System Health:**
   ```bash
   bash scripts/test_update_system.sh
   ```

3. **Stop Active Trading:**
   - Close all open positions
   - Pause bot if trading live

4. **Stable Internet:**
   - Don't update on flaky WiFi
   - Don't update during download/upload

5. **Time to Monitor:**
   - Updates take 1-5 minutes
   - Stay near computer during update

---

## Recovery Verification

After any recovery, verify system health:

```bash
# Full health check
bash scripts/health_check_enhanced.sh

# Check processes
ps aux | grep "python.*bot"
ps aux | grep "python.*dashboard"

# Check dashboard access
curl http://localhost:5000/health

# Check logs for errors
tail -50 logs/errors.log
```

---

## Getting Help

If you're still stuck:

1. **Check Logs:**
   ```bash
   cat logs/errors.log
   cat logs/bot.log
   cat logs/update.log
   ```

2. **Save Error Info:**
   ```bash
   bash scripts/health_check_enhanced.sh > health_report.txt
   tail -100 logs/errors.log > error_report.txt
   ```

3. **Create GitHub Issue:**
   - Include health_report.txt
   - Include error_report.txt
   - Describe what you were doing when it broke

4. **Emergency Contact:**
   - GitHub Issues: https://github.com/AlexMeisenzahl/market-strategy-testing-bot/issues
   - Include all error logs and health check output

---

## Quick Reference Card

Print this and keep near your computer:

```
EMERGENCY RECOVERY COMMANDS
===========================

Stop Everything:
  bash scripts/force_stop.sh

Rollback to Last Backup:
  bash scripts/emergency_rollback.sh

Unlock Stuck Update:
  bash scripts/unlock_update.sh

Check System Health:
  bash scripts/health_check_enhanced.sh

Clean Up Failed Update:
  bash scripts/cleanup_failed_update.sh

Restore Specific Backup:
  bash scripts/restore_backup.sh [backup_name]

List Backups:
  ls -lh backups/

View Recent Errors:
  tail -50 logs/errors.log
```

---

**Remember:** Automatic backups are created before every update. You can always roll back!
