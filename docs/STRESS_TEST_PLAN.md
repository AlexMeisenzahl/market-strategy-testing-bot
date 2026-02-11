# Stress Test Plan — Market Strategy Testing Bot

This document defines shell-based stress tests, long-run memory observation, crash injection, network interruption, and numpy failure simulation. **No application code is modified**; only environment, external tools, and procedures are used.

---

## Prerequisites

- Run all commands from the **project root** unless stated otherwise.
- Set a dedicated stress environment so production state/logs are not touched. Use `STRESS_DIR` to choose where artifacts go (default: `/tmp/bot_stress_<pid>`; use e.g. `./stress_artifacts` for in-project inspection):

```bash
export PROJECT_ROOT="$(pwd)"
export STRESS_DIR="${STRESS_DIR:-/tmp/bot_stress_$$}"
export STRESS_STATE="${STRESS_DIR}/state"
export STRESS_LOG="${STRESS_DIR}/logs"
mkdir -p "$STRESS_STATE" "$STRESS_LOG"
```

- Ensure the bot can run headless (no live API required for most tests): use default config with paper trading; mock clients will be used if APIs are not configured.

---

## 1. Shell-Based Stress Tests

### 1.1 Rapid restart cycles

**Goal:** Verify state survives repeated restarts and that no stale file handles or corrupt state accumulate.

**Strategy:** Start the bot with a short cycle and a fixed cycle count; kill it after a few seconds (before natural exit); restart immediately; repeat. After N cycles, check that state files are valid and that one more run completes without error.

**Commands:**

```bash
# Setup
export STATE_DIR="$STRESS_STATE" LOG_DIR="$STRESS_LOG"
export SCAN_INTERVAL_SECONDS=5 MAX_CYCLES=10

# Run 20 restart cycles: start, wait 8s, kill -15 (SIGTERM), restart
for i in $(seq 1 20); do
  echo "=== Restart cycle $i ==="
  python main.py &
  PID=$!
  sleep 8
  kill -15 $PID 2>/dev/null || true
  wait $PID 2>/dev/null || true
  sleep 1
done

# Validation: state and paper engine state should exist and be valid JSON
python3 -c "
import json
from pathlib import Path
s = Path('$STRESS_STATE')
for name in ['bot_state.json', 'paper_engine_state.json', 'engine_health.json']:
  p = s / name
  if p.exists():
    try:
      json.loads(p.read_text())
      print(f'OK {name}')
    except Exception as e:
      print(f'INVALID {name}: {e}')
  else:
    print(f'MISSING {name}')
"

# Final run: should complete without crash (e.g. 5 cycles then exit)
MAX_CYCLES=5 python main.py
echo "Exit code: $?"
```

**Pass criteria:** No INVALID or persistent crash on final run; exit code 0 for the final `MAX_CYCLES=5` run.

---

### 1.2 High-frequency engine cycles

**Goal:** Stress the main loop, state writes, and SQLite/logger under many cycles in a short wall-clock time.

**Strategy:** Use the smallest practical scan interval and a high cycle cap; run for a fixed duration or until MAX_CYCLES; watch for OOM, disk full, or SQLite errors in logs.

**Commands:**

```bash
export STATE_DIR="$STRESS_STATE" LOG_DIR="$STRESS_LOG"
# 2-second cycle; 500 cycles => ~1000s of work compressed into fast cycles
export SCAN_INTERVAL_SECONDS=2 MAX_CYCLES=500 CYCLE_TIMEOUT_SECONDS=60

time python main.py
echo "Exit code: $?"

# Sanity: logs and state updated
ls -la "$STRESS_LOG"/activity.json "$STRESS_STATE"/bot_state.json 2>/dev/null || true
tail -5 "$STRESS_LOG"/errors.log 2>/dev/null || true
```

**Pass criteria:** Process exits with 0 (or 130 if you Ctrl+C); no repeated Python tracebacks in errors.log; state and activity files present and updated.

---

### 1.3 Corrupted state file

**Goal:** Ensure the bot does not crash on invalid or truncated state and falls back to defaults or backup.

**Scenarios to run separately:**

**A) Corrupt `state/bot_state.json`**

```bash
export STATE_DIR="$STRESS_STATE" LOG_DIR="$STRESS_LOG"
mkdir -p "$STRESS_STATE"

# Invalid JSON
echo '{"balance": ' > "$STRESS_STATE/bot_state.json"

# Run for a few cycles; bot should not crash (state write is best-effort)
MAX_CYCLES=3 SCAN_INTERVAL_SECONDS=5 python main.py
echo "Exit code: $?"
```

**B) Corrupt `state/paper_engine_state.json`**

```bash
echo 'not json at all' > "$STRESS_STATE/paper_engine_state.json"
# Remove backup so there is no fallback
rm -f "$STRESS_STATE/paper_engine_state.backup.json"

MAX_CYCLES=3 SCAN_INTERVAL_SECONDS=5 python main.py
echo "Exit code: $?"
```

**C) Empty file**

```bash
touch "$STRESS_STATE/bot_state.json"
MAX_CYCLES=2 python main.py
echo "Exit code: $?"
```

**Pass criteria:** Process exits 0 (or 130); no unhandled exception; logs may show warnings about invalid/missing state; next run overwrites state.

---

### 1.4 Disk full scenario

**Goal:** Trigger ENOSPC during state or log write and observe that the bot does not crash hard and that errors are logged or handled.

**Strategy:** Point STATE_DIR and LOG_DIR to a small tmpfs (Linux/macOS) or a small disk image; run until writes fail. Alternatively, fill the target directory until the filesystem has no free space.

**Linux (tmpfs, 1MB — fills quickly):**

```bash
export STRESS_MNT="${STRESS_DIR}/mnt"
mkdir -p "$STRESS_MNT"
sudo mount -t tmpfs -o size=1M tmpfs "$STRESS_MNT" 2>/dev/null || true
export STATE_DIR="$STRESS_MNT/state" LOG_DIR="$STRESS_MNT/logs"
mkdir -p "$STATE_DIR" "$LOG_DIR"

# Run; expect failure when disk full (may see OSError in log or silent skip)
MAX_CYCLES=20 SCAN_INTERVAL_SECONDS=2 python main.py
echo "Exit code: $?"
cat "$LOG_DIR/errors.log" 2>/dev/null | tail -20

sudo umount "$STRESS_MNT" 2>/dev/null || true
```

**macOS / portable (fill a directory in a small loop until df shows full):**

```bash
# Use a small sparse/file-based volume if available, or a subdir with quota.
# Generic: fill LOG_DIR with junk until write fails
export STATE_DIR="$STRESS_STATE" LOG_DIR="$STRESS_LOG"
mkdir -p "$LOG_DIR"
# Write 50MB of junk into logs dir to put pressure on small volumes
dd if=/dev/zero of="$LOG_DIR/fill.bin" bs=1M count=50 2>/dev/null || true
MAX_CYCLES=5 python main.py
echo "Exit code: $?"
rm -f "$LOG_DIR/fill.bin" 2>/dev/null
```

**Pass criteria:** Process either exits non-zero with a logged error or continues with some writes failing; no unhandled exception; log file contains evidence of write failure if applicable.

---

### 1.5 Slow I/O simulation

**Goal:** Increase likelihood of partial writes or lock timeouts so that atomic/lock behavior can be observed.

**Strategy:** Run state and logs on a slow or remote filesystem (e.g. NFS with high latency, or a FUSE filesystem that adds delay). Without modifying code, use external means to slow I/O.

**Option A — Network filesystem (if available):**  
Mount an NFS share with high latency (e.g. over a throttled link) and set:

```bash
export STATE_DIR=/path/to/slow_nfs/state LOG_DIR=/path/to/slow_nfs/logs
MAX_CYCLES=10 SCAN_INTERVAL_SECONDS=10 python main.py
```

**Option B — Loop device with slow backing (Linux):**  
Use `dm-delay` or a slow block device if available (advanced).

**Option C — Resource throttling (affects CPU, not pure I/O):**  
Run under `nice` and/or `ionice` so the process is deprioritized; I/O may appear slower under load:

```bash
export STATE_DIR="$STRESS_STATE" LOG_DIR="$STRESS_LOG"
# Best-effort: slow down process so that lock hold times may be longer
nice -n 19 ionice -c 3 python main.py &
PID=$!
# Run high-frequency cycles in parallel to create contention
MAX_CYCLES=30 SCAN_INTERVAL_SECONDS=3
sleep 60
kill -15 $PID 2>/dev/null || true
```

**Pass criteria:** Bot completes or is stopped cleanly; no corrupt state files (validate JSON); logs may show lock timeouts.

---

### 1.6 Log file saturation

**Goal:** Force log rotation and high churn in the logs directory; check for handle leaks, rotation races, or unbounded growth.

**Strategy:** Pre-create large or many log files, or lower the effective capacity by creating a small tmpfs for LOG_DIR and running many cycles.

**A) Many and large files in LOG_DIR:**

```bash
export LOG_DIR="$STRESS_LOG" STATE_DIR="$STRESS_STATE"
mkdir -p "$LOG_DIR"
# Create 100 fake log files (10MB each = 1GB) if space allows; otherwise fewer/smaller
for i in $(seq 1 100); do
  dd if=/dev/urandom of="$LOG_DIR/prefill_$i.log" bs=1M count=10 2>/dev/null || break
done
# Run bot; it will rotate errors.log/connection.log and write activity.json
MAX_CYCLES=15 SCAN_INTERVAL_SECONDS=3 python main.py
echo "Exit code: $?"
ls -la "$LOG_DIR"
```

**B) Small tmpfs to force rotation (Linux):**

```bash
sudo mount -t tmpfs -o size=20M tmpfs "$STRESS_DIR/log_mnt" 2>/dev/null || true
export LOG_DIR="$STRESS_DIR/log_mnt" STATE_DIR="$STRESS_STATE"
mkdir -p "$LOG_DIR" "$STRESS_STATE"
# RotatingFileHandler 10MB x 5 = 50MB; 20MB tmpfs will fill
MAX_CYCLES=30 SCAN_INTERVAL_SECONDS=2 python main.py
echo "Exit code: $?"
sudo umount "$STRESS_DIR/log_mnt" 2>/dev/null || true
```

**Pass criteria:** No crash; rotation and pruning occur; no unbounded growth beyond configured limits; exit code 0 or 130.

---

## 2. Long-Run Memory Observation Procedure

**Goal:** Detect memory growth (e.g. list/dict/cache growth, connection leaks) over many hours.

**Procedure:**

1. **Isolate state and logs** so a long run does not affect production:

   ```bash
   export STATE_DIR="$STRESS_STATE" LOG_DIR="$STRESS_LOG"
   mkdir -p "$STRESS_STATE" "$STRESS_LOG"
   ```

2. **Start the bot in the background** with a high cycle limit or unlimited:

   ```bash
   export SCAN_INTERVAL_SECONDS=60 MAX_CYCLES=   # empty = unlimited
   python main.py > "$STRESS_DIR/bot_stdout.txt" 2>&1 &
   BOT_PID=$!
   echo $BOT_PID > "$STRESS_DIR/bot.pid"
   ```

3. **Sample RSS (and optionally VSZ) periodically** (e.g. every 5 minutes for 6+ hours):

   ```bash
   # Linux
   while kill -0 $BOT_PID 2>/dev/null; do
     ps -o pid,rss,vsz,etime -p $BOT_PID 2>/dev/null | tail -1
     date -Iseconds
     sleep 300
   done >> "$STRESS_DIR/memory_log.txt"

   # macOS (RSS in KB; convert to MB for comparison)
   while kill -0 $BOT_PID 2>/dev/null; do
     ps -o pid,rss,vsz,etime -p $BOT_PID 2>/dev/null | tail -1
   date -Iseconds
   sleep 300
   done >> "$STRESS_DIR/memory_log.txt"
   ```

4. **Optional: use a small script to log RSS in MB** (run in another terminal):

   ```bash
   BOT_PID=$(cat "$STRESS_DIR/bot.pid")
   while true; do
     [ ! -d /proc/$BOT_PID ] && break
     rss=$(awk '/VmRSS/ {print $2}' /proc/$BOT_PID/status 2>/dev/null)  # KB
     echo "$(date -Iseconds) $((rss/1024))" >> "$STRESS_DIR/rss_mb.txt"
     sleep 300
   done
   ```

5. **Stop after desired duration** (e.g. 6–24 hours):

   ```bash
   kill -15 $BOT_PID
   wait $BOT_PID 2>/dev/null
   ```

6. **Analyze** `memory_log.txt` or `rss_mb.txt`: plot RSS over time; flag monotonic growth beyond a small drift (e.g. >20% over 6 hours without plateau).

**Pass criteria:** RSS stabilizes or has only minor drift; no sustained upward trend over 6+ hours.

---

## 3. Crash Injection Procedure

**Goal:** Verify recovery after abrupt termination (SIGKILL, SIGTERM, SIGINT) and optional corruption of state during write.

**3.1 SIGTERM (graceful)**

```bash
export STATE_DIR="$STRESS_STATE" LOG_DIR="$STRESS_LOG"
MAX_CYCLES=9999 SCAN_INTERVAL_SECONDS=5 python main.py &
PID=$!
sleep 12
kill -15 $PID
wait $PID 2>/dev/null
echo "Exit code: $?"
# Check state written
cat "$STRESS_STATE/bot_state.json" | python3 -m json.tool >/dev/null && echo "bot_state valid"
```

**3.2 SIGINT (Ctrl+C)**

```bash
python main.py &
PID=$!
sleep 10
kill -2 $PID
wait $PID 2>/dev/null
echo "Exit code (expect 0): $?"
```

**3.3 SIGKILL during cycle (no graceful shutdown)**

```bash
export STATE_DIR="$STRESS_STATE" LOG_DIR="$STRESS_LOG"
MAX_CYCLES=9999 SCAN_INTERVAL_SECONDS=3 python main.py &
PID=$!
sleep 7
kill -9 $PID
wait $PID 2>/dev/null
# Restart and run a few cycles; should not crash
sleep 2
MAX_CYCLES=5 python main.py
echo "Exit code: $?"
```

**3.4 Kill during state write (best-effort)**

Run the bot and kill it repeatedly at short intervals so that some kills land during `_write_bot_state` / `_save_paper_engine_state`:

```bash
for i in 1 2 3 4 5 6 7 8 9 10; do
  MAX_CYCLES=99 SCAN_INTERVAL_SECONDS=2 python main.py &
  PID=$!
  sleep 3
  kill -9 $PID 2>/dev/null
  wait $PID 2>/dev/null
  sleep 1
done
# Next run must not crash (may restore from backup or start fresh)
MAX_CYCLES=3 python main.py
echo "Exit code: $?"
python3 -c "
import json
from pathlib import Path
for f in ['bot_state.json','paper_engine_state.json']:
  p = Path('$STRESS_STATE')/f
  if p.exists():
    try: json.loads(p.read_text()); print(f'{f} valid')
    except Exception as e: print(f'{f} invalid: {e}')
"
```

**Pass criteria:** After SIGTERM/SIGINT, exit code 0 and state valid. After SIGKILL, next run exits 0; state files either valid or recreated without crash.

---

## 4. Network Interruption Simulation

**Goal:** See behavior when Polymarket/CoinGecko (and optional Telegram) are unreachable; confirm fallback to mock data and no hard crash.

**4.1 Block by hostname (requires root or net admin)**

**Linux (iptables):**

```bash
# Block outbound to Polymarket and CoinGecko
sudo iptables -A OUTPUT -p tcp -d clob.polymarket.com -j DROP
sudo iptables -A OUTPUT -p tcp -d api.coingecko.com -j DROP
# Run bot; expect mock fallback after timeout
export STATE_DIR="$STRESS_STATE" LOG_DIR="$STRESS_LOG"
MAX_CYCLES=5 SCAN_INTERVAL_SECONDS=10 python main.py
echo "Exit code: $?"
# Restore
sudo iptables -D OUTPUT -p tcp -d clob.polymarket.com -j DROP
sudo iptables -D OUTPUT -p tcp -d api.coingecko.com -j DROP
```

**macOS (pf):**  
Add a rule to block the relevant hostnames or IPs, then run the same bot command; remove rule after test.

**4.2 Block by local proxy (no root)**

Use a proxy that drops connections or returns errors. Example with a minimal Python proxy (save as `stress_proxy.py` in a scratch dir, run in background):

```python
# stress_proxy.py - bind 127.0.0.1:8888, accept and close (connection refused effect)
import socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(('127.0.0.1', 8888))
s.listen(5)
while True:
    c, _ = s.accept()
    c.close()
```

Then run the bot with that proxy; API clients must be configured to use the proxy (if the app supports `HTTP_PROXY`/`HTTPS_PROXY`):

```bash
export HTTP_PROXY=http://127.0.0.1:8888 HTTPS_PROXY=http://127.0.0.1:8888
export STATE_DIR="$STRESS_STATE" LOG_DIR="$STRESS_LOG"
MAX_CYCLES=3 SCAN_INTERVAL_SECONDS=15 python main.py
unset HTTP_PROXY HTTPS_PROXY
```

**4.3 Physical/unplug (manual)**

Unplug network or disable WiFi for 30–60 seconds while the bot is running; re-enable and verify next cycle recovers (mock or real data) and no crash.

**Pass criteria:** Bot keeps running; logs show connection/API errors and fallback to mock data; exit code 0 when stopped normally.

---

## 5. Numpy Failure Simulation

**Goal:** Trigger a failure at numpy import (or first use) so that code paths that lazily import numpy are exercised under failure; ensure the process fails safely (no silent wrong math).

**Strategy:** Prepend a fake `numpy` package to `PYTHONPATH` that raises on import. Then run the bot (or a specific entry point that eventually imports numpy in the app).

**5.1 Create a fake numpy package (outside project tree)**

```bash
export FAKE_NUMPY_DIR="$STRESS_DIR/fake_numpy"
mkdir -p "$FAKE_NUMPY_DIR"
# Fake numpy that raises on import
echo '
raise RuntimeError("Stress test: simulated numpy import failure")
' > "$FAKE_NUMPY_DIR/__init__.py"
touch "$FAKE_NUMPY_DIR/__main__.py"
# So "import numpy" finds our package
export PYTHONPATH="$FAKE_NUMPY_DIR:$PYTHONPATH"
```

**5.2 Run the bot (numpy is used lazily in e.g. risk_metrics, backtesting, strategy_competition)**

```bash
export STATE_DIR="$STRESS_STATE" LOG_DIR="$STRESS_LOG"
# Bot may start; first code path that does "import numpy" will raise
MAX_CYCLES=2 SCAN_INTERVAL_SECONDS=5 python main.py
echo "Exit code: $?"
```

**5.3 Trigger numpy in dashboard (leaderboard / backtesting routes)**

```bash
# Start Flask app and hit a route that uses numpy
python -c "
from dashboard.app import create_app
app = create_app()
# Trigger import of strategy_competition or backtesting (which use numpy)
with app.test_client() as c:
    r = c.get('/api/leaderboard')  # or a route that imports numpy
    print(r.status_code, r.data[:200])
" 2>&1
echo "Exit code: $?"
```

**5.4 Restore normal behavior**

```bash
unset PYTHONPATH
# Or: export PYTHONPATH=""  (remove fake numpy)
```

**Pass criteria:** When numpy is faked to raise: the process or request fails with a clear error (RuntimeError or derived); no silent wrong results. After unsetting PYTHONPATH, normal run works.

**Optional — SIGFPE (platform-specific):**  
On platforms where numpy has been known to trigger SIGFPE (see `docs/SIGFPE_FIX_REPORT.md`), running the same binary and numpy version on that platform is the only way to simulate that failure; no generic shell recipe is given here.

---

## Summary Checklist

| Test | Command / procedure | Pass condition |
|------|---------------------|----------------|
| Rapid restart | Loop: start, sleep 8, kill -15, repeat 20x; then one MAX_CYCLES=5 run | State valid; final run exit 0 |
| High-frequency cycles | SCAN_INTERVAL_SECONDS=2 MAX_CYCLES=500 | Exit 0; no traceback storm in log |
| Corrupted state | Overwrite state files with invalid JSON / empty; run 2–3 cycles | No crash; exit 0 |
| Disk full | tmpfs 1MB or fill LOG_DIR; run bot | Logged error or graceful degradation; no unhandled exception |
| Slow I/O | NFS or nice/ionice; run with short interval | No corrupt state; optional lock timeout in log |
| Log saturation | Many/large files or small tmpfs for LOG_DIR | No crash; rotation/trimming; bounded size |
| Long-run memory | 6–24h run; sample RSS every 5 min | RSS stable or slight drift; no sustained growth |
| Crash: SIGTERM/SIGINT | kill -15 / kill -2 after 10s | Exit 0; state valid |
| Crash: SIGKILL | kill -9; restart; run 5 cycles | Restart exit 0; state valid or recreated |
| Network block | iptables/pf or proxy drop; run 5 cycles | No crash; mock fallback; exit 0 |
| Numpy failure | PYTHONPATH=fake_numpy; run bot or hit dashboard route | Clear failure (exception); after unset, normal run OK |

---

*Document version: 1.0. No application code is modified by this plan.*
