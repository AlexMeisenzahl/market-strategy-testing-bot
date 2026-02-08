# Troubleshooting Guide

Common issues and how to fix them.

---

## Update System Issues

### Update Fails: "Pre-flight Checks Failed"

**Problem:** Update won't start because checks fail.

**Diagnosis:**
```bash
bash scripts/test_update_system.sh
```

**Solutions:**

| Check Failed | Solution |
|--------------|----------|
| Git not installed | Install git: `brew install git` (Mac) or `sudo apt install git` (Linux) |
| No internet | Check WiFi/ethernet, try `ping github.com` |
| GitHub not accessible | Check firewall, try in browser: https://github.com |
| No write permissions | Run `chmod -R u+w .` or check file ownership |
| Disk space low | Free up space: delete old backups, clear logs |
| Concurrent update | Run `bash scripts/unlock_update.sh` |
| Git not clean | Run `bash scripts/cleanup_failed_update.sh` |

---

### Update Fails: "Failed to Download"

**Problem:** Git pull fails during update.

**Possible Causes:**
1. Network timeout
2. GitHub down
3. Git conflicts
4. Permission issues

**Solutions:**

```bash
# Check GitHub status
curl -I https://api.github.com

# Try manual git pull
git fetch origin main
git pull origin main

# If conflicts
git stash
git pull origin main
git stash pop

# If persistent issues
bash scripts/cleanup_failed_update.sh
```

---

### Update Fails: "Dependency Installation Failed"

**Problem:** pip install fails.

**Diagnosis:**
```bash
pip3 install -r requirements.txt
```

**Common Issues:**

1. **Python Version Too Old:**
   ```bash
   python3 --version  # Need 3.8+
   # Upgrade Python if needed
   ```

2. **pip Not Updated:**
   ```bash
   python3 -m pip install --upgrade pip
   pip3 install -r requirements.txt
   ```

3. **Conflicting Packages:**
   ```bash
   pip3 install -r requirements.txt --force-reinstall
   ```

4. **No Internet:**
   - Wait for connection
   - Use cached wheels: `pip3 install -r requirements.txt --no-index --find-links ~/pip-cache/`

---

### Update Fails: "Bot Won't Restart"

**Problem:** Bot process fails to start after update.

**Diagnosis:**
```bash
# Try starting manually
python3 bot.py

# Check for errors
tail -50 logs/errors.log
```

**Common Causes:**

1. **Import Error:**
   ```bash
   # Missing dependency
   pip3 install -r requirements.txt
   
   # Corrupted module
   pip3 install --force-reinstall <module_name>
   ```

2. **Config Error:**
   ```bash
   # Validate YAML
   python3 -c "import yaml; yaml.safe_load(open('config.yaml'))"
   
   # Restore from backup
   cp backups/backup_latest/config.yaml .
   ```

3. **Permission Error:**
   ```bash
   # Fix permissions
   chmod +x bot.py
   chmod -R u+w logs/ state/ database/
   ```

4. **Port Already in Use:**
   ```bash
   # Find process using port
   lsof -i:5000
   
   # Kill it
   kill -9 <PID>
   ```

---

## Process Management Issues

### Bot Process Won't Stop

**Problem:** `force_stop.sh` doesn't stop the bot.

**Solutions:**

```bash
# Find process ID
ps aux | grep "python.*bot"

# Force kill
kill -9 <PID>

# Or kill all Python processes (⚠️ careful!)
pkill -9 python3

# Clean up PID files
rm -f .bot.pid .dashboard.pid
```

---

### Bot Starts Then Immediately Exits

**Problem:** Process starts but exits within seconds.

**Diagnosis:**
```bash
# Run in foreground to see errors
python3 bot.py
```

**Common Causes:**

1. **Missing Config:**
   ```bash
   # Check if config exists
   ls -lh config.yaml
   
   # Create from example
   cp config.example.yaml config.yaml
   # Edit with your settings
   ```

2. **Database Locked:**
   ```bash
   # Remove lock
   rm -f database/*.lock
   
   # Reset database (⚠️ loses data)
   rm -f database/*.db
   ```

3. **Import Error:**
   - Check logs: `tail -50 logs/errors.log`
   - Reinstall dependencies: `pip3 install -r requirements.txt --force-reinstall`

---

## Git Issues

### "Local Changes" Error During Update

**Problem:** Git won't pull because of local changes.

**Solutions:**

```bash
# See what changed
git status
git diff

# Option 1: Save changes
git stash save "my-changes-backup"
# (Update will now work)
# Later: git stash pop

# Option 2: Discard changes
git checkout -- .
git clean -fd

# Option 3: Use cleanup script
bash scripts/cleanup_failed_update.sh
```

---

### Git Says "Not a Repository"

**Problem:** Git commands fail.

**Cause:** Not in git repository or .git corrupted.

**Solutions:**

```bash
# Check if .git exists
ls -la .git

# If missing, reinitialize
git init
git remote add origin https://github.com/AlexMeisenzahl/market-strategy-testing-bot.git
git fetch origin
git checkout main

# If corrupted
mv .git .git.backup
git clone https://github.com/AlexMeisenzahl/market-strategy-testing-bot.git temp
mv temp/.git .
rm -rf temp
```

---

## Network Issues

### Update Fails: "Connection Timeout"

**Problem:** Network requests timeout.

**Solutions:**

1. **Check Internet:**
   ```bash
   ping -c 3 github.com
   curl -I https://api.github.com
   ```

2. **Check Firewall:**
   - Allow git/python/curl through firewall
   - Try from different network

3. **Use Manual Update:**
   ```bash
   # Download as ZIP, extract, run:
   bash scripts/manual_update.sh
   ```

4. **Increase Timeout:**
   ```bash
   git config --global http.lowSpeedLimit 1000
   git config --global http.lowSpeedTime 600
   ```

---

### GitHub API Rate Limited

**Problem:** Too many requests to GitHub API.

**Solution:**

```bash
# Wait 1 hour, or use personal access token
git config --global github.token YOUR_TOKEN
```

---

## Permission Issues

### "Permission Denied" Errors

**Problem:** Can't write to files/directories.

**Solutions:**

```bash
# Fix ownership
sudo chown -R $USER:$USER .

# Fix permissions
chmod -R u+w .
chmod +x *.sh scripts/*.sh

# For specific directories
chmod -R 755 logs/ state/ database/ backups/
```

---

## Database Issues

### Database Corrupted

**Problem:** SQLite database errors.

**Solutions:**

```bash
# Backup current DB
cp database/bot.db database/bot.db.corrupt

# Restore from backup
cp backups/backup_latest/database/bot.db database/

# Or start fresh (⚠️ loses data)
rm database/bot.db
python3 bot.py  # Will recreate
```

---

### Database Locked

**Problem:** "Database is locked" error.

**Solutions:**

```bash
# Stop all processes
bash scripts/force_stop.sh

# Remove lock files
find database/ -name "*.lock" -delete

# Restart
python3 start_dashboard.py
```

---

## Dependency Issues

### Module Not Found

**Problem:** `ImportError: No module named 'xxx'`

**Solutions:**

```bash
# Reinstall all dependencies
pip3 install -r requirements.txt

# Reinstall specific module
pip3 install --force-reinstall <module_name>

# Check which Python pip is using
which python3
which pip3
# Make sure they match!

# Use virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

### Version Conflicts

**Problem:** Package version incompatibilities.

**Solutions:**

```bash
# Clean install
pip3 uninstall -y -r requirements.txt
pip3 install -r requirements.txt

# Or use virtual environment
python3 -m venv venv_new
source venv_new/bin/activate
pip install -r requirements.txt
```

---

## Port Conflicts

### Port 5000 Already in Use

**Problem:** Can't start dashboard on port 5000.

**Solutions:**

```bash
# Find what's using the port
lsof -i:5000

# Kill that process
kill -9 <PID>

# Or use different port (edit start_dashboard.py)
# Change: app.run(port=5001)
```

---

## macOS Specific Issues

### "Command Not Found" in Scripts

**Problem:** Scripts can't find commands.

**Solution:**

```bash
# Install Xcode command line tools
xcode-select --install

# Install Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install tools
brew install git python3
```

---

### Security / Gatekeeper Issues

**Problem:** macOS won't run scripts.

**Solution:**

```bash
# Make executable
chmod +x scripts/*.sh

# Allow in System Preferences > Security & Privacy

# Or remove quarantine
xattr -d com.apple.quarantine scripts/*.sh
```

---

## Still Having Issues?

### Collect Diagnostic Info

```bash
# Run all diagnostics
bash scripts/test_update_system.sh > diagnostics.txt
bash scripts/health_check_enhanced.sh >> diagnostics.txt
python3 --version >> diagnostics.txt
pip3 list >> diagnostics.txt
git status >> diagnostics.txt

# Collect logs
tail -100 logs/errors.log > recent_errors.txt
tail -100 logs/bot.log > recent_bot_log.txt
```

### Create GitHub Issue

Include:
- What you were trying to do
- Error message (exact text)
- Output from diagnostics.txt
- Output from recent_errors.txt
- Your OS and Python version

### Quick Fixes to Try

1. **Restart Everything:**
   ```bash
   bash scripts/force_stop.sh
   sleep 3
   python3 start_dashboard.py
   ```

2. **Rollback:**
   ```bash
   bash scripts/emergency_rollback.sh
   ```

3. **Clean Install:**
   ```bash
   bash scripts/cleanup_failed_update.sh
   pip3 install -r requirements.txt --force-reinstall
   python3 start_dashboard.py
   ```

4. **Nuclear Option:**
   See EMERGENCY_RECOVERY.md "Everything is Broken" section
