# Production Readiness Audit Report
**Market Strategy Testing Bot**  
**Date:** February 10, 2025  
**Scope:** Full repository analysis — structural mapping, boot validation, wiring audit, risk assessment  
**Audit Type:** Read-only analysis (no code modifications)

---

## PHASE 1 — Structural Mapping

### 1.1 Directory Tree (Depth 4)

```
market-strategy-testing-bot/
├── .github/workflows/
│   ├── ci.yml
│   └── release.yml
├── analysis/
│   ├── __init__.py
│   ├── diagnostics.py
│   ├── suggestions.py
│   └── trade_context.py
├── api/
│   ├── __init__.py
│   ├── server.py
│   ├── middleware/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   └── rate_limit.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── markets.py
│   │   ├── positions.py
│   │   ├── strategies.py
│   │   └── trades.py
│   └── websocket/
│       ├── __init__.py
│       └── manager.py
├── apis/
│   ├── __init__.py
│   ├── binance_client.py
│   ├── coingecko_client.py
│   ├── polymarket_subgraph.py
│   ├── price_aggregator.py
│   └── README.md
├── clients/
│   ├── __init__.py
│   ├── base_client.py
│   ├── coingecko_client.py
│   ├── mock_crypto_client.py
│   ├── mock_market_client.py
│   └── polymarket_client.py
├── config/
│   ├── __init__.py
│   └── config_loader.py
├── dashboard/
│   ├── app.py                    # Flask app entry
│   ├── websocket_server.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── config_api.py
│   │   ├── core.py
│   │   ├── data_sources_api.py
│   │   ├── emergency.py
│   │   ├── journal.py
│   │   ├── leaderboard.py
│   │   ├── settings.py
│   │   ├── strategies.py
│   │   └── system.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── analytics.py
│   │   ├── chart_data.py
│   │   ├── config_manager.py
│   │   ├── data_parser.py
│   │   ├── data_validator.py
│   │   ├── engine_state.py
│   │   └── trade_adapter.py
│   ├── static/                   # css, js, icons, manifest
│   └── templates/                # HTML templates
├── database/
│   ├── __init__.py
│   ├── competition_models.py
│   ├── models.py
│   ├── settings_models.py
│   └── (migrations via migrations/)
├── exchanges/
│   ├── __init__.py
│   ├── coinbase_client.py
│   ├── exchange_manager.py
│   └── kalshi_client.py
├── migrations/versions/
│   └── 001_complete_schema.py
├── monitoring/
│   ├── alerts.yml
│   ├── prometheus.yml
│   └── grafana/datasources/, grafana/dashboards/
├── scripts/                      # Shell scripts for backup, deploy, health-check
├── services/                     # 47+ service modules
├── state/
│   ├── bot_state.json
│   └── bot_state.backup.json
├── strategies/                   # 20 strategy modules
├── tests/
├── utils/
├── main.py                       # Canonical engine entry
├── run_bot.py                    # Bot loop + BotRunner
├── engine.py                     # ExecutionEngine
├── bot.py                        # TUI monitor (read-only)
├── start_dashboard.py            # Dashboard quick-start script
├── logger.py
├── strategy_manager.py           # Canonical StrategyManager (root)
├── risk_manager.py               # DrawdownProtection (root)
├── polymarket_api.py
├── config.yaml
└── requirements.txt
```

### 1.2 Entry Points

| Entry Point | Purpose | Command |
|-------------|---------|---------|
| **main.py** | Canonical engine entry | `python main.py` |
| **run_bot.py** | Same engine (main.py delegates to it) | `python run_bot.py` |
| **start_dashboard.py** | Dashboard quick-start | `python start_dashboard.py` |
| **dashboard.app** | Flask app module | `FLASK_APP=dashboard.app:app flask run` |
| **bot.py** | TUI monitor (read-only) | `python bot.py` |
| **api.server** | FastAPI mobile API | `python -m api.server` (or uvicorn) |

### 1.3 Flask App Initialization

- **Location:** `dashboard/app.py` line 82: `app = Flask(__name__)`
- **Blueprints:** config_api, leaderboard_bp, emergency_bp, data_sources_api, core_bp, journal_bp, settings_bp, strategies_bp, system_bp
- **SocketIO:** `socketio = init_socketio(app)` — WebSocket support via `dashboard/websocket_server.py`
- **Duplicate registration concern:** Blueprints `core_bp`, `journal_bp`, `settings_bp`, `strategies_bp`, `system_bp` are registered at line ~4678, after routes are defined inline in `app.py`. This works but creates a very large single-file app (~4700 lines).

### 1.4 Engine Loop Start

- **Location:** `run_bot.py` — `BotRunner.run()` (lines 778–865)
- **Flow:** `main()` → `BotRunner()` → `bot.run()` → `while self.running:` loop
- **Cycle:** `run_cycle()` every `scan_interval_seconds` (default 60)
- **Components in loop:** fetch markets, check alerts, check risk, run strategies, process opportunities, execute trades, check exits, write state

### 1.5 State/Log File Paths

| Path | Writer | Reader(s) | Purpose |
|------|--------|-----------|---------|
| `state/bot_state.json` | `run_bot.BotRunner._write_bot_state()` | `EngineStateReader`, `bot.py`, dashboard | Canonical engine state (balance, positions, status, PnL) |
| `state/control.json` | `bot.py` (pause/resume), dashboard emergency | `run_bot._read_control()`, `execution_gate._is_paused()` | Pause control |
| `logs/activity.json` | `run_bot._log_activity()` | `EngineStateReader`, `bot.py`, dashboard | Activity stream |
| `logs/trades.csv` | logger, paper trading engine | DataParser, dashboard | Trade log |
| `logs/opportunities.csv` | logger | DataParser | Opportunity log |
| `logs/errors.log` | logger | — | Errors/warnings |
| `logs/connection.log` | logger | — | Connection health |

All paths are relative to project root. No environment-based override for state/log directory.

### 1.6 Circular Imports

- **No confirmed circular imports** in the analyzed import graph.
- **Execution gate** uses lazy import for `emergency_kill_switch` to avoid DB-init ordering issues.
- **Potential concern:** `dashboard/app.py` imports ~70 modules at top level. A late import block at lines 2775–2790 imports `backtesting_engine`, `strategy_optimizer`, `research_service`, `alert_manager`, `database.models`. This suggests historical growth and possible tight coupling.

### 1.7 Unused/Orphaned Files

| File | Notes |
|------|-------|
| **apis/coingecko_client.py** | Duplicate of `clients/coingecko_client.py`; `run_bot` uses `clients.CoinGeckoClient` |
| **strategies/strategy_manager.py** | Different StrategyManager (no execution_engine); `run_bot` imports root `strategy_manager` |
| **risk_manager.py** (root) | Contains `DrawdownProtection`; `run_bot` uses `services.risk_manager.RiskManager`; root used only by `demo_risk_management.py`, `test_risk_modules.py` |
| **paper_trader.py** | Separate entry point; relationship to main engine unclear |
| **demo.py**, **demo_core_modules.py**, **demo_professional_modules.py** | Demo/example scripts; not production paths |
| **detector.py**, **liquidity_analyzer.py**, **performance_optimizer.py**, **monitor.py**, **performance_monitor.py**, **notifier.py**, **notification_rate_limiter.py**, **position_sizer.py**, **strategy_analyzer.py**, **tax_exporter.py**, **version_manager.py**, **quiet_hours.py** | Root-level modules; some may be legacy or optional |

### 1.8 Duplicate Responsibilities

| Responsibility | Location 1 | Location 2 | Risk |
|----------------|------------|------------|------|
| **StrategyManager** | `strategy_manager.py` (root) | `strategies/strategy_manager.py` | High — different interfaces; run_bot uses root only |
| **Risk manager** | `risk_manager.py` (DrawdownProtection) | `services/risk_manager.py` (RiskManager) | Medium — different roles; both exist |
| **DataValidator** | `services/data_validator.py` | `dashboard/services/data_validator.py` | Low — likely different scopes (backend vs UI) |
| **CoinGecko client** | `clients/coingecko_client.py` | `apis/coingecko_client.py` | Medium — duplication; clients/ is canonical |
| **Logger** | `logger.py` (custom Logger) | Uses `log_info`, `log_error`, etc.; aliases `info`, `error` | Low — single implementation, API compatible |

---

## PHASE 2 — Boot Validation

### 2.1 Primary Execution Script (main.py)

**Result:** ✅ **SUCCESS**

- `python3 main.py` boots successfully.
- Output: `>>> run_bot.py STARTED <<<`, `>>> Bot main loop starting <<<`, `❤️ Bot heartbeat – cycle started`
- Engine loop starts; cycle runs (markets, strategies, state write).
- **Note:** `main.py` does not define `main`; it imports `from run_bot import main as run_engine` and calls it. Direct `from main import main` fails for that reason.

### 2.2 Flask Dashboard

**Result:** ❌ **FAILURE — Floating Point Exception (Signal 8)**

- `from dashboard.app import app` → process crashes with `Floating point exception: 8`
- `FLASK_APP=dashboard.app:app flask routes` → same crash.
- **Likely cause:** Numerical library (numpy/scipy) or native extension, possibly in:
  - `services.strategy_competition` (uses numpy)
  - `services.performance_tracker` or analytics
  - `monitoring.metrics`
  - `database` / SQLAlchemy initialization
- **Environment:** Python 3.9, macOS (darwin 21.6.0); LibreSSL 2.8.3; urllib3 OpenSSL warning present.

### 2.3 Flask Routes

**Result:** ❌ **Cannot execute** — dashboard import crashes before routes are registered.

### 2.4 Tracebacks / Failure Explanation

| Failure | Cause |
|---------|-------|
| `from main import main` | `main` is not defined in main.py; it is in run_bot |
| Dashboard FPE (Signal 8) | Unhandled floating-point or SIGFPE in numerical/extension code during import; common with numpy/scipy on some platforms or misaligned binaries |

---

## PHASE 3 — Wiring Audit

### 3.1 Dashboard ↔ State ↔ Engine Connections

```
┌─────────────────┐     writes      ┌──────────────────────┐     reads
│  run_bot.py     │ ──────────────► │ state/bot_state.json │ ◄─────────────
│  BotRunner      │                 │ logs/activity.json   │
└────────┬────────┘                 └──────────┬───────────┘
         │                                     │
         │  ExecutionEngine                    │
         │  (PaperTradingEngine)               │
         │                                     │
         ▼                                     ▼
┌─────────────────┐                 ┌──────────────────────┐
│ DataFlowManager │ ◄──set_engine───│ EngineStateReader    │
│ (when engine    │                 │ (dashboard/services/ │
│  set by BotRunner)                │  engine_state.py)    │
└────────┬────────┘                 └──────────┬───────────┘
         │                                     │
         └──────────────┬──────────────────────┘
                        │
                        ▼
              ┌─────────────────────┐
              │ dashboard/app.py    │
              │ (Flask routes)      │
              │ - Prefers engine    │
              │   state when avail  │
              └─────────────────────┘
```

### 3.2 Mismatched Paths

- All components use consistent paths: `state/bot_state.json`, `state/control.json`, `logs/activity.json`.
- Paths are derived from `Path(__file__).resolve().parent.parent` or `BASE_DIR` — correct when run from project root.
- **Risk:** If the process is started from a different working directory (e.g., scripts/, systemd), relative paths may resolve incorrectly. No `STATE_DIR` or `LOGS_DIR` env override.

### 3.3 Fragile Assumptions

| Assumption | Risk |
|------------|------|
| **Project root = cwd** | Scripts or systemd may run from other dirs; state/log paths break |
| **Single process** | Bot and dashboard are separate processes; dashboard reads files, engine writes. No file locking; possible partial reads during write (mitigated by atomic temp+rename in `_write_bot_state`) |
| **Config at config.yaml** | Fallback to config.example.yaml; no env override for config path |
| **DataFlowManager singleton** | `set_execution_engine` called only by BotRunner; standalone dashboard has `_execution_engine = None` and falls back to PortfolioTracker/TradeLogger |
| **control.json schema** | Expects `{"pause": true/false}`; invalid JSON = fail-open (not paused) |

### 3.4 Tight Coupling

- **dashboard/app.py** imports 70+ modules; monolithic structure.
- **run_bot.py** imports 8 strategies directly by name; adding a strategy requires code change.
- **Execution gate** depends on: config, control.json, emergency_kill_switch (DB). Emergency kill uses DB — DB must be initialized before gate checks.
- **EngineStateReader** and **DataFlowManager** both provide portfolio/state; dashboard prefers engine state when available, but logic is spread across routes.

---

## PHASE 4 — Risk Assessment

### 4.1 Architecture Summary

- **Engine:** Single-process loop (`run_bot.BotRunner`) with `ExecutionEngine` and `PaperTradingEngine`. Strategies emit opportunities; `StrategyManager` executes best via engine. Execution gate (pause, kill_switch, paper-only) enforced before every trade.
- **Dashboard:** Flask app with SocketIO; reads state from files and optional DataFlowManager/engine. Does not execute trades.
- **State flow:** Engine writes `bot_state.json` and `activity.json` each cycle; dashboard and TUI read them. Control (pause) via `control.json`.
- **Data sources:** Polymarket/CoinGecko via `clients/`; mock clients when APIs unavailable.

### 4.2 Top 10 Structural Risks

1. **Dashboard fails to boot (FPE)** — Flask app cannot start in current environment; blocks production deployment of dashboard.
2. **Dual StrategyManager** — Root vs strategies/; run_bot uses root; demos use strategies/; confusion and drift risk.
3. **Dual Risk Manager** — Root `DrawdownProtection` vs `services.risk_manager.RiskManager`; different interfaces and roles.
4. **Monolithic dashboard/app.py** — ~4700 lines, 70+ imports; hard to maintain and test.
5. **No state/log path override** — Relative paths; fails if cwd ≠ project root.
6. **Client duplication** — apis/ vs clients/ for CoinGecko; maintenance burden.
7. **DataValidator not wired** — Exists but not in engine loop; bad data does not auto-pause.
8. **Heavy dashboard import chain** — Many services loaded at import; FPE suggests numerical/extension issue in chain.
9. **Orphaned/legacy root modules** — detector, liquidity_analyzer, etc.; unclear ownership.
10. **DB ordering** — Execution gate uses emergency kill (DB); init order must be correct.

### 4.3 Runtime Risks

- **File-based state** — No locking; concurrent readers during write (atomic rename mitigates).
- **Activity log unbounded growth** — Trimmed to 1000 entries in `_log_activity`; acceptable.
- **Silent state write failure** — `_write_bot_state` catches all exceptions and does not surface; dashboard may show stale state.
- **Execution gate control_path** — Defaults to `Path(__file__).parent.parent / "state" / "control.json"`; correct for standard layout.

### 4.4 Stability Risks

- **No health endpoint for engine** — Dashboard infers health from bot_state.json; no process liveness check.
- **No circuit breaker on API calls** — Polymarket/CoinGecko failures fall back to mock; no explicit backoff.
- **Logger writes to files** — No rotation; logs can grow indefinitely.
- **Rate limiter** — Flask-Limiter uses `memory://`; resets on process restart; no distributed rate limiting.

### 4.5 What Would Break in Production

| Scenario | Impact |
|----------|--------|
| **Dashboard FPE on import** | Dashboard cannot run; monitoring/control UI unavailable |
| **Wrong working directory** | State/log paths wrong; engine writes to unexpected location; dashboard reads empty/wrong files |
| **DB unavailable at startup** | Emergency kill may raise; execution gate can assume kill active (fail-safe) |
| **Config file missing** | Engine uses defaults; dashboard may fail if config_loader is required |
| **Redis not running** | Flask-Caching/redis in requirements; if used, cache fails; need to confirm cache backend |
| **OpenSSL/LibreSSL mismatch** | urllib3 warning; possible TLS issues with external APIs |
| **Multiple bot instances** | No coordination; both write to same state files; undefined behavior |
| **Kill switch in config** | `kill_switch: true` in YAML stops all trading; correct but must be understood |

---

## Recommendations (Non-Binding)

1. **Resolve dashboard FPE** — Profile import chain; isolate numpy/scipy/DB init; consider lazy loading of heavy modules.
2. **Unify StrategyManager** — Deprecate strategies/strategy_manager or make it a thin wrapper; single source of truth.
3. **Clarify risk managers** — Document DrawdownProtection vs RiskManager; consider merging or explicit delegation.
4. **Add STATE_DIR / LOGS_DIR env** — Allow override for container/systemd deployments.
5. **Split dashboard/app.py** — Move routes to blueprints; reduce top-level imports.
6. **Wire DataValidator** — Integrate into engine loop or document intentional exclusion.
7. **Remove or consolidate apis/coingecko_client** — Use clients/ as canonical.

---

*End of audit report. No code changes were made during this audit.*
