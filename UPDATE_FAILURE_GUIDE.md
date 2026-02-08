# Update Failure Guide

What to do when updates fail - organized by failure scenario.

---

## Scenario 1: Update Stuck at "Downloading..."

**What You See:**
- Progress bar stuck at 30-40%
- "Downloading from GitHub..." message for >5 minutes
- No movement in progress

**Why It Happened:**
- Slow internet connection
- GitHub server issues
- Large update size
- Network timeout

**How to Fix:**

```bash
# Step 1: Check if it's really stuck (wait 5 min)
# Watch for any progress

# Step 2: If truly stuck, cancel
# In dashboard: Click "Cancel Update"
# Or terminal: bash scripts/unlock_update.sh

# Step 3: Cleanup
bash scripts/cleanup_failed_update.sh

# Step 4: Check internet
ping -c 5 github.com
curl -I https://api.github.com

# Step 5: Try again with better internet
# Or use manual update:
bash scripts/manual_update.sh
```

**Prevention:**
- Use stable wired connection
- Don't update on slow/flaky WiFi
- Check GitHub status first: https://www.githubstatus.com

---

## Scenario 2: Update Completed But Bot Won't Start

**What You See:**
- Update shows "Complete" or 100%
- But dashboard shows "Bot not running"
- Can't access dashboard
- Process exits immediately

**Why It Happened:**
- New version incompatible with your Python version
- Missing new dependencies
- Config file format changed
- Database migration needed

**How to Fix:**

```bash
# Step 1: Check error logs
tail -50 logs/errors.log
tail -50 logs/bot.log

# Step 2: Try starting manually to see error
python3 bot.py

# Step 3: If dependency error
pip3 install -r requirements.txt --force-reinstall

# Step 4: If config error
# Restore old config, merge manually
cp backups/backup_latest/config.yaml config.yaml.old
# Compare: diff config.yaml config.yaml.old

# Step 5: If still broken, rollback
bash scripts/emergency_rollback.sh

# Step 6: Report issue on GitHub with error logs
```

**Prevention:**
- Read changelog before updating
- Check if major Python version change needed
- Update during low-activity time

---

## Scenario 3: "I Don't Want to Update Right Now"

**What You See:**
- Dashboard showing "Update Available" banner
- Don't want to update yet

**What to Do:**

**Option 1: Dismiss Notification**
- Click "Dismiss" on update banner
- Will remind you next time dashboard loads

**Option 2: Disable Update Checks (Temporary)**
```bash
# Stop dashboard
bash scripts/force_stop.sh

# Edit dashboard/app.py
# Comment out version_manager initialization
# Then restart
python3 start_dashboard.py
```

**Option 3: Update Later**
- Updates are never automatic
- You always control when to update
- Can wait as long as you want

**When to Update:**
- No active trades
- Not during important trading time
- Have 5-10 minutes to monitor
- On stable internet

---

## Scenario 4: Clicked Update During Active Trades

**What You See:**
- Update started
- Realized you have open positions
- Worried about losing trades

**What to Do Immediately:**

```bash
# Option 1: Let it complete (safest)
# Updates are fast (1-2 min)
# Trades are saved in state files
# Will resume after restart

# Option 2: If really need to cancel
# Click "Cancel Update" in dashboard
# Or: bash scripts/unlock_update.sh

# Then check your trades:
# - Check exchange directly
# - Check logs/trades.csv
# - Check state/ directory
```

**After Update:**
- Verify bot restarted
- Check dashboard for positions
- Check exchange website/app
- Verify all trades still tracked

**Prevention:**
- Close positions before updating
- Or pause bot: Stop trading in dashboard
- Check "Active Trades" warning in update modal

---

## Scenario 5: "Git Says 'Local Changes' Error"

**What You See:**
- Update fails immediately
- Error: "Local changes detected"
- or "Working tree not clean"

**Why It Happened:**
- You edited bot code directly
- Files modified accidentally
- Incomplete previous update

**How to Fix:**

```bash
# Step 1: See what changed
git status
git diff

# Step 2: Choose recovery method

# Method A: Save changes (if you want them)
git stash save "my-changes-$(date +%Y%m%d)"
# Update will work now
# Later: git stash pop  # Reapply changes

# Method B: Discard changes (if you don't need them)
git checkout -- .
git clean -fd

# Method C: Use cleanup script (easiest)
bash scripts/cleanup_failed_update.sh
```

**Prevention:**
- Don't edit code directly
- Use config.yaml for settings
- If you must edit code, use git branches

---

## Scenario 6: Update Fails: "New Version Requires Python 3.9+"

**What You See:**
- Update fails with Python version error
- "Python 3.9 or higher required"
- You have Python 3.8

**How to Fix:**

### Mac (using Homebrew):
```bash
# Install Python 3.10
brew install python@3.10

# Use it
python3.10 --version

# Create new venv
python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Start bot with new Python
python3.10 start_dashboard.py
```

### Ubuntu/Debian:
```bash
# Add deadsnakes PPA
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update

# Install Python 3.10
sudo apt install python3.10 python3.10-venv

# Create new venv
python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Or Rollback:**
```bash
# Rollback to version that works with your Python
bash scripts/emergency_rollback.sh
```

**Prevention:**
- Check changelog for Python requirements
- Keep Python updated
- Use pyenv for managing versions

---

## Scenario 7: Lost Config Settings After Update

**What You See:**
- Bot reset to defaults
- Custom settings gone
- API keys missing

**Why It Happened:**
- Config file overwritten
- Update reset config
- Backup didn't include config

**How to Fix:**

```bash
# Step 1: Find your backup
ls -lh backups/

# Step 2: Check what's in the backup
ls -lh backups/backup_20240208_101533/

# Step 3: Restore config only
cp backups/backup_20240208_101533/config.yaml config.yaml

# Step 4: Restart bot
bash scripts/force_stop.sh
python3 start_dashboard.py

# Step 5: Verify settings in dashboard
```

**If No Backup Has Config:**
```bash
# Check git history
git log --oneline config.yaml
git show <commit>:config.yaml > config_old.yaml

# Or check stashed changes
git stash list
git stash show stash@{0} -p
```

**Prevention:**
- Keep separate backup of config
- Don't store secrets in config (use .env)
- Manual backup before updates:
  ```bash
  cp config.yaml config.backup.yaml
  ```

---

## Scenario 8: Mac Restarted During Update

**What You See:**
- Mac rebooted (update, power loss, crash)
- Update was in progress
- Now bot won't start
- Update lock file exists

**How to Fix:**

```bash
# Step 1: Check damage
bash scripts/health_check_enhanced.sh

# Step 2: Remove stale lock
bash scripts/unlock_update.sh

# Step 3: Check file integrity
python3 -c "import bot; print('✅ Bot file OK')"
python3 -c "import dashboard.app; print('✅ Dashboard file OK')"

# Step 4a: If files OK
python3 start_dashboard.py

# Step 4b: If files corrupted
bash scripts/emergency_rollback.sh

# Step 5: Cleanup
bash scripts/cleanup_failed_update.sh
```

**Check for Corruption:**
```bash
# Test imports
python3 -c "import bot"
python3 -c "import dashboard.app"
python3 -c "import yaml; yaml.safe_load(open('config.yaml'))"

# Check git
git status
git fsck
```

**Prevention:**
- Don't update on low battery
- Don't update during OS updates
- UPS for desktop computers

---

## Scenario 9: "Dependencies Won't Install"

**What You See:**
- Update fails at "Installing dependencies..."
- pip errors
- Compilation errors
- Wheel building failures

**Why It Happened:**
- Missing system libraries
- Compiler not installed
- Package conflict
- PyPI issues

**How to Fix:**

### Mac:
```bash
# Install Xcode tools
xcode-select --install

# Install dependencies
brew install openssl libffi

# Retry
pip3 install -r requirements.txt
```

### Ubuntu:
```bash
# Install build essentials
sudo apt install build-essential python3-dev

# Retry
pip3 install -r requirements.txt
```

### All Platforms:
```bash
# Update pip
python3 -m pip install --upgrade pip

# Try with no cache
pip3 install -r requirements.txt --no-cache-dir

# Try with prebuilt wheels only
pip3 install -r requirements.txt --only-binary :all:

# Or rollback
bash scripts/emergency_rollback.sh
```

---

## Scenario 10: "Everything Worked But Performance is Worse"

**What You See:**
- Update completed successfully
- Bot running
- But slower, using more CPU/RAM
- or making bad decisions

**What to Do:**

```bash
# Step 1: Check resource usage
top -p $(pgrep -f "python.*bot")
# Or: htop

# Step 2: Check logs for new errors
tail -100 logs/errors.log | grep -i "error\|warning"

# Step 3: Compare with backup version
# Rollback temporarily
bash scripts/emergency_rollback.sh

# Test old version for comparison
# Monitor for 30 minutes

# Step 4: If new version is truly worse
# Stay on old version
# Report issue on GitHub

# Or try update again later
git pull origin main
```

**Report Issue:**
- Performance metrics (CPU/RAM usage)
- Trading results comparison
- Error logs
- Steps to reproduce

---

## General Recovery Steps

For any update failure:

1. **Don't Panic** - Backups exist
2. **Check Health** - `bash scripts/health_check_enhanced.sh`
3. **Read Logs** - `tail -50 logs/errors.log`
4. **Try Rollback** - `bash scripts/emergency_rollback.sh`
5. **Report Issue** - If reproducible

---

## Quick Decision Tree

```
Update Failed?
├─ Stuck/Frozen? 
│  └─ bash scripts/unlock_update.sh
│     bash scripts/cleanup_failed_update.sh
│
├─ Bot Won't Start?
│  └─ bash scripts/emergency_rollback.sh
│
├─ Config/Data Lost?
│  └─ bash scripts/restore_backup.sh
│
├─ Git Issues?
│  └─ bash scripts/cleanup_failed_update.sh
│
└─ Everything Broken?
   └─ See EMERGENCY_RECOVERY.md
```

---

## Prevention Checklist

Before EVERY update:

- [ ] No active trades (or OK to pause them)
- [ ] Stable internet connection (test: `ping -c 10 github.com`)
- [ ] 1GB+ free disk space (`df -h`)
- [ ] Bot running stable for 1+ hour
- [ ] 5-10 minutes to monitor
- [ ] Know where scripts are: `ls scripts/`
- [ ] (Optional) Manual config backup: `cp config.yaml config.backup`

---

## Still Need Help?

See:
- EMERGENCY_RECOVERY.md - Critical failures
- TROUBLESHOOTING.md - Common issues
- GitHub Issues - Community help
