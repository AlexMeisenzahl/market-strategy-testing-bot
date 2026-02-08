# Pre-Update Checklist

Complete this checklist before starting any update.

---

## Essential Checks (Must Pass)

- [ ] **No Active Trades**
  - Check dashboard: "Active Positions" = 0
  - Or: Ready to pause/close positions
  - If trading live: Close positions or wait

- [ ] **Stable Internet Connection**
  - Test: `ping -c 10 github.com`
  - All packets received (0% loss)
  - Wired connection preferred over WiFi

- [ ] **1GB+ Free Disk Space**
  - Check: `df -h .`
  - Need space for backup + download
  - Clean old backups if needed: `ls -lh backups/`

- [ ] **Bot Running Stable 1+ Hour**
  - No recent crashes
  - No errors in logs
  - Dashboard accessible

- [ ] **5-10 Minutes Available**
  - Time to monitor update
  - Don't start update and leave
  - Can respond if issues occur

- [ ] **Know Emergency Scripts Location**
  - `ls scripts/`
  - Emergency rollback: `scripts/emergency_rollback.sh`
  - Force stop: `scripts/force_stop.sh`

---

## Recommended (Best Practice)

- [ ] **Manual Config Backup** *(Extra safety)*
  ```bash
  cp config.yaml config.backup.$(date +%Y%m%d).yaml
  ```

- [ ] **Check Recent Errors**
  ```bash
  tail -50 logs/errors.log
  # Should be mostly clean
  ```

- [ ] **Test Update System**
  ```bash
  bash scripts/test_update_system.sh
  # All checks should pass
  ```

- [ ] **Read Changelog**
  - Check what's new in update
  - Any breaking changes?
  - New requirements?

- [ ] **Off-Peak Trading Time**
  - Not during major market events
  - Not during high-value trades
  - Morning/afternoon better than evening

---

## Advanced (Optional)

- [ ] **Full Manual Backup**
  ```bash
  tar -czf manual_backup_$(date +%Y%m%d).tar.gz \
      *.py config.yaml services/ dashboard/ database/ state/
  ```

- [ ] **Python Version Check**
  ```bash
  python3 --version  # Should be 3.8+
  ```

- [ ] **Dependencies Up to Date**
  ```bash
  pip3 list --outdated
  ```

- [ ] **Git Status Clean**
  ```bash
  git status
  # Should show "working tree clean"
  ```

---

## Quick Pre-Flight

Run this one command for quick check:

```bash
bash scripts/test_update_system.sh
```

**All tests pass?** ✅ Ready to update!

**Any tests fail?** ❌ Fix issues first (see TROUBLESHOOTING.md)

---

## During Update

- [ ] **Watch Progress**
  - Don't close dashboard
  - Progress should move every 10-30 seconds
  - Typical update: 1-3 minutes

- [ ] **Don't Interrupt**
  - No force-quit
  - No system restart
  - Let it complete or use Cancel button

- [ ] **Note Any Errors**
  - Screenshot error messages
  - Copy error text
  - Will help with recovery if needed

---

## After Update

- [ ] **Verify Bot Running**
  ```bash
  bash scripts/health_check_enhanced.sh
  ```

- [ ] **Check Dashboard**
  - Access: http://localhost:5000
  - All pages load
  - No errors shown

- [ ] **Check Version**
  - Dashboard shows new version
  - Or: `cat VERSION`

- [ ] **Monitor for 5-10 Minutes**
  - Watch for errors in logs
  - Check bot behavior normal
  - Verify strategies working

- [ ] **Resume Trading** *(if was paused)*
  - Only after confirming stable
  - Test with small position first

---

## If Update Fails

Don't panic! You have backups.

```bash
# Rollback immediately
bash scripts/emergency_rollback.sh

# Or restore specific backup
bash scripts/restore_backup.sh backup_20240208_101533
```

See UPDATE_FAILURE_GUIDE.md for specific scenarios.

---

## Update Decision Tree

```
Ready to Update?
├─ Active trades? 
│  ├─ Yes → Wait or close positions
│  └─ No → ✓
├─ Good internet?
│  ├─ No → Wait for stable connection  
│  └─ Yes → ✓
├─ 1GB+ disk space?
│  ├─ No → Free up space
│  └─ Yes → ✓
├─ Bot stable?
│  ├─ No → Fix issues first
│  └─ Yes → ✓
├─ Have 5-10 minutes?
│  ├─ No → Update later
│  └─ Yes → ✓
└─ All ✓ → START UPDATE
```

---

## Print This Checklist

```
PRE-UPDATE CHECKLIST
====================

Essential:
☐ No active trades
☐ Stable internet (ping github.com)
☐ 1GB+ disk space (df -h)
☐ Bot stable 1+ hour
☐ 5-10 minutes available
☐ Know emergency scripts

Recommended:
☐ Backup config.yaml
☐ Check logs clean
☐ Read changelog
☐ Off-peak time

Quick Check:
bash scripts/test_update_system.sh

Emergency Commands:
bash scripts/emergency_rollback.sh
bash scripts/force_stop.sh
bash scripts/health_check_enhanced.sh
```

---

**Remember:** Updates are never automatic. You always control when to update.
