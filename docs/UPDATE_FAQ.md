# Update System FAQ

Frequently asked questions about the auto-update system.

---

## General Questions

### Q: Are updates automatic?

**A:** No! Updates are never automatic. You always control when to update through the dashboard. The system only checks for available updates and notifies you.

### Q: How often does it check for updates?

**A:** The dashboard checks for updates every 6 hours when loaded. You can also manually check anytime by clicking the update icon.

### Q: Can I disable update notifications?

**A:** Yes, click "Dismiss" on the update banner. It won't show again until you reload the dashboard. For permanent disable, you'd need to modify the code.

### Q: Is my data safe during updates?

**A:** Yes! Every update creates an automatic backup before making any changes. If anything goes wrong, automatic rollback restores your backup.

---

## Before Updating

### Q: Can I update with open trading positions?

**A:** Technically yes, but not recommended. The bot restarts during update (1-2 minutes downtime). Active trades are saved in state files and resume after restart, but you might miss price movements. Best practice: Close positions first.

### Q: Can I update on bad internet?

**A:** Not recommended. The update downloads files from GitHub. If your connection fails mid-update, the rollback system will restore your backup, but it's better to wait for stable internet.

### Q: What if GitHub is down?

**A:** The pre-flight check will detect this and prevent the update from starting. Wait until GitHub is back up. Check status: https://www.githubstatus.com

### Q: How much disk space do I need?

**A:** Minimum 1GB free space. The backup takes 50-100MB, and the download is 10-20MB. Pre-flight checks verify disk space before starting.

---

## During Updates

### Q: How long does an update take?

**A:** Typical update: 1-3 minutes. Breakdown:
- Pre-flight checks: 5-10 seconds
- Backup: 10-20 seconds
- Download: 20-60 seconds (depends on internet speed)
- Dependencies: 20-60 seconds
- Restart: 10-20 seconds
- Verification: 5-10 seconds

### Q: Can I cancel an update?

**A:** Yes, click "Cancel Update" in the dashboard. The system will stop and clean up safely. However, it's often faster to let it complete than to cancel and cleanup.

### Q: What if my computer crashes during update?

**A:** Run the recovery script when it restarts:
```bash
bash scripts/emergency_rollback.sh
```
This restores your last backup.

### Q: What if I lose power during update?

**A:** Same as computer crash. Run emergency rollback when power returns. Your backup is safe on disk.

---

## After Updates

### Q: How do I know if the update succeeded?

**A:** The dashboard will show "Update Complete" and display the new version number. The bot will be running and responding. You can also run: `bash scripts/health_check_enhanced.sh`

### Q: What if the new version has bugs?

**A:** Rollback to previous version:
```bash
bash scripts/emergency_rollback.sh
```
Then report the bug on GitHub Issues.

### Q: Can I test updates before going live?

**A:** Yes! Use paper trading mode to test new versions before switching to live trading. Or run a test instance in a separate directory.

### Q: Are my old backups deleted?

**A:** The system keeps your 5 most recent backups automatically. Older backups are deleted to save disk space. You can manually save specific backups by copying them elsewhere.

---

## Backups

### Q: Where are backups stored?

**A:** In the `backups/` directory, named like `backup_20240208_101533/` (date and time).

### Q: How do I manually backup?

**A:** Copy important files:
```bash
cp config.yaml config.backup.yaml
tar -czf manual_backup.tar.gz *.py config.yaml services/ dashboard/
```

### Q: Can I restore old backups?

**A:** Yes!
```bash
# List backups
ls -lh backups/

# Restore specific backup
bash scripts/restore_backup.sh backup_20240208_101533
```

### Q: Are backups safe long-term?

**A:** Backups are complete snapshots but not compressed. They're safe as long as your disk is safe. For long-term storage, compress them:
```bash
tar -czf backup_20240208.tar.gz backups/backup_20240208_101533/
```

### Q: Do backups include my data/trades?

**A:** Yes! Backups include: code, config, database, state files, and logs.

---

## Troubleshooting

### Q: Update failed, what do I do?

**A:** Run emergency rollback:
```bash
bash scripts/emergency_rollback.sh
```
See UPDATE_FAILURE_GUIDE.md for specific scenarios.

### Q: Bot won't start after update

**A:** Rollback first, then investigate:
```bash
bash scripts/emergency_rollback.sh
tail -50 logs/errors.log  # Check what went wrong
```

### Q: How do I get help?

**A:** 
1. Check documentation: EMERGENCY_RECOVERY.md, TROUBLESHOOTING.md
2. Run diagnostics: `bash scripts/health_check_enhanced.sh`
3. Create GitHub Issue with error logs
4. Include: What you did, error message, output of health check

### Q: Can I manually update instead?

**A:** Yes! Use the manual update script:
```bash
bash scripts/manual_update.sh
```
This guides you step-by-step with prompts at each stage.

---

## Advanced

### Q: Can I schedule updates?

**A:** Not built-in, but you could add a cron job to check for updates. However, automatic updates are not recommended - always monitor updates manually.

### Q: How do I update offline?

**A:** Download the code as ZIP from GitHub, extract it, then manually copy files. Or use `git bundle` to package updates offline.

### Q: Can I skip a version?

**A:** Yes, updates pull the latest from GitHub. You can skip intermediate versions safely. Backups are always created.

### Q: What if I edited the code?

**A:** Git will detect local changes and either stash them or fail. Use the cleanup script:
```bash
bash scripts/cleanup_failed_update.sh
```

### Q: How do I disable auto-update checks entirely?

**A:** Comment out version checking in `dashboard/app.py`:
```python
# version_manager = VersionManager(BASE_DIR)
```

Or set check interval to very long in dashboard JavaScript.

---

## Security

### Q: Is the update system secure?

**A:** Updates come directly from GitHub via git pull. Git uses HTTPS and verifies the repository. Updates don't execute arbitrary code - they're just your repo's latest code.

### Q: Can someone hijack my updates?

**A:** No, because:
- Updates pull from authenticated GitHub repo
- Git verifies signatures
- No remote code execution
- All code runs locally

### Q: Should I review updates before installing?

**A:** Yes, good practice:
1. Read the release notes on GitHub
2. Check changed files
3. Test in paper trading first
4. Keep a manual backup

---

## Compatibility

### Q: Do updates work on Windows?

**A:** The Python code works on Windows, but bash scripts need Git Bash or WSL. Main update system works, emergency scripts may need adaptation.

### Q: Do updates work on Linux?

**A:** Yes, fully supported. All scripts work natively.

### Q: Do updates work on Mac?

**A:** Yes, fully tested on macOS. All scripts work natively with macOS commands.

### Q: What Python versions are supported?

**A:** Python 3.8+. Check your version: `python3 --version`. See docs/PYTHON_UPGRADE.md for upgrade guide.

---

## Best Practices

### Q: When is the best time to update?

**A:**
- No active trades
- Off-peak trading hours
- Stable internet connection
- When you have 10 minutes to monitor
- After reading changelog

### Q: Should I update immediately?

**A:** Not necessarily. Wait a few days for:
- Bug reports from other users
- Hot fixes if needed
- Time to read changelog thoroughly

### Q: How often should I update?

**A:** 
- Security updates: ASAP
- Bug fixes: Within a week
- New features: When convenient
- Major versions: Test first

---

## Support

### Q: Where do I report bugs?

**A:** GitHub Issues: https://github.com/AlexMeisenzahl/market-strategy-testing-bot/issues

Include:
- Error message
- Steps to reproduce
- Output of `bash scripts/health_check_enhanced.sh`
- Recent logs from `logs/errors.log`

### Q: How do I request features?

**A:** Same place - GitHub Issues, tag as "enhancement"

### Q: Is there a Discord/Slack?

**A:** Check README.md for community links

---

## Quick Reference

**Check for updates:** Dashboard shows notification automatically

**Start update:** Click "Update Now" button in dashboard

**Cancel update:** Click "Cancel" button during update

**Rollback:** `bash scripts/emergency_rollback.sh`

**Health check:** `bash scripts/health_check_enhanced.sh`

**Manual update:** `bash scripts/manual_update.sh`

**Get help:** See EMERGENCY_RECOVERY.md and TROUBLESHOOTING.md
