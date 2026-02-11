# Critical Reliability Mitigation Pass — Summary

Focus: **preventing silent failure and data loss**. No trading logic changed.

---

## 1. Disk write failures: no silent swallow

**Before:** `_write_bot_state`, `_write_engine_health`, `_log_activity`, `_save_paper_engine_state` used `try/except Exception: pass`, so disk full or other write errors were invisible.

**After:**
- On failure: **log error** (e.g. `Disk write failed (bot_state): …`) and **increment `write_error_count`**.
- **Exposed via /health:** `engine_health.json` (and thus dashboard `GET /health` / `GET /api/health`) includes `write_error_count`. Dashboard marks **overall_status = "degraded"** when `write_error_count > 0` or `disk_status == "critical"`.

**Files:** `run_bot.py` (`_write_bot_state`, `_write_engine_health`, `_log_activity`, `_save_paper_engine_state`), `dashboard/app.py` (health endpoint).

---

## 2. Disk space monitoring

**Added:** `_disk_health()` in run_bot:
- Uses `shutil.disk_usage(state_dir)` for the partition that holds state.
- **Warn at 85%:** logs warning, sets `disk_status: "warn"`.
- **Critical at 95%:** logs critical, sets `disk_status: "critical"`.
- **Surfaced in /health:** `engine_health` includes `disk_used_pct` and `disk_status` (`ok` | `warn` | `critical` | `null` if unavailable). Dashboard uses `disk_status == "critical"` to set overall_status to degraded.

**Files:** `run_bot.py` (`_disk_health`, `_write_engine_health`), `dashboard/app.py` (health).

---

## 3. SQLite timeout and retry

**Added:**
- **Explicit timeout:** All DB access uses `sqlite3.connect(path, timeout=15.0)` via shared `_connect(log_dir)` (constant `SQLITE_TIMEOUT_SEC = 15.0`).
- **One retry with backoff:** `insert_trade` and `insert_opportunity` catch `sqlite3.OperationalError`, sleep `SQLITE_RETRY_BACKOFF_SEC` (0.5s), then retry once before re-raising. Reduces transient lock contention / data loss.

**Files:** `database/trades_store.py` (`_connect`, `insert_trade`, `insert_opportunity`; all other DB calls use `_connect` for consistent timeout).

---

## 4. Data source flag and mock-persist warning

**Added:**
- **Tracking:** `_data_source` (`"live"` | `"mock"`) and `_mock_cycles` (consecutive cycles on mock). Set in `_fetch_markets`: live path sets `_data_source = "live"`, `_mock_cycles = 0`; mock path sets `_data_source = "mock"`, `_mock_cycles += 1`.
- **Exposed via /health:** `engine_health` includes `data_source` and `mock_cycles`.
- **Log warning when mock persists:** If `_mock_cycles >= MOCK_WARN_CYCLES` (3), log: `Mock data in use for N consecutive cycles (no live data)`.

**Files:** `run_bot.py` (`_fetch_markets`, `_write_engine_health`, init).

---

## 5. System sleep/resume detection and reconnection

**Added:**
- **Detection:** At start of each cycle, if `_last_cycle_end_time` is set and `(cycle_start - _last_cycle_end_time) > SLEEP_RESUME_THRESHOLD_SEC` (max(300, 2×scan_interval)), treat as possible sleep/resume and log: `System resume detected (gap Ns since last cycle). Forcing reconnection.`
- **Reconnection:** Call `market_client.connect()` if the client has that method (e.g. PolymarketClient). Runs before the next trade cycle so the next `get_markets()` uses a fresh connection.
- **Bookkeeping:** `_last_cycle_end_time = time.time()` set after each successful cycle (before sleep).

**Files:** `run_bot.py` (main loop: before `run_cycle()`, after state saves).

---

## /health payload (engine section)

When the engine is running and writing `state/engine_health.json`, the dashboard’s `/health` response includes an `engine` object with (among existing fields):

- `write_error_count`: number of disk write failures since start.
- `disk_used_pct`: percentage of disk used (state partition), or null.
- `disk_status`: `"ok"` | `"warn"` | `"critical"` | null.
- `data_source`: `"live"` | `"mock"` | `"unknown"`.
- `mock_cycles`: consecutive cycles on mock data.

Dashboard sets **overall_status = "degraded"** (and 503) when `engine.disk_status == "critical"` or `engine.write_error_count > 0`.

---

## Remaining risk (concise)

| Risk | Mitigation status | Note |
|------|-------------------|------|
| **Disk full** | Logged, counted, surfaced in /health; dashboard degrades. | No automatic remediation; operator must free space. |
| **SQLite lock > 15s** | Timeout 15s + one retry. | Second failure still raises; trade/opportunity can be lost that cycle. |
| **Mock data for long time** | Flag + mock_cycles in /health; log every cycle when ≥ 3. | No auto-alert channel (e.g. Telegram); operator must check logs or /health. |
| **Sleep/resume** | Detect and reconnect market client. | Reconnect can fail (logged); no retry loop. |
| **Activity write failure** | Logged, write_error_count. | Activity feed can be stale until disk is fixed. |
| **Paper state save failure** | Logged, write_error_count. | Restart may lose some state since last successful save. |
| **Engine not running** | N/A | /health shows last written engine_health; no live disk/write_error until engine runs again. |

---

## No change to trading logic

- No changes to strategy selection, order sizing, or execution.
- Only reliability and observability around disk, DB, data source, and sleep/resume.
