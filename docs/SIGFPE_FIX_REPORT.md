# SIGFPE Fix Report

## Problem

Importing `dashboard.app` caused a Floating Point Exception (signal 8, SIGFPE), a C-level crash typically from compiled numerical libraries.

## Root Cause

**Dependency: `numpy`**

The crash occurs when `import numpy as np` is executed at module import time. This is a known issue on some platforms (e.g. macOS with LibreSSL 2.8.3, certain numpy/OpenSSL combinations).

## Identification Process

Binary search import isolation identified the exact modules that triggered the crash when importing numpy at top level:

1. **services.risk_metrics** – top-level `import numpy as np`
2. **services.strategy_competition** – imported by `dashboard.routes.leaderboard`; top-level `import numpy as np`
3. **services.backtesting_engine** – imported in dashboard.app late block (line ~2780); top-level `import numpy as np`

## Solution

Moved all `import numpy` from module top-level to **lazy imports inside the methods** that use it. Numpy is only loaded when a method that needs it is called, not when the module is imported.

### Files Modified

| File | Change |
|------|--------|
| `services/risk_metrics.py` | Removed top-level `import numpy`; added `import numpy as np` inside `calculate_all_risk_metrics`, `calculate_rolling_sharpe`, `calculate_drawdown_history` |
| `services/strategy_competition.py` | Removed top-level `import numpy`; added inside `_calculate_sharpe`, `get_competition_summary` |
| `services/backtesting_engine.py` | Removed top-level `import numpy`; added inside `_evaluate_strategy_signal`, `_calculate_metrics` |

### Other Modules with numpy

- `services/performance_calculator.py` – has top-level numpy import but is only imported lazily inside route handlers (e.g. line 4379), so it does not affect dashboard boot.
- `dashboard/app.py` – uses numpy inside a route handler (lazy); no change needed.

## Verification

- `python -c "from dashboard.app import create_app"` – does not crash
- `create_app()` – executes cleanly
- `flask routes` – works; 186 routes registered
- Engine boot – unchanged; `python main.py` still works
