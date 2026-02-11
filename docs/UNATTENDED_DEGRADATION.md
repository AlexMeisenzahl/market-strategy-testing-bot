# If This Ran Unattended for 6 Months, What Would Silently Degrade?

This document lists behaviors that would **silently** worsen over time (no crash, no alert): unbounded growth, stale caches, and drift that only show up as slowness, wrong data, or memory pressure.

---

## 1. **logs/trades.csv and logs/opportunities.csv — unbounded growth**

- **What:** Logger appends every trade and opportunity with `open(..., "a")`. No rotation or size limit.
- **Effect:** File size and row count grow without bound. Dashboard `DataParser` reads the **entire** file into memory on each cache refresh (TTL 5s). Parse time and memory scale with file size.
- **Silent degradation:** Dashboard loads (trades, analytics, strategy comparison, evaluation) become slower; eventually very slow or OOM on a memory-constrained host. No error until load times or memory are extreme.
- **Mitigation:** Add rotation/trim (e.g. keep last N rows or last N MB) in `logger.py`, or a scheduled job that truncates/archives old rows. Not fixed here to avoid changing live logging behavior without your approval.

---

## 2. **Backtest run_id store (_run_by_id) — unbounded in-memory dict**

- **What:** `services/research_service.py`: `_backtest_runs` is a `deque(maxlen=50)`, but every stored run is also added to `_run_by_id[run_id] = entry` and **never removed**. When the deque drops the oldest run, that run_id remains in `_run_by_id`.
- **Effect:** Every backtest run (e.g. from dashboard “Run backtest” or comparison) adds one permanent entry. Over months this dict grows without bound in the **dashboard/API process**.
- **Silent degradation:** Memory use of the dashboard process grows; “Compare selected runs” and “Get run by id” keep resolving old run_ids to stale data. No crash, just creeping memory and stale comparisons.
- **Mitigation:** When evicting from the deque, remove the same run_id from `_run_by_id`. Fixed below.

---

## 3. **Strategy optimizer history — unbounded list**

- **What:** `services/strategy_optimizer.py`: `self.optimization_history = []` and `self.optimization_history.append(optimization_record)` with no cap.
- **Effect:** Every parameter sweep / optimizer run appends a full result. List grows forever in the process that runs the optimizer (e.g. dashboard).
- **Silent degradation:** Memory growth; “optimizer history” and export endpoints may return huge payloads and get slower. No failure until memory or response size is a problem.
- **Mitigation:** Cap length (e.g. keep last 100 entries) or age-based eviction. Documented here; not changed to avoid altering optimizer API without approval.

---

## 4. **Strategy competition — unbounded per-strategy lists**

- **What:** `services/strategy_competition.py`: `trade_history[strategy_id].append(...)`, `portfolio["pnl_history"].append(pnl)`, and `performance_cache` grows with strategies and use.
- **Effect:** If the competition module runs continuously, in-memory trade and PnL history per strategy grow without bound.
- **Silent degradation:** Memory growth in the process that runs strategy competition; slower leaderboard/competition views. No alert.
- **Mitigation:** Cap list lengths per strategy or evict by age. Documented only.

---

## 5. **Portfolio manager snapshots — unbounded list**

- **What:** `services/portfolio_manager.py`: `self.snapshots.append(snapshot)` with no max length.
- **Effect:** Every snapshot (e.g. per cycle or per trade) is kept forever in memory.
- **Silent degradation:** Process memory grows; any logic that iterates over `snapshots` (e.g. for charts or analytics) gets slower. No explicit failure.
- **Mitigation:** Keep last N snapshots or last N days. Documented only.

---

## 6. **Dashboard data parser cache — full-file load**

- **What:** `dashboard/services/data_parser.py`: On cache miss, the **entire** `trades.csv` (and opportunities CSV) is read and stored in `_trades_cache` / `_opportunities_cache`. Cache TTL is 5 seconds; there is no cap on cached list size.
- **Effect:** As the CSVs grow (see #1), each cache refresh does a larger read and holds more data in memory. Multiple concurrent requests can each trigger a full load.
- **Silent degradation:** Same as #1: slower and heavier dashboard over time. No error, just latency and memory.

---

## 7. **Time-based and config drift**

- **What:** No automatic refresh of config from disk; no built-in “health date” checks. Any logic that assumes “recent” data (e.g. “last 24h”) uses wall clock; if the process runs for 6 months, “recent” is still correct but “last 90 days” grows to a lot of data if stored.
- **Effect:** Config changes (e.g. API keys, limits) require process restart. Stale API keys or rate limits may cause increasing failures that look like “API errors” rather than “config drift.”
- **Silent degradation:** More 401/403 or rate-limit errors over time if keys expire or limits change; no automatic signal that “config is old.”

---

## 8. **What is already bounded (no silent degradation from growth)**

- **activity.json:** Capped at last 1000 entries in `run_bot.py` (`activities = activities[-1000:]`). Bounded.
- **errors.log / connection.log:** `RotatingFileHandler` (10MB × 5 backups) in `logger.py`. Bounded.
- **Paper engine trade_history:** In-memory cap (`trade_history_max_len`, default 10k); state save only writes last 1000 trades. Bounded.
- **Backtest runs deque:** `_backtest_runs` has `maxlen=50`. Only `_run_by_id` was unbounded; fix below addresses that.

---

## Summary table

| Component              | Grows?   | Where              | Silent effect              |
|------------------------|----------|--------------------|----------------------------|
| trades.csv             | Yes      | disk               | Slower dashboard, OOM risk |
| opportunities.csv      | Yes      | disk               | Same                       |
| _run_by_id             | Yes      | dashboard process  | Memory, stale run ids     |
| optimization_history   | Yes      | optimizer process  | Memory, slow exports      |
| strategy_competition   | Yes      | competition process| Memory, slow views        |
| portfolio_manager.snapshots | Yes | engine/process     | Memory, slow analytics    |
| activity.json          | No (1k)  | disk               | —                          |
| errors.log             | No (rotate) | disk            | —                          |
| Paper trade_history    | No (10k/1k) | memory/state   | —                          |
| _backtest_runs         | No (50)  | memory             | —                          |

---

## Fix applied: _run_by_id eviction

When a backtest run is evicted from the deque (because a new run was added and the deque is full), the same run_id is now removed from `_run_by_id` so the dict does not grow forever. Old run_ids will 404 after eviction instead of returning stale data.
