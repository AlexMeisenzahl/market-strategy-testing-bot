# Phase 6A — Product & UI Audit

**Status:** Complete (Step 1, no code)  
**Authority:** Read-only with respect to execution engine. UI consumes existing state only.

---

## 1. Engine State Contracts (Canonical)

### 1.1 `state/bot_state.json` (written by `run_bot.py`)

Schema written each cycle by `BotRunner._write_bot_state()`:

| Field | Type | Description |
|-------|------|-------------|
| `connection.healthy` | bool | API health |
| `connection.response_time_ms` | number | Latency |
| `rate_limit.usage_pct` | number | Rate limit usage |
| `rate_limit.remaining` | int | Remaining requests |
| `rate_limit.reset_seconds` | int | Reset countdown |
| `trading.opportunities_found` | int | Total opportunities detected |
| `trading.trades_executed` | int | Total paper trades |
| `trading.paper_profit` | float | Total paper P&L (from engine metrics) |
| `positions` | array | From `execution_engine.get_positions(prices)` — each item: symbol/market, quantity, avg_price, current_value, etc. |
| `balance` | float | From `execution_engine.get_balance()` |
| `last_update` | string | ISO timestamp |
| `status` | string | `"running"` \| `"paused"` \| `"stopped"` |
| `runtime_seconds` | int | Uptime |

**Note:** A different schema may exist on disk if another writer (e.g. strategy_competition) has written the file; the dashboard’s `EngineStateReader` expects the run_bot schema above.

### 1.2 `logs/activity.json` (written by `run_bot.py`)

- **Format:** JSON array of activity objects (last 1000 kept).
- **Fields per entry:** `timestamp` (ISO), plus type-specific fields.
- **Activity types logged by engine:**
  - `opportunity_found` — strategy, market_id, market_name, yes_price, no_price, profit_margin, action (`executing` \| `skipped`), reason
  - `trade_executed` — strategy, count
  - `alert_triggered` — alert_id, message

### 1.3 Strategy leaderboard

- **Source:** `services/strategy_competition.py` → `StrategyCompetition.get_leaderboard()`.
- **Data:** DB (Strategy model, StrategyPerformanceSnapshot). Not from `bot_state.json`.
- **API:** `/api/leaderboard/` (blueprint), `/api/leaderboard` (legacy in app.py). Dashboard can use either; leaderboard page uses blueprint.

---

## 2. Feature → UI → Data Source Mapping

| Feature (README / product) | Current UI location | Data source | Notes |
|----------------------------|----------------------|-------------|--------|
| **Market data** | Crypto ticker (index); market_reality; /api/market/live | CryptoPriceManager; market APIs | Live prices: external APIs. No engine-written market list in state. |
| **Strategy definition** | Settings (strategies); Strategy comparison; Leaderboard | config.yaml (config_manager); DB (Strategy) | Enable/disable and params in config; leaderboard from DB. |
| **Backtesting** | /api/backtest/run; strategy_comparison; analytics | backtesting_engine | Backtest run is POST; results from service, not from engine state files. |
| **Paper trading** | Overview (P&L, trades); Control; Positions; Execution | state/bot_state.json (trading.*, positions, balance); logs/activity.json | Primary source for “live” paper state is bot_state + activity. |
| **Execution** | Control (start/stop); Positions; Trade log | bot_state (status, positions); activity.json (trade_executed); logs/trades.csv | Start/stop is process-level (TUI/bot.py); dashboard is read-only. |
| **Monitoring** | Overview; Control (status); Recent activity; Leaderboard; Logs | bot_state.json; activity.json; leaderboard API; logs/bot.log | Engine health = bot_state.status + connection; activity = activity.json. |
| **Trades history** | Trades page; Export | data_parser → logs/trades.csv | CSV may be written by engine or other path; parser has sample fallback. |
| **Opportunities history** | Opportunities page | data_parser → logs/opportunities.csv | Same as trades; CSV + optional sample fallback. |
| **Charts (P&L, daily, strategy)** | Overview; Analytics | chart_data → data_parser → trades.csv | Derived from CSV, not from bot_state. |
| **Notifications** | Settings (email, desktop, Telegram) | config + notification services | Config and external services; not in engine state. |
| **Tax reports** | Tax page; /api/tax/* | data_parser / tax_report_generator | From trades/positions data, not bot_state. |

---

## 3. Proposed Navigation & Information Architecture

### 3.1 Top-level sections (trading-first)

1. **Overview** — Account status (paper), engine health, today’s P&L and key metrics, active strategies.
2. **Strategies** — Enable/disable strategies, configure parameters, clone/save presets (when backend supports).
3. **Markets & Charts** — Live prices, indicators, timeframes (use existing ticker/charts; mark unsupported bits).
4. **Execution** — Paper trading status, positions, trade log (activity + CSV where applicable).
5. **Results & Analysis** — Backtests, performance comparisons, leaderboard.
6. **System Status** — Logs, diagnostics, alerts.

### 3.2 Proposed URL and nav structure

- `/` — Overview (default).
- `/strategies` — Strategy list, enable/disable, config (read/write config only; no execution changes).
- `/markets` — Markets & charts (existing charts + ticker; link from Overview).
- `/execution` — Status, positions, trade log (aggregate from bot_state + activity + CSV).
- `/results` — Backtests, comparisons, leaderboard (existing leaderboard + strategy_comparison).
- `/system` — Logs, health, alerts.

Existing routes to keep but align under this IA: `/leaderboard`, `/analytics`, `/opportunities`, `/trade_journal`, `/alerts`, `/settings`, `/api_keys`, etc. — either as sub-views or linked from the six sections.

### 3.3 Mobile (iPhone-first)

- **Use for:** Monitoring, pause/enable strategies, reviewing performance.
- **Patterns:** Bottom nav (Overview, Strategies, Execution, Results, More), collapsible panels, summary-first layouts, one-handed actions.
- **Current state:** index.html has bottom-nav and slide-out “More”; desktop has top nav. Phase 6A will align mobile nav labels and targets with the six sections above.

---

## 4. UI Elements to Disable or Annotate (Missing or Partial Backend)

- **Start/Stop/Restart in dashboard** — Engine is started via `python run_bot.py` / `python bot.py`; dashboard does not start/stop process. **Action:** Keep UI but show “Engine runs via python run_bot.py. Use TUI (python bot.py) for pause/resume.” (already present in get_bot_status). Disable or make read-only any control that implies process start/stop from the web.
- **Strategy “clone / save presets”** — No backend for presets yet. **Action:** Hide or show as “Coming soon” until an API exists.
- **Backtest “Run” from UI** — Backend exists (`/api/backtest/run`); ensure it does not write to execution state. **Action:** If backtest only reads config and writes to its own result store, keep; else annotate or disable.
- **Real-time WebSocket push** — Optional; dashboard can poll. **Action:** If WebSocket is not wired to engine state, show “Live updates: polling every Ns” and do not imply true push.
- **Derived metrics not from engine** — e.g. Sharpe, max drawdown in Overview. **Action:** If not computed by engine (e.g. not in bot_state or activity), source from CSV/analytics and label “From trade history” or disable until engine provides them.
- **Leaderboard when DB has no strategies** — Returns empty. **Action:** Show “No strategy data yet” instead of empty table with no message.
- **Crypto ticker / market reality** — Depends on external APIs. **Action:** Show “Data from external API” and handle errors (e.g. “Unavailable”) without implying engine failure.
- **Tax reports** — Depend on trades/positions data. **Action:** If no trades.csv or no data, show “No data for period” and disable export for that period.

---

## 5. Data Source Summary

| Data need | Primary source | Fallback |
|-----------|----------------|----------|
| Paper account balance, P&L, status, runtime | state/bot_state.json | None (show “Engine not running”) |
| Positions | state/bot_state.json `positions` | position_tracker (if no engine state) |
| Recent activity stream | logs/activity.json | [] |
| Trades list (history) | logs/trades.csv via data_parser | Sample only if configured |
| Opportunities list | logs/opportunities.csv via data_parser | Sample only if configured |
| Charts (cumulative/daily P&L, strategy) | data_parser → trades.csv | Empty or message |
| Leaderboard | Strategy competition (DB) | [] |
| Bot process status | bot_state.status; else process scan for run_bot.py/main.py/bot.py | Stopped |
| Config (strategies, notifications) | config.yaml via config_manager | Read-only display |

---

## 6. Audit Checklist

- [x] README and dashboard README reviewed.
- [x] Dashboard routes and app.py data flow reviewed.
- [x] Engine state contracts (bot_state.json, activity.json) documented.
- [x] Leaderboard and strategy competition data source identified.
- [x] Feature → UI → data source mapping produced.
- [x] Proposed navigation and IA defined.
- [x] List of UI elements to disable or annotate documented.

Next: **Step 2 — Core Dashboard Structure** (implement Overview, Strategies, Markets & Charts, Execution, Results & Analysis, System Status, with mobile-friendly layout and truthful labeling).
