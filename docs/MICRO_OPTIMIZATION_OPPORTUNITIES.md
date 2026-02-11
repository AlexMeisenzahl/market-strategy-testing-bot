# Micro-Optimization Opportunities

Identified without altering logic or strategy behavior. No architectural rewrites.

---

## 1. CPU / I/O overhead reductions

### 1.1 `_write_bot_state`: double JSON serialization

**Location:** `run_bot.py` ~523–565

**Current:** State dict is built, then `json.dumps(state, sort_keys=True)` is used only to compute `state_hash`. If the hash changed, `locked_write_json(self.state_path, state, ...)` is called, which calls `atomic_write_json` and serializes the same dict again with `json.dumps(data, indent=indent)`.

**Optimization:** Serialize once. Compute hash from the same payload string that will be written (or from a stable subset), then pass that string to a write path that accepts pre-serialized bytes/string, or pass the dict and have the writer return the payload so the caller can hash it and only call the writer when hash changed. Avoids one full `json.dumps` per cycle when state is written.

---

### 1.2 `atomic_write_json`: repeated `Path` and path ops

**Location:** `utils/atomic_json.py` 46–94, 217–259

**Current:** `path = Path(path)` and `path.parent` / `path.name` are used multiple times. `locked_write_json` builds `lock_path = path.parent / (path.name + ".lock")` and calls `path.parent.mkdir(...)`; `atomic_write_json` again does `path.parent.mkdir(...)` and `path.parent / (path.name + ".tmp." + ...)`.

**Optimization:** Compute `parent = path.parent`, `path_name = path.name` once per call; reuse for mkdir, tmp name, and (in locked_write_json) lock path. Reduces repeated attribute access and path construction.

---

### 1.3 `execution_gate`: control path and file stat every call

**Location:** `services/execution_gate.py` 26–36, 73–74, 89–90

**Current:** When `control_path` is `None`, `Path(__file__).resolve().parent.parent / "state" / "control.json"` is built on every `may_execute_trade` and `get_gate_status` call. `_is_paused` does `control_path.exists()` (stat) then `open` + `json.load`.

**Optimization:** Resolve default control path once at module load (e.g. `_DEFAULT_CONTROL_PATH = Path(__file__).resolve().parent.parent / "state" / "control.json"`) and reuse. Cuts repeated path resolution and keeps gate logic unchanged.

---

### 1.4 `_read_control`: full locked load every loop iteration

**Location:** `run_bot.py` 476–488, main loop 1147

**Current:** Every main-loop iteration (including when paused) calls `locked_load_json(self.control_path, default={})`, which opens the file, acquires shared lock, reads and parses JSON, then unlocks. When paused, the loop does this every `scan_interval_seconds` with no other work.

**Optimization:** When paused, either skip reading control on every wait (e.g. read at most every N seconds) or use a short in-memory TTL so repeated reads within the same second reuse the last result. Reduces I/O and lock traffic when no one is toggling pause.

---

### 1.5 `logger`: `log_dir` as `Path` on every write

**Location:** `logger.py` – `log_trade` / `log_opportunity` use `self.log_dir / "trades.csv"` etc.

**Current:** Each call builds path from `self.log_dir` (already a Path). When using SQLite, `_get_db_path(log_dir)` is called per insert, which does `Path(log_dir) / DB_FILENAME`.

**Optimization:** Cache `_db_path = self.log_dir / DB_FILENAME` (and other fixed paths) once in `Logger.__init__` and reuse. Cuts repeated path construction and normalization.

---

## 2. Redundant computations

### 2.1 `min_profit_margin` in `_process_opportunities` inner loop

**Location:** `run_bot.py` 776–778, inside the per-opportunity loop

**Current:** `min_margin = self.config.get("min_profit_margin", 0.02) * 100` is evaluated for every opportunity. Config does not change mid-cycle.

**Optimization:** Compute once before the loop (e.g. `min_margin_pct = self.config.get("min_profit_margin", 0.02) * 100`) and use `min_margin_pct` inside the loop. Same for the string `f"Meets {min_margin:.1f}% minimum threshold"` / `f"Below {min_margin:.1f}% minimum threshold"` if the numeric value is fixed for the cycle.

---

### 2.2 Positions and portfolio value computed multiple times per cycle

**Location:** `run_bot.py` _check_alerts (900–902), _write_bot_state (508–512); `services/paper_trading_engine.py` get_all_positions, get_portfolio_value, get_performance_metrics

**Current:** In one cycle: `_check_alerts` builds `current_prices` from `prices_dict`, calls `get_positions(current_prices)` and `get_balance()` and `get_trade_history()`. Later `_write_bot_state` calls `get_performance_metrics(self._last_prices_dict)` (which calls `get_portfolio_value` and iterates `self.positions` for `open_positions`), then `get_positions(self._last_prices_dict)`, then `get_balance()`. So positions are iterated at least three times (get_portfolio_value, open_positions list comp, get_all_positions), and `_last_prices_dict` is the same as the prices used in _check_alerts when no error occurred.

**Optimization:** In the main loop, after `run_cycle()` and before _write_engine_health / _write_bot_state, call `get_positions(self._last_prices_dict)` and `get_performance_metrics(self._last_prices_dict)` once (or a single helper that returns both positions and metrics in one pass over positions). Pass the results into _write_bot_state so it does not call get_positions/get_performance_metrics again. Same positions and metrics, fewer iterations over the positions dict.

---

### 2.3 `current_prices` built twice from same `prices_dict`

**Location:** `run_bot.py` _check_alerts 881–884 and 906–908

**Current:** `current_prices = { market_id: price_data.get("yes", 0.5) for ... }` is built from `prices_dict`. The same mapping (market_id → yes price) is already representable by `prices_dict` or by a single pass; later we build `alert_data["prices"]` with the same comprehension again.

**Optimization:** Build `current_prices` once; reuse for `get_positions(current_prices)` and for `alert_data["prices"]` (or pass the same dict reference). Avoids a second dict comprehension over the same data.

---

### 2.4 `today_prefix` and trade history scan in _check_alerts

**Location:** `run_bot.py` 893–910

**Current:** `today_prefix = datetime.now(timezone.utc).date().isoformat()` is computed; then we iterate `self.execution_engine.get_trade_history()` (which returns a new list copy) and filter by `(t.get("timestamp") or "").startswith(today_prefix)`.

**Optimization:** Use a single `datetime.now(timezone.utc)` and derive both date and prefix if needed elsewhere. Trade-history filtering is required for correct daily P&L; the only redundancy is `get_trade_history()` allocating a new list each time—see “Memory churn” for a lighter-weight option (e.g. a generator or a method that sums daily P&L without returning the full list).

---

### 2.5 `_normalize_market_format`: duplicate key lookups per market

**Location:** `run_bot.py` 641–655

**Current:** For each market, `market.get("market_id", market.get("id", "unknown"))` and `market.get("market_name", market.get("question", "Unknown"))` do multiple lookups. Same for other keys.

**Optimization:** Use a single get with a default, or local variables (e.g. `id_ = market.get("market_id") or market.get("id") or "unknown"`) so each key is resolved once per market. Small per-item CPU save over many markets.

---

## 3. Unnecessary disk writes

### 3.1 `engine_health.json` every cycle and every pause tick

**Location:** `run_bot.py` 1169–1171 (after cycle), 1149–1150 (when paused), 1219 (on exception)

**Current:** `_write_engine_health()` is called after every completed cycle (with timestamp and duration), on every paused-loop iteration (no cycle run), and on main-loop exception. Each call does `atomic_write_json(self.engine_health_path, health)` (full write + fsync + optional dir sync).

**Optimization:** Write engine_health at most every N seconds (e.g. 30–60) or only when a field that consumers care about changes (e.g. status, last_cycle_timestamp, error_count, cycles_completed). When paused, write once when entering pause and optionally on a timer instead of every sleep. Reduces write and fsync rate without changing semantics for dashboard/health checks.

---

### 3.2 `paper_engine_state.json` every cycle

**Location:** `run_bot.py` 1199–1200

**Current:** `_save_paper_engine_state()` runs after every successful cycle. It calls `get_state()` (which builds a new dict and slices `trade_history[-1000:]`) and `locked_write_json` with backup. So we do a full atomic write + backup read/write every cycle even when no trade occurred and balance/positions unchanged.

**Optimization:** Write paper state at most every N cycles (e.g. 5–10) or only when the engine state changed (e.g. compare a lightweight hash of balance + position count + last order_counter to last saved hash). Still call at shutdown. Cuts disk writes and lock contention when state is unchanged.

---

### 3.3 `activity.json`: one read-modify-write per activity

**Location:** `run_bot.py` _log_activity 589–614; called from _process_opportunities (per opportunity), _execute_trades (per strategy with trades), _check_alerts (per triggered alert), error handler, etc.

**Current:** Each `_log_activity(activity)` does: `load_json(activity_log_path, ...)` (read + parse), append one item, slice to last 1000, `locked_write_json(activity_log_path, activities)` (lock + atomic write). With many opportunities per cycle, this can be dozens of read-lock-write sequences per cycle.

**Optimization:** Batch activities per cycle. Collect activities in a list during the cycle (e.g. in _process_opportunities append to a list instead of calling _log_activity; same for trade executions and alerts). Once at end of cycle (before or with _write_bot_state), call a single _log_activities(activities) that does one load, extend, trim to 1000, one write. Same data, one read and one write per cycle for activity.

---

### 3.4 `bot_state` backup on every hash change

**Location:** `run_bot.py` 551–565; `utils/atomic_json.py` 70–79

**Current:** When state hash changes, `locked_write_json(..., backup_path=self.state_dir / "bot_state.backup.json")` runs. Inside `atomic_write_json`, when `backup_path` is set and the target file exists, it reads the current file and writes it to the backup (then replaces the main file). So every state update does a read of current + write of backup + write of new content.

**Optimization:** Create backup only every N writes or every M seconds (e.g. every 10th write or every 5 minutes). Or make backup optional via a parameter and call with backup_path only periodically from run_bot. Reduces I/O while keeping a recent backup for recovery.

---

## 4. Memory churn

### 4.1 `get_trade_history()` returns a new list every call

**Location:** `engine.py` 120–122

**Current:** `return list(self.trading_engine.trade_history)` allocates a new list and copies all references (up to trade_history_max_len, e.g. 10000). Called from _check_alerts once per cycle to compute daily P&L (filter by today’s timestamp).

**Optimization:** Add a method on the engine or paper engine that returns “daily realized PnL” (or similar) by iterating trade_history once and summing, without building a full list to return. Call that from _check_alerts instead of get_trade_history() when only the sum is needed. Reduces allocation and copying when history is large.

---

### 4.2 `get_state()` slices and builds new structures every save

**Location:** `services/paper_trading_engine.py` 580–604

**Current:** `get_state()` builds a new `positions_list` (new list + new dicts per position), then returns a dict that includes `self.trade_history[-1000:]` (new list slice). Called every cycle from _save_paper_engine_state when that write is not skipped (see 3.2).

**Optimization:** If paper state is written less often (see 3.2), fewer calls to get_state(). Alternatively, reuse a buffer for the positions list (e.g. clear and repopulate a list that is kept as an instance attribute) to reduce small allocations; only if profiling shows this as hot. The main gain is writing less often so get_state is called less.

---

### 4.3 `_convert_markets_to_prices_dict`: new dict and datetime per market

**Location:** `run_bot.py` 748–756

**Current:** For each market we build `{"yes": ..., "no": ..., "last_updated": datetime.now(timezone.utc).isoformat()}`. So we call `datetime.now(timezone.utc).isoformat()` N times (e.g. 100) per cycle.

**Optimization:** Compute `now_iso = datetime.now(timezone.utc).isoformat()` once before the loop and use it for every market’s `last_updated`. Same semantics, less datetime and string work.

---

### 4.4 `_process_opportunities`: repeated opportunity-to-dict and attribute access

**Location:** `run_bot.py` 764–814

**Current:** For each opportunity we do `opp.to_dict() if hasattr(opp, "to_dict") else {}` and `opp.profit_margin if hasattr(opp, "profit_margin") else 0`. We then build two similar dicts (executing vs skipped) with overlapping keys.

**Optimization:** Hoist `min_margin_pct` (see 2.1). Optionally call `to_dict` once and reuse for both “executing” and “skipped” payloads (shared keys); build the two activity dicts from that plus the single differing field (action/reason). Cuts duplicate dict construction and repeated hasattr/getattr.

---

### 4.5 Paper engine `get_performance_metrics`: extra list for `open_positions`

**Location:** `services/paper_trading_engine.py` 504–506

**Current:** `open_positions: len([p for p in self.positions.values() if p.quantity != 0])` allocates a new list only to take its length.

**Optimization:** Use `sum(1 for p in self.positions.values() if p.quantity != 0)` so no list is allocated. Same count.

---

## 5. Batching and caching

### 5.1 Activity log: batch writes per cycle

**Location:** `run_bot.py` _log_activity and all call sites (see 3.3)

**Optimization:** Collect all activity dicts for the cycle in a list (e.g. on BotRunner). At end of cycle, call a single method that reads activity.json once, extends with the list, trims to last 1000, writes once. Same behavior, one read and one write per cycle instead of per activity.

---

### 5.2 Trades/opportunities SQLite: batch inserts per cycle

**Location:** `database/trades_store.py` insert_trade, insert_opportunity; `logger.py` log_trade, log_opportunity; `services/paper_trading_engine.py` (calls logger.log_trade per fill)

**Current:** Each trade triggers `store_insert_trade(log_dir, ...)`, which opens a new connection, inserts one row, checks count for prune, closes. Same for opportunities when strategies call log_opportunity.

**Optimization:** Add `insert_trades_batch(log_dir, rows)` and `insert_opportunities_batch(log_dir, rows)` that use a single connection and `executemany` (or multiple executes in one transaction). From the paper engine (or a thin adapter), collect trade records for the cycle and flush once when the cycle completes (or when N records accumulate). For opportunities, run_bot could collect strategy-reported opportunities and call a batch insert at end of _process_opportunities. Requires a small API to “queue” trades/opportunities and flush at cycle end; logic and strategy output stay the same.

---

### 5.3 Execution gate result per cycle

**Location:** `run_bot.py` _execute_trades 822–823; `engine.py` execute_trade; `services/paper_trading_engine.py` place_order

**Current:** `may_execute_trade(config, control_path)` is called from run_bot once at the start of _execute_trades, and again for every place_order from the engine (and again inside place_order via execution_gate). So we can call it multiple times per cycle (once in run_bot, then once per order in the engine/paper engine).

**Optimization:** Compute gate result once at the start of the cycle (e.g. in run_cycle or at the start of _execute_trades) and pass a “gate allowed” flag into the execution path, or set a short-lived thread-local/call-context that the engine and place_order read. Gate is still evaluated once per cycle before any trade; later calls in the same cycle reuse the result. Reduces repeated file read and DB hit for kill_switch.

---

### 5.4 Config reads in hot path

**Location:** Various; e.g. `run_bot.py` (min_profit_margin, paper_trading, etc.), execution_gate (config.get), strategy_manager (config.get).

**Current:** `self.config.get("min_profit_margin", 0.02)` and similar are called repeatedly. Config is loaded at startup and not reloaded in the loop.

**Optimization:** Cache hot config values on BotRunner (and strategy manager) at init or at first use: e.g. `min_profit_margin_pct`, `paper_trading`, `scan_interval_seconds`. Use the cached values in the loop. No config reload logic required; same behavior.

---

### 5.5 Default control path in execution_gate

**Location:** `services/execution_gate.py` (see 1.3)

**Optimization:** Cache the default control path at module load. This is both a CPU/path-reduction (1.3) and a small “cache” of a derived value so it is not recomputed on every gate check.

---

## Summary table

| Category        | Item                               | File(s)                    | Effect                          |
|----------------|------------------------------------|----------------------------|---------------------------------|
| CPU/I/O        | Double JSON serialize in bot state | run_bot.py                 | One less json.dumps per write   |
| CPU/I/O        | Path/parent/name reuse in atomic_json | utils/atomic_json.py   | Fewer Path ops per write        |
| CPU/I/O        | Default control path constant      | execution_gate.py          | No path build per gate call     |
| CPU/I/O        | Control read when paused           | run_bot.py                 | Fewer reads per pause tick      |
| CPU/I/O        | Logger DB/csv paths cached          | logger.py                  | Fewer path builds per log       |
| Redundant      | min_profit_margin in loop           | run_bot.py                 | One config read per cycle       |
| Redundant      | Positions/metrics once per cycle    | run_bot, paper_trading_engine | Fewer position iterations   |
| Redundant      | current_prices once in _check_alerts| run_bot.py                 | One dict comp instead of two    |
| Redundant      | open_positions count without list   | paper_trading_engine.py    | No list allocation              |
| Redundant      | _normalize_market_format key lookups| run_bot.py                 | One lookup per key per market   |
| Disk writes    | engine_health write throttle        | run_bot.py                 | Fewer fsyncs per hour           |
| Disk writes    | paper_engine_state write throttle   | run_bot.py                 | Fewer state writes per cycle    |
| Disk writes    | activity.json batch per cycle       | run_bot.py                 | One read/write per cycle        |
| Disk writes    | bot_state backup less often         | run_bot, atomic_json       | Fewer backup writes             |
| Memory churn   | get_trade_history → daily PnL only  | engine, run_bot            | No full list copy for alerts    |
| Memory churn   | last_updated once in prices dict    | run_bot.py                 | One datetime/iso per cycle      |
| Memory churn   | get_performance_metrics open_positions | paper_trading_engine.py | No list for count           |
| Batching       | Activity batch                      | run_bot.py                 | One activity write per cycle    |
| Batching       | SQLite batch insert                 | trades_store, logger, engine| Fewer connections per cycle      |
| Caching        | Gate result per cycle               | run_bot, engine, gate       | One gate check per cycle        |
| Caching        | Hot config values                   | run_bot, strategy_manager   | Fewer dict lookups in loop      |

---

*Document version: 1.0. Logic and strategy behavior unchanged.*
