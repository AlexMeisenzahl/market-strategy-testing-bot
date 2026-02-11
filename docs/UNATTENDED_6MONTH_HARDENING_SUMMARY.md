# 6+ Month Unattended Runtime — Hardening Summary

Changes implemented to **eliminate silent degradation** (no trading logic modified).

---

## 1. Bounded History Lists

| Component | Cap | Location |
|-----------|-----|----------|
| **optimization_history** | 200 | `services/strategy_optimizer.py` — `OPTIMIZATION_HISTORY_MAX_LEN` |
| **trade_history[strategy_id]** | 5,000 per strategy | `services/strategy_competition.py` — `TRADE_HISTORY_MAX_LEN_PER_STRATEGY` |
| **pnl_history** (per portfolio) | 10,000 | `services/strategy_competition.py` — `PNL_HISTORY_MAX_LEN` |
| **portfolio snapshots** | 5,000 | `services/portfolio_manager.py` — `SNAPSHOTS_MAX_LEN` |

Older entries are trimmed (keep last N). No unbounded in-memory growth from these lists.

---

## 2. Trades/Opportunities Storage — SQLite (Bounded)

- **Primary store:** `database/trades_store.py` — SQLite DB at `logs/trades.db`.
- **Row caps:** Last 500,000 trades and 500,000 opportunities retained; older rows pruned on insert.
- **Logger:** Writes to SQLite (with CSV fallback if import fails). No unbounded CSV append.
- **Data parser:** Reads last 25,000 trades and 25,000 opportunities for dashboard; 30s cache TTL (no full-file load every 5s).
- **Tax exporter:** Loads from store when available (year filter supported).
- **Export:** `/api/export/trades` builds CSV from data_parser (bounded list).
- **Migration:** On first run, if `trades.csv` / `opportunities.csv` exist and DB is empty, they are backfilled once.

---

## 3. Dashboard — No Full History Every 5s

- **Data parser:** Loads only last **25,000** trades and opportunities; cache TTL **30 seconds** (was 5s).
- **Panel refresh:** Polling interval increased from **5s to 15s** (`realtime_contract.js` `POLL_PANELS_MS`, `dashboard.js` `REFRESH_INTERVAL`, opportunities.html, leaderboard.html).
- **Export:** Uses data_parser (bounded) so export does not read entire unbounded file.

---

## 4. Disk Usage Logging (Logs Directory)

- **Logger:** `log_logs_disk_usage()` added — recurses `log_dir`, sums file sizes, logs one line to the standard log (e.g. `Logs dir disk usage: X.XX MB (path)`).
- **run_bot:** Calls `log_logs_disk_usage()` whenever it logs memory (same interval as memory logging).

---

## Memory and Disk Growth Projections (After Changes)

### Memory (process)

| Source | Before | After (6 months) |
|--------|--------|-------------------|
| optimization_history | Unbounded | ≤200 records |
| strategy_competition (trade_history + pnl_history) | Unbounded per strategy | ≤5k trades × strategies + ≤10k PnL per portfolio |
| portfolio_manager.snapshots | Unbounded | ≤5,000 snapshots |
| DataParser cache | Full CSV in memory every 5s | ≤25k trades + 25k opportunities, refresh every 30s |
| **Rough total delta** | Could grow 100s MB+ over 6 months | **Bounded** (order of tens of MB for these structures) |

### Disk (logs directory)

| Source | Before | After (6 months) |
|--------|--------|-------------------|
| trades.csv / opportunities.csv | Unbounded append | **No longer written** (SQLite primary); legacy CSV may exist but not grown by logger |
| logs/trades.db | N/A | **Bounded:** 500k trades + 500k opportunities then prune. ~50–100 bytes/row → ~50–100 MB max for these tables |
| errors.log / connection.log | Rotating (10 MB × 5) | Unchanged — **~50 MB max** |
| activity.json | Capped at 1k entries | Unchanged |
| **Rough total** | Unbounded (GB possible) | **Bounded** — on the order of **~100–200 MB** for logs dir under heavy use, with disk usage logged periodically |

### Summary

- **Memory:** In-process lists and dashboard cache are capped; no silent growth from optimization history, competition history, snapshots, or full-file CSV load.
- **Disk:** Trades/opportunities are in a single SQLite DB with a fixed max row count; rotating text logs unchanged; logs dir size is logged periodically for monitoring.
