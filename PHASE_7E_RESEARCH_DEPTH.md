# Phase 7E: Research & Testing Depth (Final Pre-Run Phase)

**Role:** Quant Research Engineer / Analytics UX Designer / Backtesting Platform Owner  
**Mission:** Make the system useful for real research before firing up the bot for continuous testing.

---

## 1. Scope

- **UI scope:** Results & Analysis pages only (Analytics, Strategy Comparison & Research).
- **No execution impact:** All research features are read-only; no live controls, no engine changes.
- **Exit condition:** A quant can meaningfully test, compare, and export strategies without touching the engine.

---

## 2. Deliverables Implemented

### 2.1 Backtest comparison views

- **Strategy Comparison page** (`/strategy_comparison`):
  - **Compare by date range:** Select 2–4 strategies, set start/end date, click “Run & Compare” to run backtests and compare metrics and equity curves.
  - **Compare saved runs:** Recent backtest runs are stored (in-memory, last 50). List saved runs, select 2+ by `run_id`, and compare.
  - **Metrics table:** Total return, win rate, Sharpe ratio, max drawdown, total trades; best value per row highlighted.
  - **Equity curves:** Multi-series line chart for compared runs/strategies.
- **APIs:**
  - `POST /api/backtest/run` — Run backtest; response includes `run_id`; result is stored for comparison.
  - `GET /api/backtest/runs?limit=20` — List recent backtest runs.
  - `GET /api/backtest/runs/<run_id>` — Get one run by id.
  - `POST /api/strategies/compare` — Body: `run_ids` (array) **or** `strategies` + `start_date` + `end_date`. Returns `comparison` (metrics by label) and `equity_curves` (label → array of equity values).

### 2.2 Parameter sweep visualization

- **Strategy Comparison page — Parameter Sweep section:**
  - Strategy dropdown, param ranges as JSON (e.g. `{"lookback": [10,20], "threshold": [0.02,0.05]}`), optimization metric (Sharpe ratio, return %, win rate).
  - “Run sweep” calls optimizer; results shown in a table (parameters, score, return %, win rate) and a bar chart (score by combo).
  - Export sweep results as CSV or JSON.
- **APIs:**
  - `POST /api/optimizer/run` — Body: `strategy_name`, `param_ranges`, `optimization_metric`, optional `start_date`/`end_date`. Returns full optimization result including `all_results`.
  - `GET /api/optimizer/history` — Returns optimization history for the session.

### 2.3 Regime-based slicing

- **Time:** Start date and end date on Analytics and on Strategy Comparison (for backtest and for exports).
- **Volatility:** Optional `volatility_regime` = `low` | `med` | `high`. Trades are classified by |PnL| percentile (terciles); filter keeps only trades in the chosen band.
- **Event windows:** Optional `event_window_start` and `event_window_end` (ISO dates). Only trades whose `entry_time` falls in that window are included.
- **Where applied:**
  - **Analytics page:** “Regime filters” card: start/end date, volatility regime dropdown, event window start/end. “Apply & refresh” reloads strategy performance (and exports use the same filters).
  - **APIs:**  
    - `GET /api/analytics/strategy_performance` accepts query params: `start_date`, `end_date`, `volatility_regime`, `event_window_start`, `event_window_end`.  
    - `GET /api/analytics/export?format=csv|json` accepts the same regime params.

### 2.4 Exportable results (CSV and JSON)

- **Analytics:**
  - **Export CSV:** `GET /api/analytics/export?format=csv` (optional regime params). Downloads `analytics_export.csv`.
  - **Export JSON:** `GET /api/analytics/export?format=json` (optional regime params). Downloads `analytics_export.json` (structure: `{ "strategies": [ ... ] }`).
- **Research export (unified):**  
  `GET /api/research/export?type=<type>&format=<format>[&...]`
  - `type=analytics` — Strategy performance (optionally filtered by regime). Same regime params as above.
  - `type=comparison` — Backtest comparison rows. Query: `run_ids=id1&run_ids=id2&...`.
  - `type=sweep` — Parameter sweep history (optimal parameters and metrics per run).
  - `format=csv` or `format=json`. JSON returns attachment with `{ "data": [ ... ] }`.

---

## 3. Code and UX Summary

| Component | Location | Notes |
|-----------|----------|--------|
| Backtest run storage | `services/research_service.py` | `store_backtest_run`, `get_backtest_runs`, `get_backtest_run`, `get_run_ids_for_comparison`; in-memory deque + dict, max 50 runs. |
| Regime filter helper | `services/research_service.py` | `filter_trades_by_regime(trades, start_date, end_date, volatility_regime, event_window_start, event_window_end)`. |
| Strategy analytics from trades | `services/strategy_analytics.py` | `get_all_strategies_performance_from_trades(trades)` for regime-filtered trade lists. |
| Backtest / compare / optimizer / export routes | `dashboard/app.py` | See sections above; no execution or live controls. |
| Strategy comparison UI | `dashboard/templates/strategy_comparison.html` | Date range + run backtests, saved runs list + compare by run_ids, metrics table, equity chart, parameter sweep form + table + chart, export comparison/sweep. |
| Analytics regime + export | `dashboard/templates/analytics.html`, `dashboard/static/js/analytics.js` | Regime filters card; export CSV/JSON; `getRegimeQueryString()`, `applyRegimeAndRefresh()`. |

---

## 4. How a quant uses it (without touching the engine)

1. **Backtest:** Run backtests from the dashboard or by calling `POST /api/backtest/run`; each run is stored and gets a `run_id`.
2. **Compare:** On Strategy Comparison, either run 2–4 strategies over the same date range or select 2+ saved runs; view metrics table and equity curves; export comparison via “Export CSV”/“Export JSON” (using `type=comparison` and `run_ids`).
3. **Parameter sweep:** On Strategy Comparison, set strategy, param ranges (JSON), and metric; run sweep; view table and bar chart; export via “Export sweep CSV/JSON” (or `type=sweep` on `/api/research/export`).
4. **Regime slicing:** On Analytics, set date range, volatility regime, and/or event window; “Apply & refresh”; strategy performance and all downstream views use the filtered set; export CSV/JSON with the same regime.
5. **Exports:** All of the above support CSV and JSON for use in notebooks, spreadsheets, or other tools.

---

## 5. Exit condition

**A quant can meaningfully test, compare, and export strategies without touching the engine.**

- Testing: backtest run + parameter sweep (optimizer).
- Compare: side-by-side backtest comparison (by date range or by saved run_ids) with metrics and equity curves.
- Regime slicing: time, volatility, and event-window filters on analytics and exports.
- Export: CSV and JSON for analytics, comparison, and sweep.

No execution impact: research features are confined to Results & Analysis (Analytics and Strategy Comparison) and to read-only APIs; no live trading or engine controls are changed.
