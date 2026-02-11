# Phase 7B: Execution Path, Data Sources & UX Truth

**Objective:** One execution path, one trade data source, and no misleading UI or documentation.

---

## 1. Canonical Execution Path (HARD RULE)

| Component | Role | How to run |
|-----------|------|------------|
| **Engine** | Only process that executes strategies and trades | `python main.py` (which starts `run_bot.py`) |
| **TUI (bot.py)** | Read-only terminal monitor; displays state from `state/bot_state.json` and `logs/activity.json` | `python bot.py` (optional) |

**Rules enforced:**

- **main.py** is the only entry point for the execution engine. It delegates to `run_bot.py`; there is no other way to run the engine.
- **bot.py** does not fetch markets, run strategies, or execute trades. It is a monitor only. Pause/resume is via `state/control.json`.
- **ProcessManager** (used by the dashboard) starts and stops **main.py**, not bot.py. `is_bot_running()` checks for a process running `main.py` or `run_bot.py` (and for a PID file written when the dashboard starts the engine).
- **force_stop_all** and process scan look for `main.py`, `run_bot.py`, or `start_dashboard.py` (no longer for `bot.py`).

**Code locations:**

- `main.py` – docstring and single call to `run_bot.main()`.
- `bot.py` – docstring states it is TUI-only and tells users to run `python main.py` for the engine.
- `services/process_manager.py` – `start_bot()` runs `python3 main.py`; `is_bot_running()` checks for `main.py` or `run_bot.py`.

---

## 2. Dashboard Truthfulness

**Before (Phase 7A audit):** Dashboard had Start/Stop buttons that only updated in-memory status; they did not start or stop any process. Copy suggested the dashboard could not start/stop the engine.

**After (Phase 7B):**

- **Start Engine / Stop Engine / Restart Engine** – Actually start or stop the engine process via `ProcessManager.start_bot()` / `stop_bot()` / `restart_bot()` (which run `main.py`).
- **Status** – Reflects whether the engine (main.py/run_bot.py) is running: from engine state when available, else from ProcessManager PID file or a process scan for `main.py`/`run_bot.py`.
- **Labels** – UI uses “Engine” and “Engine Control” (not “Bot” where it means the engine). Toasts say “engine” (e.g. “Failed to start engine”).
- **Instructions** – Control page and system settings say: start the engine with `python main.py` in a terminal or use the dashboard buttons; optional TUI is `python bot.py`.

**Code locations:**

- `dashboard/app.py` – `/api/bot/status`, `/api/bot/start`, `/api/bot/stop`, `/api/bot/restart` call ProcessManager and return real success/failure.
- `dashboard/templates/index.html` – “Engine Control”, “Start Engine”, “Stop Engine”, “Restart Engine”, and the info note about `main.py` / `bot.py`.
- `dashboard/templates/system_settings.html` – Restart note references `python main.py` and states that the dashboard can start/stop the engine.
- `dashboard/static/js/dashboard.js` – Toasts and confirm message use “engine”.

---

## 3. Single Trade History Source

**Canonical source:** `logs/trades.csv`

- Written by **Logger** (`logger.py`) from the engine, strategies, and paper execution paths.
- Read by **DataParser** (`dashboard/services/data_parser.py`) for the dashboard.

**Unified usage:**

- **Charts** – Distribution, cumulative, and other trade-based charts use `data_parser.get_all_trades()` (which reads from `logs/trades.csv` with caching).
- **Analytics** – Performance metrics, strategy performance, and tax reports use `data_parser.get_all_trades()` (or equivalent) instead of `DataFlowManager().trade_logger`.
- **CSV export** – `/api/export/trades` serves the contents of `logs/trades.csv` directly. If the file is missing, it returns a CSV with headers only.

**Deprecated for dashboard:**

- **TradeLogger** (`services/trade_logger.py`, `data/trades.json`) – No longer used by the dashboard. Docstring updated to state that the single source of truth is `logs/trades.csv` and that the dashboard uses DataParser. TradeLogger remains in the codebase for legacy/backtest use.

**Code locations:**

- `dashboard/app.py` – All trade data for charts, analytics, tax reports, and strategy performance use `data_parser`. Export reads `LOGS_DIR / "trades.csv"`.
- `dashboard/services/data_parser.py` – Reads `logs/trades.csv` (and `opportunities.csv`); used by ChartDataService, AnalyticsService, and the above routes.

---

## 4. README Corrections

**“How to Run the Bot” → “How to Run the Engine”:**

- States that there is **one execution path**: the engine runs only via `main.py`.
- **Start the engine:** `python main.py` (or `python3 main.py`). Notes that the web dashboard can also start/stop it.
- **Optional TUI:** `python bot.py` – described as a read-only terminal dashboard that does not run the engine; pause/resume via `state/control.json`.
- **Stop the engine:** Ctrl+C in terminal, or “Stop Engine” on the dashboard.

**“Project Structure”:**

- Lists `main.py` as the canonical entry point (starts the engine).
- Lists `run_bot.py` as the execution engine (started only via main.py).
- Lists `bot.py` as “TUI monitor only (read-only; optional)”.
- States that `logs/trades.csv` is the single source of truth for trade history.

**Dashboard README:**

- Describes Start/Stop/Restart as controlling the engine (main.py).
- API list describes `/api/bot/start` etc. as starting/stopping the engine.

---

## 5. Exit Condition

- **One execution path:** The only way to run the trading engine is `python main.py` (which runs `run_bot.py`). bot.py is TUI-only and does not execute trades.
- **One trade data source:** All dashboard trade data (charts, analytics, export) comes from `logs/trades.csv` via DataParser. TradeLogger/data/trades.json is not used by the dashboard.
- **No misleading UX:** Dashboard labels and copy refer to the “engine” and accurately describe starting/stopping it; Start/Stop/Restart actually control the engine process.
