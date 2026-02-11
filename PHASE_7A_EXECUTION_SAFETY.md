# Phase 7A: Execution Safety & Control Truth

**Objective:** Guarantee that no trade can execute when the system is paused, killed, or paper-only.

---

## 1. Canonical Kill Switch

**Two sources are combined into one gate; either one stops execution:**

| Source | Location | How it is checked |
|--------|----------|-------------------|
| **Config kill switch** | `config.yaml` → `kill_switch: true` | Read by execution gate from `config` |
| **Emergency kill switch** | DB `config` table → `kill_switch_active` | Read via `services.emergency_kill_switch.kill_switch.is_active()` |

**Canonical rule:** If **either** is active, the execution gate returns **do not execute**. There is no bypass. The gate is implemented in **`services/execution_gate.py`** and used at every execution boundary.

---

## 2. Pause vs Kill Semantics

| Concept | Meaning | Resumable? | Where stored |
|--------|---------|------------|---------------|
| **Pause** | Temporary hold; engine skips trading cycles. | Yes (set `pause: false` in control.json or via TUI). | `state/control.json` → `"pause": true` |
| **Kill** | Hard stop; no trades until kill is deactivated and (for emergency) strategies may remain disabled. | Yes, but emergency kill deactivation does **not** auto re-enable strategies. | Config YAML and/or DB `kill_switch_active` |

**Enforcement:**

- **Pause:** The main loop in `run_bot.py` already skips `run_cycle()` when `self.paused` is True (read from `state/control.json`). The execution gate **also** checks pause so that any path that might execute a trade (e.g. via ExecutionEngine or PaperTrader) cannot run while paused.
- **Kill:** Enforced only in the execution gate. No trade can execute when config `kill_switch` is True or when emergency kill switch is active.

---

## 3. Where Enforcement Occurs

All of the following must pass the **same** gate: `services.execution_gate.may_execute_trade(config, control_path?)`.

| # | Location | When |
|---|----------|------|
| 1 | **`run_bot.BotRunner._execute_trades()`** | Before calling `strategy_manager.execute_best_opportunities()`. If gate closed, returns without executing any trade. |
| 2 | **`engine.ExecutionEngine.execute_trade()`** | First line of `execute_trade()`: if gate closed, returns `{"success": False, "error": reason}`. |
| 3 | **`services.paper_trading_engine.PaperTradingEngine.place_order()`** | At top of `place_order()`: if gate closed or config missing, returns error dict (defense in depth). |
| 4 | **`services.paper_trading_engine.PaperTradingEngine.execute_order()`** | At top of `execute_order()`: re-check before filling (order may have been placed before kill). |
| 5 | **`paper_trader.PaperTrader.execute_paper_trade()`** | After `can_trade()`; if gate closed, returns `None` (legacy/demo path). |

**Gate checks (all must pass):**

1. `config` is non-empty.
2. `config["paper_trading"]` is True (default True if missing).
3. `config["kill_switch"]` is not True.
4. Emergency kill switch (DB) is not active.
5. Engine is not paused (`state/control.json` → `"pause"` is not True).

If any check fails, the gate returns `(False, reason)` and the caller must **not** execute a trade.

---

## 4. Strategy Health and Execution

- **Strategy health monitor** (`services.strategy_health_monitor`): Runs against strategies in the **DB** (competition/leaderboard model). It can auto-disable strategies via `Strategy.update(..., enabled=0)`.
- **run_bot execution path**: Uses **config only** for which strategies run: `config["strategies"]["enabled"]`. It does **not** read DB `Strategy.enabled` or strategy health.
- **Result:** Health-based disables currently affect the **competition/leaderboard** (e.g. dashboard, leaderboard APIs) and any code that uses `Strategy.get_enabled()`. They do **not** currently filter run_bot’s execution. Making run_bot respect DB strategy enabled status would require StrategyManager (or run_bot) to query the DB and filter by `Strategy.get_enabled()`; that is out of scope for Phase 7A.

---

## 5. Exit Condition (Phase 7A)

**It is provably impossible for the engine to execute a trade when:**

- The system is **paused** (control.json `pause: true`), or  
- The system is **killed** (config `kill_switch: true` **or** emergency kill switch active), or  
- The system is **not paper-only** (`paper_trading` is False).

**Proof:** Every execution path that can record or perform a trade goes through one of the call sites above, and each of those call sites calls `may_execute_trade()`. If the gate returns “do not execute,” the path returns an error or None and does not execute a trade. No alternate code path bypasses the gate.
