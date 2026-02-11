# Production Reliability Analysis (PRE)

Assessment of failure modes, OS effects, and external dependencies after hardening for 6+ month unattended runtime. No trading logic changed; focus on **silent degradation**, **blocking**, and **external dependency** risks.

---

## 1. Non-obvious failure modes that remain

| Risk | Where | What happens |
|------|--------|--------------|
| **State writes swallowed on disk full** | `run_bot.py` `_write_bot_state()`, `_write_engine_health()`, `_log_activity()` | All wrap in `try/except Exception: pass`. `atomic_write_json` / `locked_write_json` raise `OSError` (e.g. `ENOSPC`) on full disk; the exception is caught and ignored. **Effect:** Bot keeps running but `bot_state.json`, `engine_health.json`, and `activity.json` stop updating; dashboard shows stale state and “last update” drifts. No alert. |
| **Trade/opportunity log lost on SQLite error** | `logger.log_trade` / `log_opportunity` → `database/trades_store.py` | If `insert_trade` / `insert_opportunity` raise (e.g. `sqlite3.OperationalError` on lock, or `OSError` on disk full), the exception propagates. Callers: `paper_trading_engine` (on fill) and strategy code. **Effect:** Uncaught in engine path can fail the cycle (caught by `run_cycle`’s broad `except`), so one cycle logs error and continues; the **trade or opportunity is not written** to the store (and CSV fallback is only used when store import fails at init). |
| **Activity log failure only logs once** | `_log_activity()` | On `locked_write_json` failure (lock timeout or disk), exception is caught and `logger.log_error(...)` is called. **Effect:** Repeated failures spam errors.log but activity still doesn’t persist; dashboard activity feed freezes. |
| **Optimizer / competition / portfolio caps trim oldest** | `strategy_optimizer`, `strategy_competition`, `portfolio_manager` | History is bounded by dropping oldest entries. **Effect:** Long-running comparisons (e.g. “compare optimizations over time”) or drawdown over full history only see last N; no explicit “data truncated” indicator in API responses. |
| **Dashboard export from bounded data** | `data_parser.get_all_trades()` used for CSV export and charts | Export and charts use last 25k trades (or store limit). **Effect:** Users may assume “all time” but get “last N”; no disclaimer in UI. |
| **Config/control file lock timeout** | `utils/atomic_json.py` `locked_load_json` / `locked_write_json` | Lock timeout 10s; on timeout, `locked_load_json` returns default and logs; `locked_write_json` logs and still calls `atomic_write_json` (without lock). **Effect:** Under contention (e.g. dashboard writing pause while engine writes state), one side may see stale read or duplicate write; no hard crash. |

---

## 2. OS-level issues after 6 months

| Issue | Likelihood / cause | Impact |
|-------|--------------------|--------|
| **File descriptor leak** | Low. No long-lived open files in the main loop; SQLite and `open()` use context managers or explicit close. RotatingFileHandler is fixed. | If something did leak (e.g. a forked path), eventual `OSError: [Errno 24] Too many open files` and crash. |
| **Process limits (ulimit)** | Default `nofile` often 256–1024. Engine + dashboard + launcher each hold a few FDs; SQLite opens one connection per call and closes. | Under very high concurrency (many dashboard tabs, many API calls) or a leak, could hit limit and crash. |
| **Time drift (NTP skew or no NTP)** | `datetime.utcnow()` and `time.time()` follow system clock. | Stale or jumping timestamps in logs, activity, and trade records; incorrect “last 24h” windows and possible confusion in tax/reporting. |
| **Memory fragmentation** | Long-running single process; Python’s allocator can fragment. | Gradual RSS growth beyond bounded structures; rare but possible OOM after months. |
| **Disk inode exhaustion** | Many small files (e.g. logs, temp files). | `ENOSPC` on new file creation even if bytes free; same “write swallowed” behavior as full disk. |
| **Kernel / filesystem bugs** | Rare. | Corruption or weird behavior on `os.replace` / `fsync`; atomic_json’s backup and recovery mitigate partial reads. |

---

## 3. What could cause the engine to stall silently

| Cause | Mechanism | Severity |
|-------|-----------|----------|
| **Long cycle (not infinite)** | `run_cycle()` is synchronous: `_fetch_markets()` (timeout 30s in Polymarket client), then strategies, then `_process_opportunities`, `_execute_trades`, `_check_exit_conditions`. Any step that blocks (e.g. a strategy calling a slow API without a timeout) adds to cycle time. | Cycle timeout is only **logged** (`cycle_duration > _cycle_timeout_seconds`); loop continues. So “stall” = one very long cycle, not permanent stop. |
| **Blocking in strategy or client** | `get_markets()` uses `timeout=30`. If another client or strategy uses `requests` without timeout, that call can block until OS TCP timeout (minutes). | One cycle can hang for a long time; next cycle would only start after `time.sleep(scan_interval_seconds)`. |
| **Deadlock** | `portalocker` (file lock) and `threading.Lock` (e.g. in `rate_limiter`) can deadlock if lock order is inconsistent across threads. Main engine is single-threaded; dashboard and launcher use threads. | If a thread in dashboard holds a lock and waits on another held by the same process, that request stalls; engine loop is unaffected unless it shares that lock. |
| **Pause state stuck** | `_read_control()` reads `state/control.json` each cycle. If dashboard writes `pause: true` and then crashes before writing `false`, or file is corrupted, engine stays paused. | Not a CPU stall; engine keeps looping and skipping execution. Dashboard would show “paused”; operator must fix control file or restart. |

So true **silent permanent stall** (no more cycle iterations) would require the main loop to block indefinitely—e.g. a call with no timeout in the cycle path, or a deadlock in code invoked from the loop. Current code has timeouts on the main network and lock calls; the remaining risk is untimed third-party or strategy code.

---

## 4. Where thread or blocking behavior can appear

| Location | Behavior | Blocking risk |
|----------|----------|----------------|
| **run_bot main loop** | Single-threaded; `time.sleep(scan_interval_seconds)` is the only intentional wait. | All I/O in the cycle is synchronous; `get_markets` has timeout=30, so max ~30s block per cycle from that. |
| **Dashboard** | Flask + SocketIO with `async_mode="threading"`; each request runs in a thread. | Request handlers that call `data_parser` or `trades_store` do synchronous SQLite/CSV reads. Long request = one thread blocked; others can still run. |
| **SQLite** | No connection pooling; each `get_trades` / `insert_trade` etc. opens and closes a connection. Default `sqlite3.connect()` timeout is **5 seconds**. | If the DB is locked (e.g. another process or long query), connect or execute blocks up to 5s then raises `OperationalError`. |
| **atomic_json** | `locked_load_json` / `locked_write_json` use `portalocker` with timeout=10s. | Blocks up to 10s waiting for lock, then timeout or proceed. |
| **rate_limiter** | `threading.Lock`; `acquire(timeout=None)` can wait indefinitely. | Call sites that pass no timeout (e.g. `acquire()`) can block forever if the bucket is starved. Most usages (e.g. queue) use `timeout=30`. |
| **Launcher** | `threading.Thread(target=self._start_worker, daemon=True)`; subprocess management. | Worker does subprocess wait; main thread can block on `proc.wait(timeout=...)`. |
| **Telegram bot (async)** | `telegram_bot/bot_manager.py` uses asyncio; `send_message` etc. are async. | Isolated from the sync engine; if asyncio loop blocks, only Telegram path is affected. |
| **Order timeout handler** | `monitor_order_async` starts a daemon thread that can sleep. | Thread is daemon; if it blocks on I/O without timeout, it can hold resources but won’t block the main engine. |

**Summary:** Main engine blocking is bounded by network timeouts (30s) and lock timeouts (10s). SQLite adds up to 5s per call when contended. The main unbounded risk is `rate_limiter.acquire(timeout=None)` if ever used in the hot path.

---

## 5. Part of the system that depends most on external services

**Polymarket (or configured market) API** is the most critical external dependency:

- **Used by:** `run_bot` → `_fetch_markets()` → `market_client.get_markets()` (Polymarket client with `timeout=30`).
- **Effect of failure:** Exception is caught; engine falls back to `_get_mock_markets()` and continues with **mock data**. No crash, but **trading and opportunity logic run on synthetic data**; PnL and “opportunities found” are not real.
- **Other externals:** CoinGecko (crypto prices), Telegram (notifications), optional weather/NOAA. Failures there degrade features (alerts, notifications, weather strategy) but do not replace market data with mocks.

So the **highest-impact** external dependency is the market data source: when it’s down or unreachable, the bot keeps running but behaves as if it’s trading on mock markets.

---

## 6. If internet disconnects intermittently for 2 hours

| Component | Behavior |
|-----------|----------|
| **Engine** | Every cycle `get_markets()` fails (timeout or connection error), caught → fallback to `_get_mock_markets()`. Engine keeps cycling; logs “Error fetching markets” and “Falling back to mock market data.” **Trades and opportunities are against mock data**, not live markets. |
| **State files** | Written locally; no dependency on network. `bot_state.json` and `activity.json` keep updating (unless disk fails). |
| **Dashboard** | Serves from local state and data_parser (SQLite/CSV). No need for internet except for any external API calls the UI might trigger (e.g. test connection). |
| **Telegram** | Notifications that require Telegram API will fail; errors logged; no retry queue. |
| **Version/update check** | If triggered, will fail; no impact on trading loop. |

**Summary:** For 2 hours of intermittent disconnect, the engine **does not stop** but **silently runs on mock data**; PnL and opportunity counts for that period are not real. There is no automatic “live data lost” alert.

---

## 7. If disk fills to 95% (or 100%)

| Write path | Behavior |
|------------|----------|
| **atomic_write_json** (state, activity, engine_health) | Raises `OSError` (e.g. `ENOSPC`) from `open()`, `write()`, or `os.replace`. |
| **run_bot** | `_write_bot_state()`, `_write_engine_health()`, `_log_activity()` catch `Exception` and **swallow** (or log and continue). State and activity **stop updating**; engine keeps running. |
| **Logger** (errors.log, connection.log) | `RotatingFileHandler.emit()` can raise if disk full; exception may propagate to logging caller. If uncaught, that call (e.g. `log_trade`) can fail. |
| **SQLite (trades.db)** | `insert_trade` / `insert_opportunity` can raise when the DB or filesystem reports full. Exception propagates to logger → paper engine or strategy; cycle may fail and **that trade/opportunity is not recorded**. |
| **CSV fallback in logger** | Same as any `open(..., "a")` → can raise `OSError`; propagated to caller. |

**Summary:** At 95–100% disk full, the engine **continues** but state/activity writes are skipped (silent staleness). Log and trade writes can start failing and cause cycle errors or lost trades; there is **no proactive “disk full” check or alert**.

---

## 8. If SQLite DB is locked for 30 seconds

- Python’s `sqlite3.connect()` uses a **default timeout of 5.0 seconds** (not 30). So any connection that needs a lock (read or write) will **block up to 5 seconds**, then raise `sqlite3.OperationalError` if the lock is still held.
- **Engine (logger.log_trade / log_opportunity → insert_trade / insert_opportunity):** Blocks up to 5s then raises. Exception propagates (e.g. from paper engine on fill) and is caught by `run_cycle`’s `except Exception`. **Effect:** One cycle fails with error logged; the **trade/opportunity for that insert is not written**. Next cycle may succeed if lock is gone.
- **Dashboard (data_parser → store_get_trades / get_opportunities):** Same: block up to 5s then `OperationalError`. Request fails or returns partial/empty; user sees error or stale data.
- **Who holds the lock 30s?** Not the app’s own code (each call opens and closes quickly). Possible causes: backup tool, another process, or a bug that holds a connection open (none found in current code).

**Summary:** A 30s lock doesn’t mean 30s block; it means **5s block then failure** for each attempt. Trades/opportunities can be lost for that cycle; dashboard requests can fail. No retry or queue; operator would need to fix the blocking process or restart.

---

## 9. If the machine sleeps and wakes repeatedly

| Aspect | Behavior |
|--------|----------|
| **Process** | On macOS/Windows, the process may be **suspended** during sleep; on Linux it depends on power management. On wake, process resumes; no automatic restart. |
| **Main loop** | `time.sleep(scan_interval_seconds)` may return early on some systems when the system sleeps (e.g. macOS). So after wake, the next cycle can run **sooner** than expected or immediately. |
| **State files** | Stored on disk; survive sleep. No corruption from sleep itself. |
| **TCP connections** | Any open socket to Polymarket/Telegram etc. will be broken by sleep (connection idle or RST). Next `get_markets()` or API call will get a connection error and trigger fallback or failure. So first cycle(s) after wake may use **mock data** until the client effectively “reconnects” on next successful request. |
| **Clock** | If the system clock is adjusted on wake (e.g. NTP), `datetime.utcnow()` and `time.time()` jump; timestamps and intervals may be inconsistent. |
| **SQLite** | DB is on disk; no in-memory connection across sleep. After wake, new connections are opened as usual; no special recovery. |

**Summary:** Sleep/wake doesn’t crash the app but can cause: (1) first cycle(s) after wake to use mock data due to broken TCP; (2) skewed timing if sleep duration is large or clock changes; (3) no explicit “reconnected to live data” signal. The bot does not detect “was suspended” or force a reconnection step.

---

## Recommended mitigations (concise)

1. **Disk full / state write failure:** Check free space periodically (e.g. in same place as `log_logs_disk_usage()`); if below threshold, log at ERROR and consider a dedicated alert (e.g. Telegram). Optionally surface “last write failed” in `engine_health.json`.
2. **SQLite:** Set an explicit short timeout (e.g. 5s) and use a retry (e.g. 1–2 retries with backoff) for `insert_trade` / `insert_opportunity` so transient lock contention doesn’t drop trades.
3. **Internet/market data loss:** When falling back to mock data, log at ERROR and optionally set a flag in `engine_health.json` (e.g. `"data_source": "mock"`) so dashboard or alerts can show “not live.”
4. **Pause stuck:** Dashboard or a small cron job could check `control.json` age and content; alert if pause has been true for > N hours with engine running.
5. **Export/charts bounded data:** In UI or API doc, state that export and charts show “last N trades” (e.g. 25,000) and that full history is in DB with a higher limit (500k) or via tax export by year.

These are operational and small code additions; they do not change trading logic.
