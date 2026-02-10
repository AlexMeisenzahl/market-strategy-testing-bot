# Phase 6A — UX and Product Decisions

This document explains the major UX and product decisions for the trading-first dashboard (Phase 6A).

---

## 1. Trading performance over decoration

- **Decision:** No new decorative elements were added. Existing gradients and cards were kept; new sections (Execution, Strategies, Markets, Results, System) use the same dark card style and minimal chrome.
- **Rationale:** Dense, scannable information and clear hierarchy matter more than visual flair. Consistency with the existing dashboard reduces cognitive load.

## 2. Information architecture: six sections

- **Decision:** Primary navigation is structured into six areas: **Overview**, **Strategies**, **Markets & Charts**, **Execution**, **Results & Analysis**, **System Status**. Secondary items (Trades, Opportunities, Analytics, Tax, Settings, Control) remain available under “More” on mobile and as smaller nav items on desktop.
- **Rationale:** Aligns with the Phase 6A plan and separates “what’s running” (Overview, Execution), “what I can configure” (Strategies), “what I see in the market” (Markets), “how I did” (Results), and “health and ops” (System). Trades/Opportunities/Analytics are still one tap away for power users.

## 3. Read-only with respect to execution

- **Decision:** The dashboard never starts or stops the execution process. Control page keeps Start/Stop/Restart buttons but adds a clear note: “Engine runs via `python run_bot.py` or `python bot.py`. Use the TUI for pause/resume. Dashboard is read-only.”
- **Rationale:** Execution is canonical in the engine; the UI must not duplicate or override process lifecycle. Disabling or annotating controls avoids the impression that the dashboard can start/stop the bot.

## 4. Single source of truth for live state

- **Decision:** All “live” paper state (balance, status, positions, activity stream) is read from `state/bot_state.json` and `logs/activity.json` via the existing `EngineStateReader`. No new backend paths or derived trading metrics were introduced.
- **Rationale:** Keeps the UI truthful and avoids drift between engine and dashboard. When engine is not running, the UI shows “Engine not running” or zeros and does not invent data.

## 5. Execution page: status, positions, activity

- **Decision:** A dedicated **Execution** page shows: (1) paper status and last update, (2) balance and open position count, (3) positions table from engine state, (4) recent activity from `logs/activity.json` (opportunity_found, trade_executed, alert_triggered).
- **Rationale:** Matches the “paper trading status, positions, trade logs” requirement and gives one place to see “what the engine is doing right now” without touching execution logic.

## 6. Strategies page: leaderboard + config entry

- **Decision:** The **Strategies** page does not implement enable/disable or parameter editing in-dashboard. It provides: (1) short description of the leaderboard and link to `/leaderboard`, (2) short description of strategy config and link to Settings. A note states that “Clone / save presets” is not yet supported.
- **Rationale:** Enable/disable and parameters are ultimately in config/engine; the UI avoids guessing. Linking to existing leaderboard and settings keeps the flow clear and leaves room for a future presets API.

## 7. Markets & Charts: reuse, no new backend

- **Decision:** The **Markets & Charts** page reuses existing chart APIs (`/api/charts/cumulative-pnl`, `/api/charts/daily-pnl`) and renders the same data on dedicated canvases on that page. A short note explains that the crypto ticker uses external APIs and charts use `logs/trades.csv`.
- **Rationale:** No new chart or market endpoints; the UI stays truthful to current data sources and avoids implying “live” chart feeds that the engine does not provide.

## 8. Results & Analysis: links, no duplicate logic

- **Decision:** The **Results & Analysis** page links to Leaderboard, Strategy comparison, and mentions Backtest as “Run via API; UI trigger in Strategy comparison / Analytics.” No new backtest or comparison logic in the dashboard.
- **Rationale:** Results and backtesting are already served by existing pages and APIs; this page is a hub rather than a second implementation.

## 9. System Status: logs and health

- **Decision:** The **System Status** page shows recent logs (from `/api/logs/recent`) and a health summary (from `/api/health`). It links to Alerts and Control and states that start/stop is via terminal.
- **Rationale:** Gives a single place for “is the system healthy?” and “what did it log?” without adding new health or log pipelines.

## 10. Mobile: bottom nav and “More”

- **Decision:** Mobile bottom nav shows five items: **Overview**, **Strategies**, **Execution**, **Results**, **More**. “More” opens the slide-out menu with Markets, System, Trades, Opportunities, Analytics, Control, Tax, Settings.
- **Rationale:** Matches “monitoring, pausing/enabling strategies, reviewing performance” with one-handed access to the four main areas; detailed and secondary items stay in “More” to avoid clutter.

## 11. Disabled or annotated features

- **Start/Stop/Restart (Control):** Annotated as read-only; engine runs via CLI.
- **Clone / save presets (Strategies):** Shown as “not yet supported” until backend exists.
- **Backtest from Results:** Described as “Run via API; UI trigger in Strategy comparison / Analytics.”
- **Data source and health:** Overview and status indicators already show “Engine” vs “Historical” and connection state; no new fake “live” labels.

## 12. Accessibility and safety

- **Decision:** New tables (e.g. positions, activity) use semantic markup and avoid information-only images. Control and System pages use short, direct copy so users understand what is read-only and what is not.
- **Rationale:** Reduces the risk of users believing they can start/stop the bot or change execution from the dashboard when they cannot.

---

These decisions keep the dashboard aligned with the Phase 6A principles: **trading performance over decoration**, **clarity under load**, **confidence while trading**, **safe iteration**, and **read-only consumption of engine state**.
