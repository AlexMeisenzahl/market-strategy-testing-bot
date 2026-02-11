# Dashboard Panel → Data Contracts (Phase 9B)

Each dashboard section has a defined data source, fallback behavior, empty-state message, and degraded-mode behavior. No silent failures; no guessing.

---

## Mission Control Bar (header)

| Contract | Value |
|--------|--------|
| **Primary source** | `GET /api/dashboard/system` (engine state, config, execution gate) |
| **Fallback** | On error: show "Unknown", gate "closed", heartbeat "—" |
| **Empty state** | N/A (always shows at least labels) |
| **Degraded mode** | Engine running but no heartbeat yet: show "Stopped" until first successful system response; then show last_heartbeat and gate |

---

## Live Trades & Positions (overview table)

| Contract | Value |
|--------|--------|
| **Primary source** | `GET /api/dashboard/trades` (normalized open + closed from CSV + engine) |
| **Fallback** | On error: return `{ open: [], closed: [], count_open: 0, count_closed: 0 }`; UI shows "Error loading trades" in table body |
| **Empty state** | "No trades yet — engine running. Trades appear here as they open and close." |
| **Degraded mode** | Engine running but no trades yet: show empty state message; do not show "broken" |

---

## Strategy Status (overview list)

| Contract | Value |
|--------|--------|
| **Primary source** | `GET /api/dashboard/strategies` (names from data_parser + open positions + activity) |
| **Fallback** | On error: `{ strategies: [] }`; UI shows "No strategy data yet." |
| **Empty state** | "No strategy data yet." |
| **Degraded mode** | Engine running but no strategies in config/logs: show empty state |

---

## Overview metrics (Total P&L, Win rate, Open, Total trades)

| Contract | Value |
|--------|--------|
| **Primary source** | `GET /api/overview` (aggregates from engine + data_parser) |
| **Fallback** | On error: show $0.00, 0%, 0, 0; toast "Error loading data" |
| **Empty state** | Zero values are valid (no special message) |
| **Degraded mode** | Partial response: show whatever numbers returned; never crash |

---

## Cumulative / Daily / Strategy charts

| Contract | Value |
|--------|--------|
| **Primary source** | `GET /api/charts/cumulative-pnl`, `daily-pnl`, `strategy-performance` |
| **Fallback** | On error: leave previous chart or empty; toast on error |
| **Empty state** | Empty chart with "No data" or zero series |
| **Degraded mode** | Cap rendered points to 200 (see realtime_contract.js); partial data renders |

---

## Trades page (full table)

| Contract | Value |
|--------|--------|
| **Primary source** | `GET /api/trades?page=1&per_page=25` (paginated) |
| **Fallback** | On error: show "Error loading trades" in table body |
| **Empty state** | "No trades found" |
| **Degraded mode** | Pagination required; never render unbounded list |

---

## Opportunities page

| Contract | Value |
|--------|--------|
| **Primary source** | `GET /api/opportunities` (with optional filters) |
| **Fallback** | On error: show empty table + toast |
| **Empty state** | "No opportunities found" |
| **Degraded mode** | Empty array is valid |

---

## Diagnostics view

| Contract | Value |
|--------|--------|
| **Primary source** | `GET /api/dashboard/diagnostics` |
| **Fallback** | On error: show error in banner; sources list empty |
| **Empty state** | N/A (always shows at least section headers) |
| **Degraded mode** | Some sources ok, some failed: show per-source status |

---

## Execution gate semantics

- **Green (gate open)** = allowed to execute (paper or live per config).
- **Red (gate closed)** = execution blocked; reason shown (e.g. kill switch, paused).
- UI must never imply "safe" when gate is closed; never block UI on gate state.
