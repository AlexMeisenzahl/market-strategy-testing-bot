"""
Strategy Parameter Optimizer

Uses grid search to find optimal parameters for trading strategies
by running backtests on all parameter combinations.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
from itertools import product
from services.backtesting_engine import backtesting_engine


class StrategyOptimizer:
    """
    Optimizer for strategy parameters using grid search

    Tests all combinations of parameters and returns the optimal set
    based on Sharpe ratio or other metrics.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.optimization_history = []

    def optimize_strategy(
        self,
        strategy_name: str,
        param_ranges: Dict,
        start_date: datetime = None,
        end_date: datetime = None,
        optimization_metric: str = "sharpe_ratio",
    ) -> Dict:
        """
        Optimize strategy parameters using grid search

        Args:
            strategy_name: Name of strategy to optimize
            param_ranges: Dict of parameter names to lists of values to test
            start_date: Start date for backtesting (default: 90 days ago)
            end_date: End date for backtesting (default: today)
            optimization_metric: Metric to optimize ('sharpe_ratio', 'return_pct', 'win_rate')

        Returns:
            Dict with optimal parameters and results

        Example:
            param_ranges = {
                'min_profit_margin': [1.5, 2.0, 2.5, 3.0],
                'min_liquidity': [500, 1000, 2000]
            }
            result = optimizer.optimize_strategy('polymarket_arbitrage', param_ranges)
        """
        self.logger.info(f"Starting parameter optimization for {strategy_name}")

        # Default date range if not provided
        if end_date is None:
            end_date = datetime.utcnow()
        if start_date is None:
            start_date = end_date - timedelta(days=90)

        # Generate all parameter combinations
        param_names = list(param_ranges.keys())
        param_values = list(param_ranges.values())
        combinations = list(product(*param_values))

        total_combinations = len(combinations)
        self.logger.info(f"Testing {total_combinations} parameter combinations...")

        # Test each combination
        results = []
        for i, combo in enumerate(combinations, 1):
            # Create parameter dict
            params = dict(zip(param_names, combo))

            self.logger.info(f"Testing combination {i}/{total_combinations}: {params}")

            # Create strategy instance with these parameters
            # Note: This is simplified - in production, you'd instantiate
            # the actual strategy class with these parameters
            strategy = self._create_strategy_instance(strategy_name, params)

            # Run backtest
            backtest_result = backtesting_engine.run_backtest(
                strategy, start_date, end_date
            )

            if backtest_result["success"]:
                metrics = backtest_result["metrics"]

                results.append(
                    {
                        "parameters": params,
                        "metrics": metrics,
                        "recommendation": backtest_result["recommendation"],
                        "optimization_score": metrics.get(optimization_metric, 0),
                    }
                )

                self.logger.info(
                    f"  → {optimization_metric}: {metrics.get(optimization_metric, 0):.2f}, "
                    f"Return: {metrics['return_pct']:.2f}%, "
                    f"Win Rate: {metrics['win_rate']:.2f}%"
                )
            else:
                self.logger.warning(
                    f"  → Backtest failed: {backtest_result.get('error', 'Unknown error')}"
                )

        if not results:
            return {"success": False, "error": "No successful backtests completed"}

        # Find optimal parameters
        optimal = max(results, key=lambda x: x["optimization_score"])

        # Sort all results by optimization score
        results.sort(key=lambda x: x["optimization_score"], reverse=True)

        self.logger.info(
            f"✓ Optimization complete! Optimal {optimization_metric}: "
            f"{optimal['optimization_score']:.2f}"
        )
        self.logger.info(f"  Optimal parameters: {optimal['parameters']}")

        # Save to history
        optimization_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "strategy_name": strategy_name,
            "param_ranges": param_ranges,
            "combinations_tested": total_combinations,
            "optimal_parameters": optimal["parameters"],
            "optimal_metrics": optimal["metrics"],
            "optimization_metric": optimization_metric,
        }
        self.optimization_history.append(optimization_record)

        return {
            "success": True,
            "strategy_name": strategy_name,
            "optimization_metric": optimization_metric,
            "combinations_tested": total_combinations,
            "optimal_parameters": optimal["parameters"],
            "optimal_metrics": optimal["metrics"],
            "recommendation": optimal["recommendation"],
            "all_results": results[:10],  # Top 10 results
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
        }

    def _create_strategy_instance(self, strategy_name: str, params: Dict) -> Any:
        """
        Create strategy instance with given parameters

        Args:
            strategy_name: Name of strategy
            params: Parameter values

        Returns:
            Strategy instance

        Note: This is a placeholder - in production, this would
        dynamically import and instantiate the actual strategy class
        """

        # Placeholder strategy class
        class DummyStrategy:
            def __init__(self, params):
                self.params = params
                self.__class__.__name__ = strategy_name

        return DummyStrategy(params)

    def compare_optimizations(self, strategy_name: str) -> Dict:
        """
        Compare optimization results for a strategy over time

        Args:
            strategy_name: Name of strategy

        Returns:
            Dict with comparison data
        """
        strategy_optimizations = [
            opt
            for opt in self.optimization_history
            if opt["strategy_name"] == strategy_name
        ]

        if not strategy_optimizations:
            return {
                "success": False,
                "error": f"No optimization history for {strategy_name}",
            }

        return {
            "success": True,
            "strategy_name": strategy_name,
            "optimization_count": len(strategy_optimizations),
            "optimizations": strategy_optimizations,
        }

    def get_optimization_history(self) -> List[Dict]:
        """
        Get all optimization history

        Returns:
            List of optimization records
        """
        return self.optimization_history

    def optimize_multiple_strategies(
        self,
        strategies: Dict[str, Dict],
        start_date: datetime = None,
        end_date: datetime = None,
    ) -> Dict:
        """
        Optimize multiple strategies in batch

        Args:
            strategies: Dict of strategy_name -> param_ranges
            start_date: Start date for backtesting
            end_date: End date for backtesting

        Returns:
            Dict with all optimization results

        Example:
            strategies = {
                'polymarket_arbitrage': {
                    'min_profit_margin': [1.5, 2.0, 2.5],
                    'min_liquidity': [500, 1000]
                },
                'crypto_momentum': {
                    'lookback_period': [10, 20, 30],
                    'threshold': [0.02, 0.03, 0.05]
                }
            }
        """
        self.logger.info(f"Optimizing {len(strategies)} strategies...")

        results = {}
        for strategy_name, param_ranges in strategies.items():
            self.logger.info(f"\n=== Optimizing {strategy_name} ===")

            result = self.optimize_strategy(
                strategy_name, param_ranges, start_date, end_date
            )
            results[strategy_name] = result

        self.logger.info("\n✓ All strategies optimized!")

        return {
            "success": True,
            "strategies_optimized": len(strategies),
            "results": results,
        }

    def sensitivity_analysis(
        self, strategy_name: str, param_ranges: Dict, focus_param: str
    ) -> Dict:
        """
        Perform sensitivity analysis on a single parameter

        Args:
            strategy_name: Name of strategy
            param_ranges: Parameter ranges
            focus_param: Parameter to analyze sensitivity for

        Returns:
            Dict with sensitivity analysis results
        """
        if focus_param not in param_ranges:
            return {
                "success": False,
                "error": f"Parameter {focus_param} not in param_ranges",
            }

        self.logger.info(f"Performing sensitivity analysis on {focus_param}...")

        # Fix all parameters except focus_param at their first value
        fixed_params = {k: v[0] for k, v in param_ranges.items() if k != focus_param}

        results = []
        for value in param_ranges[focus_param]:
            test_params = fixed_params.copy()
            test_params[focus_param] = value

            strategy = self._create_strategy_instance(strategy_name, test_params)
            backtest_result = backtesting_engine.run_backtest(
                strategy, datetime.utcnow() - timedelta(days=90), datetime.utcnow()
            )

            if backtest_result["success"]:
                results.append(
                    {
                        "parameter_value": value,
                        "return_pct": backtest_result["metrics"]["return_pct"],
                        "sharpe_ratio": backtest_result["metrics"]["sharpe_ratio"],
                        "win_rate": backtest_result["metrics"]["win_rate"],
                    }
                )

        return {
            "success": True,
            "strategy_name": strategy_name,
            "focus_parameter": focus_param,
            "fixed_parameters": fixed_params,
            "results": results,
        }


# Global instance
strategy_optimizer = StrategyOptimizer()
