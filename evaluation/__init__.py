"""
Strategy Evaluation Framework — Research Layer

Isolated from live execution. Use for backtest/paper evaluation only.
- Evaluation metrics (rolling Sharpe, drawdown, profit factor, etc.)
- Realistic friction (commission, spread, slippage, partial fill)
- Walk-forward validation
- Monte Carlo robustness
- Overfitting guard and robustness score
- Strategy comparison (rank by robustness; no auto-deploy)
"""

from evaluation.config import FrictionConfig, EvaluationConfig
from evaluation.metrics import StrategyMetrics
from evaluation.friction import apply_friction_to_trades
from evaluation.walk_forward import WalkForwardResult, run_walk_forward
from evaluation.monte_carlo import MonteCarloResult, run_monte_carlo
from evaluation.overfitting_guard import OverfittingGuardResult, check_overfitting
from evaluation.comparison import StrategyComparisonResult, compare_strategies
from evaluation.evaluator import run_evaluation, EvaluationReport

__all__ = [
    "FrictionConfig",
    "EvaluationConfig",
    "StrategyMetrics",
    "apply_friction_to_trades",
    "WalkForwardResult",
    "run_walk_forward",
    "MonteCarloResult",
    "run_monte_carlo",
    "OverfittingGuardResult",
    "check_overfitting",
    "StrategyComparisonResult",
    "compare_strategies",
    "run_evaluation",
    "EvaluationReport",
]
