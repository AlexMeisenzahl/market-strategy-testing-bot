# Structural Normalization Summary

This document summarizes the structural changes made for open-source readiness.

## Phase 1 — Package Structure

Created `market_strategy_bot/` package with:
- `__init__.py` – Package entry, version, run_engine/run_dashboard/run_tui/system_check
- `paths.py` – Environment-configurable paths (STATE_DIR, LOG_DIR, CONFIG_PATH)
- `runner.py` – Delegates to run_bot
- `dashboard_app.py` – Delegates to dashboard via create_app()
- `tui.py` – Delegates to bot.py
- `cli.py` – CLI entry (run-engine, run-dashboard, run-tui, system-check)
- `system_check.py` – System readiness validation

## Phase 2 — Duplicate Resolution

- **StrategyManager:** Root `strategy_manager.py` is canonical; `strategies/strategy_manager.py` archived (see docs/DUPLICATE_RESOLUTION.md)
- **Risk managers:** services/risk_manager (RiskManager) and root risk_manager (DrawdownProtection) serve different purposes; both retained
- **DataValidator:** Dashboard `DataValidator` renamed to `CsvDataValidator`; services `DataValidator` for trading data
- **CoinGecko:** clients/ and apis/ have different interfaces; both retained (see DUPLICATE_RESOLUTION.md)

## Phase 3 — Dashboard

- Added `create_app()` factory in dashboard/app.py
- `market_strategy_bot.dashboard_app.create_app()` uses factory pattern
- Full blueprint decomposition (analytics, admin, health) documented for future work

## Phase 4 — Configuration

- `STATE_DIR`, `LOG_DIR`, `CONFIG_PATH` env vars supported
- `market_strategy_bot.paths` provides get_state_dir(), get_log_dir(), get_config_path()
- run_bot, bot.py use env-configurable paths
- config_loader get_config() uses CONFIG_PATH env when config_path is None
- .env.example updated with path configuration section

## Phase 5 — Entry Points

- CLI: `msb run-engine | run-dashboard | run-tui | system-check`
- Options: `system-check --skip-dashboard --skip-cycle`
- pyproject.toml entry point: `msb = market_strategy_bot.cli:main`
- Also runnable: `python -m market_strategy_bot.cli run-engine`

## Phase 6 — Health Check

- `market_strategy_bot.system_check.run_checks()` validates:
  - Directories (state/, logs/)
  - Config file
  - Engine imports
  - Dashboard imports (optional, skip with --skip-dashboard)
  - Flask routes (optional)
  - Engine cycle smoke test (optional, skip with --skip-cycle)
- Returns 0 on success, 1 on failure

## Phase 7 — Packaging

- pyproject.toml with metadata, dependencies, optional extras (dashboard, dev)
- Project scripts: msb
- Minimal core deps; dashboard extras for full install

## Files Added/Modified

**Added:**
- market_strategy_bot/ (package)
- LICENSE
- CONTRIBUTING.md
- docs/DUPLICATE_RESOLUTION.md
- docs/STRUCTURAL_NORMALIZATION_SUMMARY.md

**Modified:**
- run_bot.py – env paths
- bot.py – env paths
- config/config_loader.py – CONFIG_PATH env
- dashboard/app.py – create_app(), CsvDataValidator import
- dashboard/services/data_validator.py – CsvDataValidator class
- .env.example – path config section
