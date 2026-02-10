"""
Strategy Manager Module - Orchestrates multiple trading strategies

Coordinates multiple trading strategies running in parallel:
- Arbitrage Strategy (classic YES+NO < $1.00)
- Momentum Strategy (trend-following)
- Statistical Arbitrage Strategy (mean reversion)
- News-Based Strategy (event-driven)

Each strategy can be enabled/disabled via config and has separate capital allocation.
Tracks and compares performance across all strategies.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import time
from logger import get_logger
from engine import ExecutionEngine, TradeSignal

# Import all available strategies
from strategies.arbitrage_strategy import ArbitrageStrategy
from strategies.momentum_strategy import MomentumStrategy
from strategies.statistical_arb_strategy import StatisticalArbStrategy
from strategies.news_strategy import NewsStrategy


class StrategyManager:
    """
    Manages multiple trading strategies running in parallel

    Coordinates strategy execution, capital allocation, and performance tracking.
    Each strategy operates independently with its own allocated capital.
    """

    def __init__(
        self,
        config: Dict[str, Any],
        execution_engine: Optional[ExecutionEngine] = None,
    ):
        """
        Initialize strategy manager

        Args:
            config: Configuration dictionary from config.yaml
            execution_engine: Single execution engine; all trades route through it.
        """
        self.config = config
        self.execution_engine = execution_engine
        self.logger = get_logger()

        # Total capital allocation
        self.total_capital = config.get("total_capital", 100)  # Default $100

        # Strategy configuration (which strategies to enable)
        # Can be configured via config.yaml under 'strategies' key
        strategy_config = config.get("strategies", {})
        self.enabled_strategies = strategy_config.get(
            "enabled",
            [
                "arbitrage",  # Default: only arbitrage enabled
            ],
        )

        # Capital allocation per strategy (equal split by default)
        self.capital_allocation = self._calculate_capital_allocation(strategy_config)

        # Initialize strategies
        self.strategies: Dict[str, Any] = {}
        self._initialize_strategies()

        # Performance tracking
        self.start_time = datetime.now()
        self.cycles_completed = 0
        self.total_opportunities = 0
        self.total_trades = 0

        self.logger.log_warning(
            f"Strategy Manager initialized with {len(self.strategies)} strategies: "
            f"{list(self.strategies.keys())}"
        )

    def _calculate_capital_allocation(
        self, strategy_config: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        Calculate capital allocation for each strategy

        Args:
            strategy_config: Strategy configuration from config

        Returns:
            Dictionary mapping strategy name to allocated capital
        """
        allocation = {}

        # Check if custom allocation is specified
        custom_allocation = strategy_config.get("capital_allocation", {})

        if custom_allocation:
            # Use custom allocation (percentages)
            for strategy_name in self.enabled_strategies:
                pct = custom_allocation.get(strategy_name, 0)
                allocation[strategy_name] = self.total_capital * pct
        else:
            # Equal split among enabled strategies
            capital_per_strategy = self.total_capital / len(self.enabled_strategies)
            for strategy_name in self.enabled_strategies:
                allocation[strategy_name] = capital_per_strategy

        return allocation

    def _initialize_strategies(self) -> None:
        """Initialize all enabled strategies"""

        # Map strategy names to classes
        strategy_classes = {
            "arbitrage": ArbitrageStrategy,
            "momentum": MomentumStrategy,
            "statistical_arb": StatisticalArbStrategy,
            "news": NewsStrategy,
        }

        for strategy_name in self.enabled_strategies:
            if strategy_name not in strategy_classes:
                self.logger.log_warning(
                    f"Unknown strategy '{strategy_name}' - skipping"
                )
                continue

            try:
                # Create strategy-specific config
                strategy_config = self.config.copy()
                strategy_config["allocated_capital"] = self.capital_allocation[
                    strategy_name
                ]
                strategy_config["max_trade_size"] = min(
                    self.config.get("max_trade_size", 10),
                    self.capital_allocation[strategy_name] * 0.1,  # Max 10% per trade
                )

                # Initialize strategy
                strategy_class = strategy_classes[strategy_name]
                self.strategies[strategy_name] = strategy_class(strategy_config)

                self.logger.log_warning(
                    f"Initialized {strategy_name} strategy with "
                    f"${self.capital_allocation[strategy_name]:.2f} capital"
                )

            except Exception as e:
                self.logger.log_error(
                    f"Failed to initialize {strategy_name} strategy: {str(e)}"
                )

    def run_all_strategies(
        self, markets: List[Dict[str, Any]], prices_dict: Dict[str, Dict[str, float]]
    ) -> Dict[str, List[Any]]:
        """
        Run all enabled strategies on the current market data

        Args:
            markets: List of market information
            prices_dict: Dictionary mapping market_id to price data

        Returns:
            Dictionary mapping strategy name to list of opportunities found
        """
        self.cycles_completed += 1
        all_opportunities = {}

        # Run each strategy in parallel (conceptually - Python GIL makes true parallelism complex)
        for strategy_name, strategy in self.strategies.items():
            try:
                start_time = time.time()

                # Find opportunities using this strategy
                opportunities = strategy.find_opportunities(markets, prices_dict)

                # Track timing
                elapsed_ms = (time.time() - start_time) * 1000

                # Store results
                all_opportunities[strategy_name] = opportunities

                # Update tracking
                if opportunities:
                    self.total_opportunities += len(opportunities)
                    self.logger.log_warning(
                        f"{strategy_name}: Found {len(opportunities)} opportunities "
                        f"in {elapsed_ms:.0f}ms"
                    )

            except Exception as e:
                self.logger.log_error(
                    f"Error running {strategy_name} strategy: {str(e)}"
                )
                all_opportunities[strategy_name] = []

        return all_opportunities

    # NOTE:
    # This method routes TradeSignals to the ExecutionEngine.
    # Strategies do NOT execute trades and do NOT mutate state.
    def execute_best_opportunities(
        self, all_opportunities: Dict[str, List[Any]]
    ) -> Dict[str, int]:
        """
        Execute the best opportunities from all strategies

        For paper trading, we simulate execution of top opportunities from each strategy.
        Each strategy can execute independently based on its own criteria.

        Args:
            all_opportunities: Dictionary mapping strategy name to opportunities

        Returns:
            Dictionary mapping strategy name to number of trades executed
        """
        trades_executed = {}

        for strategy_name, opportunities in all_opportunities.items():
            if not opportunities:
                trades_executed[strategy_name] = 0
                continue

            strategy = self.strategies[strategy_name]
            executed = 0

            # Sort opportunities by profit potential (descending)
            sorted_opps = sorted(
                opportunities,
                key=lambda x: x.profit_margin if hasattr(x, "profit_margin") else 0,
                reverse=True,
            )

            # Try to execute top opportunities via the single execution engine
            for opp in sorted_opps[:3]:  # Limit to top 3 per cycle
                if not self.execution_engine:
                    break
                if hasattr(strategy, "should_enter") and not strategy.should_enter(opp):
                    continue
                trade_size = min(
                    self.config.get("max_trade_size", 10),
                    self.capital_allocation[strategy_name] * 0.1,
                )
                # Build signal from opportunity; engine executes (no strategy execution)
                signal = self._opportunity_to_signal(opp, trade_size, strategy_name)
                if not signal:
                    continue
                result = self.execution_engine.execute_trade(signal)
                if result.get("success"):
                    executed += 1
                    self.total_trades += 1

            trades_executed[strategy_name] = executed

        return trades_executed

    def _opportunity_to_signal(
        self,
        opp: Any,
        trade_size: float,
        strategy_name: str,
    ) -> Optional[TradeSignal]:
        """Build a TradeSignal from an opportunity; used for execution-engine routing."""
        if hasattr(opp, "market_id"):
            symbol = opp.market_id
        elif hasattr(opp, "to_dict"):
            d = opp.to_dict()
            symbol = d.get("market_id") or d.get("market_name", "")
        elif isinstance(opp, dict):
            symbol = opp.get("market_id") or opp.get("market_name", "")
        else:
            return None
        if not symbol:
            return None
        price = 0.5
        if hasattr(opp, "yes_price") and opp.yes_price:
            price = float(opp.yes_price)
        elif isinstance(opp, dict):
            price = float(opp.get("yes_price", 0.5) or 0.5)
        elif hasattr(opp, "to_dict"):
            price = float(opp.to_dict().get("yes_price", 0.5) or 0.5)
        if price <= 0:
            price = 0.5
        quantity = trade_size / price
        if quantity <= 0:
            return None
        return TradeSignal(
            symbol=str(symbol),
            side="buy",
            quantity=quantity,
            order_type="market",
            price=price,
            strategy_name=strategy_name,
        )

    def compare_strategies(self) -> Dict[str, Any]:
        """
        Compare performance metrics across all strategies

        Returns:
            Dictionary with comparative statistics for each strategy
        """
        comparison = {}

        for strategy_name, strategy in self.strategies.items():
            # Get strategy statistics
            stats = strategy.get_statistics()

            # Calculate additional metrics
            allocated_capital = self.capital_allocation[strategy_name]

            # ROI (Return on Investment)
            roi_pct = 0.0
            if allocated_capital > 0 and stats.get("total_actual_profit", 0) != 0:
                roi_pct = (
                    stats.get("total_actual_profit", 0) / allocated_capital
                ) * 100
            elif allocated_capital > 0 and stats.get("total_expected_profit", 0) != 0:
                roi_pct = (
                    stats.get("total_expected_profit", 0) / allocated_capital
                ) * 100

            # Win rate
            win_rate = 0.0
            if stats.get("opportunities_found", 0) > 0:
                win_rate = (
                    stats.get("opportunities_taken", 0)
                    / stats.get("opportunities_found", 0)
                ) * 100

            # Average profit per trade
            avg_profit = 0.0
            if stats.get("opportunities_taken", 0) > 0:
                total_profit = stats.get(
                    "total_actual_profit", stats.get("total_expected_profit", 0)
                )
                avg_profit = total_profit / stats.get("opportunities_taken", 1)

            comparison[strategy_name] = {
                "allocated_capital": allocated_capital,
                "opportunities_found": stats.get("opportunities_found", 0),
                "opportunities_taken": stats.get("opportunities_taken", 0),
                "total_profit": stats.get(
                    "total_actual_profit", stats.get("total_expected_profit", 0)
                ),
                "roi_percent": roi_pct,
                "win_rate_percent": win_rate,
                "avg_profit_per_trade": avg_profit,
                "active_positions": stats.get("active_positions", 0),
                "execution_rate": stats.get("execution_rate", 0),
            }

        return comparison

    def get_best_performing_strategy(self) -> Optional[str]:
        """
        Identify the best performing strategy based on ROI

        Returns:
            Name of best performing strategy, or None if no trades yet
        """
        comparison = self.compare_strategies()

        if not comparison:
            return None

        # Find strategy with highest ROI
        best_strategy = max(comparison.items(), key=lambda x: x[1]["roi_percent"])

        return best_strategy[0]

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get overall statistics across all strategies

        Returns:
            Dictionary with aggregate statistics
        """
        # Get individual strategy stats
        strategy_stats = self.compare_strategies()

        # Calculate aggregate metrics
        total_opportunities = sum(
            s["opportunities_found"] for s in strategy_stats.values()
        )
        total_trades = sum(s["opportunities_taken"] for s in strategy_stats.values())
        total_profit = sum(s["total_profit"] for s in strategy_stats.values())
        total_active_positions = sum(
            s["active_positions"] for s in strategy_stats.values()
        )

        # Overall ROI
        overall_roi = (
            (total_profit / self.total_capital * 100) if self.total_capital > 0 else 0.0
        )

        # Runtime
        runtime_seconds = (datetime.now() - self.start_time).total_seconds()
        runtime_minutes = runtime_seconds / 60.0

        # Best performing strategy
        best_strategy = self.get_best_performing_strategy()

        return {
            "enabled_strategies": list(self.strategies.keys()),
            "total_capital": self.total_capital,
            "cycles_completed": self.cycles_completed,
            "total_opportunities": total_opportunities,
            "total_trades": total_trades,
            "total_profit": total_profit,
            "overall_roi_percent": overall_roi,
            "active_positions": total_active_positions,
            "runtime_minutes": runtime_minutes,
            "best_strategy": best_strategy,
            "strategy_comparison": strategy_stats,
        }

    def enable_strategy(self, strategy_name: str) -> bool:
        """
        Enable a strategy at runtime

        Args:
            strategy_name: Name of strategy to enable

        Returns:
            True if successfully enabled, False otherwise
        """
        if strategy_name in self.strategies:
            self.logger.log_warning(f"{strategy_name} is already enabled")
            return True

        if strategy_name not in ["arbitrage", "momentum", "statistical_arb", "news"]:
            self.logger.log_error(f"Unknown strategy: {strategy_name}")
            return False

        try:
            # Add to enabled list
            self.enabled_strategies.append(strategy_name)

            # Recalculate capital allocation
            self.capital_allocation = self._calculate_capital_allocation(
                self.config.get("strategies", {})
            )

            # Initialize the strategy
            self._initialize_strategies()

            self.logger.log_warning(f"Enabled {strategy_name} strategy")
            return True

        except Exception as e:
            self.logger.log_error(f"Failed to enable {strategy_name}: {str(e)}")
            return False

    def disable_strategy(self, strategy_name: str) -> bool:
        """
        Disable a strategy at runtime

        Args:
            strategy_name: Name of strategy to disable

        Returns:
            True if successfully disabled, False otherwise
        """
        if strategy_name not in self.strategies:
            self.logger.log_warning(f"{strategy_name} is not currently enabled")
            return True

        try:
            # Remove from enabled list and strategies dict
            self.enabled_strategies.remove(strategy_name)
            del self.strategies[strategy_name]

            # Recalculate capital allocation for remaining strategies
            self.capital_allocation = self._calculate_capital_allocation(
                self.config.get("strategies", {})
            )

            self.logger.log_warning(f"Disabled {strategy_name} strategy")
            return True

        except Exception as e:
            self.logger.log_error(f"Failed to disable {strategy_name}: {str(e)}")
            return False

    def rebalance_capital(self, new_allocation: Dict[str, float]) -> bool:
        """
        Rebalance capital allocation across strategies

        Args:
            new_allocation: Dictionary mapping strategy name to allocation percentage

        Returns:
            True if successfully rebalanced, False otherwise
        """
        # Validate allocation sums to 1.0 (100%)
        total_allocation = sum(new_allocation.values())
        if abs(total_allocation - 1.0) > 0.01:  # Allow small rounding errors
            self.logger.log_error(
                f"Capital allocation must sum to 100% (got {total_allocation*100:.1f}%)"
            )
            return False

        try:
            # Update capital allocation
            for strategy_name in self.strategies.keys():
                if strategy_name in new_allocation:
                    self.capital_allocation[strategy_name] = (
                        self.total_capital * new_allocation[strategy_name]
                    )

            self.logger.log_warning("Capital rebalanced across strategies")
            return True

        except Exception as e:
            self.logger.log_error(f"Failed to rebalance capital: {str(e)}")
            return False

    def get_portfolio_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the entire portfolio across all strategies

        Returns:
            Dictionary with portfolio summary
        """
        summary = {"total_capital": self.total_capital, "strategies": {}}

        for strategy_name, strategy in self.strategies.items():
            stats = strategy.get_statistics()

            summary["strategies"][strategy_name] = {
                "allocated_capital": self.capital_allocation[strategy_name],
                "allocation_percent": (
                    self.capital_allocation[strategy_name] / self.total_capital * 100
                ),
                "current_profit": stats.get(
                    "total_actual_profit", stats.get("total_expected_profit", 0)
                ),
                "open_positions": stats.get("active_positions", 0),
                "total_trades": stats.get("opportunities_taken", 0),
            }

        return summary
