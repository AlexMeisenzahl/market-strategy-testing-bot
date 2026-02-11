# Phase 7D: Strategy Lifecycle, Intelligence & UI Depth

**Objective:** Strategy experimentation lab with full visibility into rankings, health, attribution, and graduation — without changing execution logic. No README or UI misrepresents strategy behavior, health, or allocation.

---

## 1. Strategy Leaderboard Depth

**Surfaced (read-only):**

| Field | Source | Notes |
|-------|--------|--------|
| **Rankings** | Sorted by return_pct | Rank 1, 2, 3, … |
| **Health** | Derived from strategy.enabled, auto_disabled, paused | healthy \| paused \| auto_disabled \| disabled |
| **Attribution** | strategy.allocated_capital | Shown as "Allocation" (competition DB); engine uses config only |
| **Graduation stage** | strategy.trading_stage | paper, micro_live, mini_live, full_live (symbolic) |
| **Status** | Derived from return_pct | WINNING / MARGINAL / LOSING |
| **Metrics** | Snapshot or calculated | current_value, return_pct, sharpe_ratio, total_trades, win_rate, max_drawdown |

**Filters (GET /api/leaderboard/):**

- `status` — winning | marginal | losing
- `enabled` — 1 to show only enabled strategies
- `health` — healthy | paused | auto_disabled | disabled

**Drill-down:**

- Click strategy name on leaderboard → modal with historical performance (GET /api/leaderboard/performance/<name>?hours=168). Read-only.

**Code:**

- `services/strategy_competition.py` — `get_leaderboard()` extended with health, trading_stage, allocated_capital, attribution_note
- `dashboard/routes/leaderboard.py` — filters applied in route; `/performance/<strategy_name>` unchanged
- `dashboard/templates/leaderboard.html` — columns Health, Stage, Allocation; filter UI; drill-down modal

**No execution controls.** Leaderboard and filters are read-only.

---

## 2. Capital Allocation Alignment

**Actual engine behavior:**

- **Source:** `strategy_manager.py` → `_calculate_capital_allocation(strategy_config)`
- **Logic:** Reads `config["strategies"]`. If `capital_allocation` is set (e.g. `{ "arbitrage": 0.7, "momentum": 0.2 }`), uses those percentages of `total_capital`. Otherwise **equal split** among `strategies.enabled`.
- **Engine does not** read Strategy.allocated_capital from the competition DB. It does not use 70/20/10 from the database.

**Score-based 70/20/10:**

- **Where:** `services/strategy_selector.py` → `auto_allocate_capital()`. Allocates 70% to top strategy, 20% to second, 10% to third by score and **writes to DB** (`Strategy.update(..., allocated_capital=...)`).
- **Purpose:** Dashboard / Strategy Selector can show a **recommendation** and store it in the competition DB. That is for display and possible future use (e.g. a config sync job). The running engine does **not** use it.

**Documentation and UI:**

- **README:** States that allocation is config-based (equal or custom percentages); 70/20/10 is a score-based recommendation in the dashboard only.
- **Leaderboard UI:** Shows "Allocation" from competition DB with note that engine uses config only (attribution_note in API; inline note on page).

**Behavior and documentation match:** Engine = config. Dashboard = config + optional 70/20/10 recommendation (display/DB only).

---

## 3. Strategy Graduation Enforcement

**Do graduation stages gate behavior?**

- **No.** Graduation updates the **competition DB** (e.g. `Strategy.update(..., trading_stage=..., allocated_capital=...)`). The **engine** (run_bot → strategy_manager) does **not** read `trading_stage` or DB `enabled` for execution. It uses only:
  - `config["strategies"]["enabled"]` — which strategies to run
  - Execution gate (paper_trading, kill_switch, pause)

So graduation is **symbolic**: it tracks stage and recommended capital for display and future use; it does not by itself enable/disable execution.

**Labeled in UI and docs:**

- **Leaderboard:** Note on page: "Graduation stage and allocation are for tracking; execution is controlled by config and the execution gate."
- **STRATEGY_GRADUATION.md:** Section added: "Graduation stages are symbolic … They do not gate execution."
- **README:** Strategy Graduation bullet updated to state stages are symbolic and execution is controlled by config and execution gate.

**If you want graduation to gate execution:** You would need to change the engine to (e.g.) respect `Strategy.get_enabled()` or `trading_stage` from the DB. That is out of scope for Phase 7D; behavior is documented as symbolic.

---

## 4. Data Pipeline Enforcement Visibility

**Does bad data pause execution or trigger alerts?**

- **DataValidator** (`services/data_validator.py`): Validates price (vs API), data freshness, and liquidity. Provides `validate_before_trade()`.
- **Usage:** DataValidator is **not** called from `run_bot.py` or the main execution path. No integration in the engine loop.
- **Result:** Bad or stale data does **not** automatically pause execution or trigger alerts from this validator.

**What does pause execution / trigger alerts:**

- **Execution gate** (Phase 7A): pause (control.json), kill_switch (config/DB). No trade runs when gate is closed.
- **Risk manager** (e.g. circuit breakers): Can pause trading and trigger alerts on drawdown/loss limits (separate from data validation).
- **Strategy health monitor:** Can auto-disable strategies in the DB (affects leaderboard/competition; engine currently uses config for which strategies run, per Phase 7A notes).

**Documentation:**

- **README:** Safety Controls updated: "Data pipeline: Data validation exists (DataValidator) but is not wired into the engine loop. Bad data does not automatically pause execution or trigger alerts."
- **This doc:** Explicit that enforcement is **partial** — validation exists, integration into execution is not present.

---

## 5. Exit Condition

- **Strategy intelligence UI:** Leaderboard shows rankings, health, attribution (allocation), graduation stage; filters and drill-down are read-only.
- **README:** No feature misrepresents strategy behavior, health, or allocation; capital allocation and graduation are described accurately (config vs 70/20/10, symbolic stages).
- **PHASE_7D_STRATEGY_ALIGNMENT.md:** Delivered; single source of truth for alignment.

**No new strategies, no live trading, no invented metrics, no UI that alters execution behavior.**
