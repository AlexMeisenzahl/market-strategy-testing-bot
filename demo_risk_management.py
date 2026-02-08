#!/usr/bin/env python3
"""
Integration Example - How to use all risk management modules together

This demonstrates a complete trading loop using all four risk management modules:
- Position Sizer (dynamic position sizing)
- Risk Manager (circuit breakers)
- Loss Analyzer (diagnose losses)
- Strategy Analyzer (compare strategies)
"""

import yaml
from datetime import datetime
from typing import Dict, Any, List

# Import risk management modules
from position_sizer import RiskAdjustedPositionSizer
from risk_manager import DrawdownProtection
from loss_analyzer import LossAnalyzer
from strategy_analyzer import StrategyAnalyzer

# Import existing modules
from detector import ArbitrageOpportunity
from logger import get_logger


class EnhancedTradingBot:
    """
    Trading bot with integrated risk management

    Combines all risk management modules with the core trading logic.
    """

    def __init__(self, config_path: str = "config.yaml"):
        """Initialize bot with risk management"""
        # Load config
        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f)

        self.logger = get_logger()

        # Initialize risk management modules
        self.position_sizer = RiskAdjustedPositionSizer(self.config)
        self.risk_manager = DrawdownProtection(self.config)
        self.loss_analyzer = LossAnalyzer(self.config)
        self.strategy_analyzer = StrategyAnalyzer(self.config)

        # Trading state
        self.current_capital = 1000.0  # Starting capital
        self.trade_history = []
        self.strategy_performance = {
            "arbitrage": [],
            "momentum": [],
            "statistical_arb": [],
            "news": [],
        }

        self.logger.log_warning("Enhanced Trading Bot initialized with risk management")

    def should_trade(self) -> Dict[str, Any]:
        """
        Check if trading is allowed

        Returns:
            Dictionary with status and reason
        """
        # Check circuit breakers
        risk_status = self.risk_manager.check_all_breakers(self.current_capital)

        if not risk_status["trading_allowed"]:
            # Trading paused - analyze why
            self._handle_trading_pause(risk_status)
            return risk_status

        return risk_status

    def calculate_trade_size(
        self, opportunity: ArbitrageOpportunity, strategy: str
    ) -> float:
        """
        Calculate optimal trade size for opportunity

        Args:
            opportunity: Arbitrage opportunity
            strategy: Strategy name

        Returns:
            Position size in USD
        """
        # Build stats for position sizer
        stats = self._build_stats(strategy)

        # Calculate position size
        sizing = self.position_sizer.calculate_position_size(
            opportunity=opportunity, bankroll=self.current_capital, stats=stats
        )

        return sizing["position_size"]

    def execute_trade(
        self, opportunity: ArbitrageOpportunity, position_size: float, strategy: str
    ) -> Dict[str, Any]:
        """
        Execute a trade (paper trading)

        Args:
            opportunity: Arbitrage opportunity
            position_size: Position size in USD
            strategy: Strategy name

        Returns:
            Trade result dictionary
        """
        # Simulate trade execution
        total_cost = position_size * opportunity.price_sum
        expected_return = position_size
        profit = expected_return - total_cost

        trade = {
            "timestamp": datetime.now(),
            "executed_at": datetime.now(),
            "strategy": strategy,
            "market_id": opportunity.market_id,
            "market_name": opportunity.market_name,
            "position_size": position_size,
            "profit": profit,
            "profit_margin": opportunity.profit_margin,
            "yes_price": opportunity.yes_price,
            "no_price": opportunity.no_price,
            "execution_time_ms": 250,  # Simulated
            "fill_percentage": 1.0,  # Simulated
            "market_volatility": "normal",
            "notes": "Paper trade execution",
        }

        # Record the trade
        self.trade_history.append(trade)
        self.strategy_performance[strategy].append(trade)

        # Update risk manager
        self.risk_manager.record_trade(profit, self.current_capital + profit)

        # Update capital
        self.current_capital += profit

        return trade

    def _build_stats(self, strategy: str) -> Dict[str, Any]:
        """
        Build statistics for position sizing

        Args:
            strategy: Strategy name

        Returns:
            Statistics dictionary
        """
        # Calculate overall win rate
        total_trades = self.risk_manager.total_trades
        win_rate = 0.5  # Default
        if total_trades > 0:
            win_rate = self.risk_manager.winning_trades / total_trades

        # For now, use simple liquidity/volatility estimates
        # In production, these would come from real market data
        stats = {
            "win_rate": win_rate,
            "total_trades": total_trades,
            "market_liquidity": {},  # Would be populated with real data
            "market_volatility": {},  # Would be populated with real data
        }

        return stats

    def _handle_trading_pause(self, risk_status: Dict[str, Any]) -> None:
        """
        Handle trading pause - analyze and recommend fixes

        Args:
            risk_status: Risk status from check_all_breakers
        """
        self.logger.log_critical(f"🚨 TRADING PAUSED: {risk_status['pause_reason']}")

        # Analyze losses to find root cause
        if len(self.trade_history) >= 10:
            analysis = self.loss_analyzer.analyze_losses(self.trade_history)

            # Generate fix recommendations
            recommendations = self.loss_analyzer.generate_fix_suggestions(analysis)

            self.logger.log_critical("📋 RECOMMENDED ACTIONS:")
            for i, rec in enumerate(recommendations[:3], 1):  # Top 3 recommendations
                self.logger.log_critical(
                    f"{i}. [{rec['priority']}] {rec['category']}: {rec['recommendation']}"
                )
                for action in rec["actions"][:2]:  # Top 2 actions per recommendation
                    self.logger.log_warning(f"   - {action}")

    def analyze_strategies(self) -> Dict[str, Any]:
        """
        Analyze all strategies and get allocation recommendation

        Returns:
            Allocation recommendation
        """
        # Filter out strategies with no trades
        active_strategies = {
            name: trades
            for name, trades in self.strategy_performance.items()
            if len(trades) > 0
        }

        if not active_strategies:
            self.logger.log_warning("No strategy performance data yet")
            return {}

        # Compare strategies
        comparison = self.strategy_analyzer.compare_strategies(active_strategies)

        # Get allocation recommendation
        allocation = self.strategy_analyzer.generate_allocation_recommendation(
            comparison, self.current_capital
        )

        return allocation

    def get_status(self) -> Dict[str, Any]:
        """
        Get current bot status

        Returns:
            Status dictionary
        """
        risk_metrics = self.risk_manager.get_risk_metrics(self.current_capital)

        return {
            "current_capital": self.current_capital,
            "total_trades": len(self.trade_history),
            "total_profit": self.current_capital - 1000.0,  # Starting was 1000
            "risk_metrics": risk_metrics,
            "trading_allowed": not risk_metrics["is_paused"],
        }


def demo_integration():
    """Demonstrate the integration"""
    print("=" * 70)
    print("Risk Management Integration Demo")
    print("=" * 70)

    # Initialize bot
    bot = EnhancedTradingBot()

    # Simulate some trades
    print("\n📊 Simulating 10 trades...\n")

    for i in range(10):
        # Check if trading allowed
        status = bot.should_trade()

        if not status["trading_allowed"]:
            print(f"\n⛔ Trading paused after {i} trades")
            break

        # Create sample opportunity
        opportunity = ArbitrageOpportunity(
            market_id=f"market_{i}",
            market_name=f"Test Market {i}",
            yes_price=0.46 + (i * 0.01),  # Varying margins
            no_price=0.47 + (i * 0.01),
        )

        # Calculate position size
        position_size = bot.calculate_trade_size(opportunity, strategy="arbitrage")

        # Execute trade
        trade = bot.execute_trade(opportunity, position_size, strategy="arbitrage")

        # Show result
        profit_emoji = "📈" if trade["profit"] > 0 else "📉"
        print(
            f"{profit_emoji} Trade {i+1}: ${trade['profit']:.2f} profit "
            f"(size: ${position_size:.2f}, margin: {trade['profit_margin']:.2f}%)"
        )

    # Show final status
    print("\n" + "=" * 70)
    print("Final Status")
    print("=" * 70)

    final_status = bot.get_status()
    print(f"💰 Capital: ${final_status['current_capital']:.2f}")
    print(f"📊 Total Trades: {final_status['total_trades']}")
    print(f"💵 Total Profit: ${final_status['total_profit']:.2f}")
    print(f"✅ Trading Allowed: {final_status['trading_allowed']}")

    # Show risk metrics
    metrics = final_status["risk_metrics"]
    print(f"\n🎯 Risk Metrics:")
    print(f"  Win Rate: {metrics['win_rate']*100:.1f}%")
    print(f"  Consecutive Losses: {metrics['consecutive_losses']}")
    print(f"  Hourly Loss: ${metrics['hourly_loss']:.2f}")
    print(f"  Daily Drawdown: {metrics['daily_drawdown_pct']*100:.1f}%")

    # Analyze strategies (if enough data)
    if final_status["total_trades"] >= 5:
        print("\n📊 Strategy Analysis:")
        allocation = bot.analyze_strategies()
        if allocation:
            for strategy, alloc in allocation.get("allocations", {}).items():
                print(
                    f"  {strategy}: {alloc['percentage']:.1f}% (${alloc['capital']:.2f})"
                )

    print("\n" + "=" * 70)
    print("✓ Integration demo completed successfully!")
    print("=" * 70)


if __name__ == "__main__":
    demo_integration()
