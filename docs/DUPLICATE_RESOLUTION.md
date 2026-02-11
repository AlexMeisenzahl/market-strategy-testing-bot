# Duplicate Module Resolution

This document records canonical module choices and deprecated/archived modules.

## StrategyManager

| Location | Status | Reason |
|----------|--------|--------|
| `strategy_manager.py` (root) | **CANONICAL** | Used by run_bot; accepts ExecutionEngine; integrates with execution flow |
| `strategies/strategy_manager.py` | **ARCHIVED** | Different interface (no execution_engine); orphaned (no imports found) |

**Action:** `strategies/strategy_manager.py` marked deprecated with docstring. Use root `strategy_manager` for production.

## Risk Manager

| Location | Status | Reason |
|----------|--------|--------|
| `services/risk_manager.py` | **CANONICAL** | Used by run_bot; RiskManager with position tracking, stop-loss, take-profit |
| `risk_manager.py` (root) | **SEPARATE** | DrawdownProtection - circuit breakers; used by demo_risk_management, test_risk_modules |

**Note:** These serve different purposes. Root `risk_manager` provides DrawdownProtection (circuit breakers). Services provides RiskManager (position risk). Both are retained. Demos use root for DrawdownProtection demos.

## DataValidator

| Location | Status | Reason |
|----------|--------|--------|
| `services/data_validator.py` | **CANONICAL** (trading) | Price validation, freshness; for trading data |
| `dashboard/services/data_validator.py` | **RENAMED** CsvDataValidator | CSV structure validation for display; different purpose |

**Action:** Dashboard DataValidator renamed to CsvDataValidator to avoid name collision.

## CoinGecko Client

| Location | Status | Reason |
|----------|--------|--------|
| `clients/coingecko_client.py` | **CANONICAL** | Extends BaseClient; used by run_bot data clients |
| `apis/coingecko_client.py` | **SEPARATE** | Different interface; used by crypto_price_manager, tests |

**Note:** Different interfaces (BaseClient vs standalone). Both retained. `apis/` serves free-API ecosystem; `clients/` serves main execution path.
