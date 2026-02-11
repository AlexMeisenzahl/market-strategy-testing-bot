# Strategy Evaluation Framework

Research-layer only. **Does not modify live execution.** Use for backtest and paper-trade evaluation.

## Usage

- **From code:** `from evaluation import run_evaluation, EvaluationConfig`
- **From dashboard:** Strategy Comparison page → "Run robustness evaluation" (uses `/api/evaluation/run`).
- **Validation:** `python3 scripts/run_evaluation_validation.py` (from project root).

## Components

| Phase | Module | Description |
|-------|--------|-------------|
| 1 | `metrics` | Rolling Sharpe, max drawdown, profit factor, expectancy, volatility-segmented metrics, return distribution (skew, kurtosis). All on segments. |
| 2 | `friction` | Configurable commission, spread, slippage, partial fill. Applied to trade lists only. |
| 3 | `walk_forward` | Train window A, test window B, roll forward; aggregate out-of-sample only. |
| 4 | `monte_carlo` | Randomize trade order and slippage; return distribution and confidence intervals; flag unstable. |
| 5 | `overfitting_guard` | Flag if OOS Sharpe drops more than threshold from in-sample; robustness score. |
| 6 | `comparison` | Compare strategies side-by-side; rank by robustness; in-sample vs OOS. No auto-deploy. |

## Config

- `EvaluationConfig`: risk-free rate, train/test/step days, OOS Sharpe drop threshold, Monte Carlo sims, rolling window.
- `FrictionConfig`: commission_rate, spread_bps, slippage_bps, partial_fill_rate, partial_fill_ratio_min/max.

## Constraints

- Evaluation is **sandboxed**: it only reads trade data (e.g. from CSV or backtest results).
- Live execution engine and strategy deployment are **unchanged**.
- No strategy is automatically deployed based on evaluation results.
