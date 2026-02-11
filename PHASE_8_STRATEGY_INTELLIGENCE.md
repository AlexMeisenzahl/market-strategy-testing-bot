# Phase 8: Strategy Intelligence, Diagnostics & Improvement Suggestions

## Scope

Phase 8 adds a **read-only, offline** Strategy Intelligence system that:

- Observes completed trades (from `logs/trades.csv`)
- Analyzes historical performance
- Identifies patterns of success and failure
- Produces **ranked, explainable suggestions** for improving strategies

**This system does not modify execution, strategy logic, strategy parameters, or config.** It is analysis and suggestion tooling only. All outputs are for human review.

---

## Architecture

```
Trade closes (paper) → Trade logged (existing) → Periodic/manual analysis (Phase 8)
       → Diagnostics & pattern analysis → Suggestion generation (read-only)
       → Human review via dashboard / report
```

### Components

| Component | Location | Role |
|-----------|-----------|------|
| **Trade context (8A)** | `analysis/trade_context.py` | Enriches trade records with derived context (time of day, volatility proxy, exit reason) for analysis only. Does not modify logs. |
| **Diagnostics engine (8B)** | `analysis/diagnostics.py` | Computes performance breakdowns, risk-adjusted metrics, failure analysis, regime detection. Read-only. |
| **Suggestion generator (8C)** | `analysis/suggestions.py` | Produces ranked suggestions with confidence and evidence. Never code patches or config writes. |
| **Facade & storage (8D)** | `services/strategy_intelligence.py` | Single entry point for dashboard. In-memory cache; optional JSON export under `analysis/reports/`. |
| **Dashboard (8E)** | `dashboard/app.py`, `templates/strategy_intelligence.html` | Strategy Intelligence page and `/api/intelligence/*` routes. No apply buttons. |
| **Tests (8F)** | `tests/test_strategy_intelligence.py` | No-trades, small-sample, contradictory-data, no-writes, execution-independence tests. |

---

## Safeguards (Non-Negotiable)

1. **No automatic changes**  
   No strategy parameters, strategy code, or config files are ever modified by this system.

2. **No execution coupling**  
   The execution engine (`run_bot.py`, paper trading, etc.) does **not** import `services.strategy_intelligence` or the `analysis` package. Trade execution works identically if Phase 8 is removed.

3. **Read-only data access**  
   Data is consumed only from:
   - `logs/trades.csv` (via `DataParser`)
   - `logs/activity.json` (read-only)
   - Existing backtest outputs if present  

   No writes to strategy code or config.

4. **No per-trade adaptation**  
   Analysis runs on demand or periodically (batch). It is **never** invoked inline on every trade.

5. **Explainable output**  
   Every suggestion includes evidence, sample size, confidence score, and validation steps. No black-box ML in this phase.

---

## Data Audit (Phase 8A)

### Available from logs

- `timestamp` (used as entry_time/exit_time)
- `market`, `yes_price`, `no_price`, `sum`, `profit_pct`, `profit_usd`, `status`, `strategy`, `arbitrage_type`

### Derived in analysis (labeled as derived)

- `time_of_day`, `hour_of_day` (from timestamp)
- `volatility_proxy` (from |profit_pct| heuristic)
- `exit_reason` (inferred from P&L: target/stop/breakeven)

### Not available

- Strategy version, parameters used, exact exit reason (target/stop/timeout), market volatility/liquidity at trade time  

These are documented in diagnostics `trade_context_audit`. No execution or logging changes were made to capture them; they can be added in the logging layer in a future phase if desired.

---

## Suggestion Schema (Example)

```json
{
  "strategy": "ArbitrageStrategy",
  "issue_detected": "Low edge trades underperform in high volatility",
  "suggested_change": "Consider increasing min edge during high-volatility regimes...",
  "confidence": 0.81,
  "evidence": {
    "sample_size": 142,
    "win_rate_before": 0.42,
    "win_rate_after_threshold": 0.61,
    "p_value": 0.03
  },
  "risk": "May reduce trade frequency",
  "validation_required": [
    "Backtest with new parameter",
    "Paper run for ≥ 100 trades"
  ]
}
```

Suggestions are **recommendations only**. They never include code patches or instructions to write files.

---

## Storage & Access

- **In-memory:** Last run diagnostics and suggestions are cached in `services/strategy_intelligence`.
- **Optional export:** JSON files under `analysis/reports/` (e.g. `strategy_intelligence_YYYYMMDD_HHMMSS.json`). Nothing under `config/` or strategy code paths is written.
- **API (read-only):**
  - `GET /api/intelligence/diagnostics?strategy=&refresh=`
  - `GET /api/intelligence/suggestions?strategy=&refresh=`
  - `POST /api/intelligence/run` (body: `{ "strategy": "optional" }`)
  - `GET /api/intelligence/export` (download JSON)
- **Page:** `/intelligence` — Strategy Intelligence view with disclaimer, diagnostics, and ranked suggestions. No apply or auto-tune controls.

---

## Limitations

- **Execution does not depend on Phase 8.** Removing the `analysis` package and `services/strategy_intelligence`, and the dashboard routes that use them, has zero impact on trade execution.
- **Suggestions are heuristic-based.** No machine learning in this phase; all logic is explainable.
- **Missing log fields** (e.g. strategy version, exact exit reason, live volatility) are either derived with clear labeling or left as “not available” in the audit. Adding them would require changes to the **logging** layer (e.g. `logger.py` / engine), which was out of scope for Phase 8 (read-only analysis only).

---

## Exit Criteria (Mandatory)

- [x] The bot never modifies itself (no auto changes to strategy/config/code).
- [x] Suggestions are explainable and reproducible (evidence, sample size, confidence).
- [x] A human can review, test, and reject suggestions safely (dashboard + export, no apply button).
- [x] Removing Phase 8 has zero impact on execution (execution path does not import strategy_intelligence).

If any future change would require modifying execution logic, strategy code, or config files automatically, that change must be stopped, documented, and approved before implementation.
