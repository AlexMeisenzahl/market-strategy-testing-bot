"""
Loss Analyzer Module - Diagnose WHY the bot is losing money

When circuit breakers trigger, analyzes trade history to identify root causes:
- Partial fills (execution issues)
- Edge lost during execution (speed/latency issues)
- Strategy not working (logic flaws)
- Market conditions changed (external factors)
- Competition increased (structural changes)

Provides specific, actionable recommendations for each root cause.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
from logger import get_logger


class LossAnalyzer:
    """
    Analyzes trade history to identify root causes of losses

    Categorizes losses into different types and provides specific
    recommendations for fixing each category of problem.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize loss analyzer

        Args:
            config: Configuration dictionary from config.yaml
        """
        self.config = config
        self.logger = get_logger()

        # Analysis thresholds
        analysis_config = config.get("loss_analysis", {})
        self.min_trades_for_analysis = analysis_config.get("min_trades", 10)
        self.execution_lag_threshold_ms = analysis_config.get(
            "execution_lag_threshold_ms", 500
        )
        self.partial_fill_threshold = analysis_config.get(
            "partial_fill_threshold", 0.8
        )  # 80%

        self.logger.log_warning("Loss Analyzer initialized")

    def analyze_losses(self, trade_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze trade history to identify loss patterns

        Args:
            trade_history: List of trade dictionaries with details

        Returns:
            Dictionary with analysis results and categorized losses
        """
        if len(trade_history) < self.min_trades_for_analysis:
            return {
                "insufficient_data": True,
                "message": f"Need at least {self.min_trades_for_analysis} trades for analysis",
                "trade_count": len(trade_history),
            }

        # Categorize losses
        categories = {
            "partial_fills": [],
            "edge_lost_execution": [],
            "strategy_failure": [],
            "market_conditions": [],
            "competition": [],
            "other": [],
        }

        # Analyze each losing trade
        losing_trades = [t for t in trade_history if t.get("profit", 0) < 0]

        for trade in losing_trades:
            category = self._categorize_loss(trade, trade_history)
            categories[category].append(trade)

        # Calculate statistics for each category
        analysis = {
            "total_trades": len(trade_history),
            "losing_trades": len(losing_trades),
            "total_loss": sum(t.get("profit", 0) for t in losing_trades),
            "categories": {},
            "primary_issue": None,
            "severity": None,
        }

        # Analyze each category
        for category, trades in categories.items():
            if trades:
                analysis["categories"][category] = {
                    "count": len(trades),
                    "total_loss": sum(t.get("profit", 0) for t in trades),
                    "avg_loss": sum(t.get("profit", 0) for t in trades) / len(trades),
                    "percentage": (
                        (len(trades) / len(losing_trades)) * 100 if losing_trades else 0
                    ),
                    "trades": trades,
                }

        # Identify primary issue (category with most losses)
        if analysis["categories"]:
            primary_category = max(
                analysis["categories"].items(), key=lambda x: abs(x[1]["total_loss"])
            )
            analysis["primary_issue"] = primary_category[0]

            # Determine severity
            loss_rate = len(losing_trades) / len(trade_history)
            if loss_rate > 0.7:
                analysis["severity"] = "CRITICAL"
            elif loss_rate > 0.5:
                analysis["severity"] = "HIGH"
            else:
                analysis["severity"] = "MODERATE"

        # Log analysis results
        self._log_analysis(analysis)

        return analysis

    def _categorize_loss(
        self, trade: Dict[str, Any], full_history: List[Dict[str, Any]]
    ) -> str:
        """
        Categorize a single losing trade

        Args:
            trade: Trade dictionary to categorize
            full_history: Full trade history for context

        Returns:
            Category name (partial_fills, edge_lost_execution, etc.)
        """
        # Check for partial fill issues
        if self._is_partial_fill_issue(trade):
            return "partial_fills"

        # Check for execution lag
        if self._is_execution_lag_issue(trade):
            return "edge_lost_execution"

        # Check if strategy is consistently failing
        if self._is_strategy_failure(trade, full_history):
            return "strategy_failure"

        # Check for market condition changes
        if self._is_market_condition_issue(trade, full_history):
            return "market_conditions"

        # Check for increased competition
        if self._is_competition_issue(trade, full_history):
            return "competition"

        # Default category
        return "other"

    def _is_partial_fill_issue(self, trade: Dict[str, Any]) -> bool:
        """
        Check if trade suffered from partial fills

        Args:
            trade: Trade dictionary

        Returns:
            True if partial fill issue detected
        """
        # Check if fill percentage is below threshold
        fill_pct = trade.get("fill_percentage", 1.0)
        if fill_pct < self.partial_fill_threshold:
            return True

        # Check if trade notes indicate partial fill
        notes = trade.get("notes", "").lower()
        if "partial" in notes or "incomplete" in notes:
            return True

        return False

    def _is_execution_lag_issue(self, trade: Dict[str, Any]) -> bool:
        """
        Check if edge was lost due to execution lag

        Args:
            trade: Trade dictionary

        Returns:
            True if execution lag issue detected
        """
        # Check execution time
        execution_time_ms = trade.get("execution_time_ms", 0)
        if execution_time_ms > self.execution_lag_threshold_ms:
            return True

        # Check if initial profit margin was good but final was poor
        initial_margin = trade.get("initial_profit_margin", 0)
        final_margin = trade.get("final_profit_margin", 0)
        if initial_margin > 2.0 and final_margin < 0:  # Good opportunity turned bad
            return True

        return False

    def _is_strategy_failure(
        self, trade: Dict[str, Any], full_history: List[Dict[str, Any]]
    ) -> bool:
        """
        Check if the trading strategy itself is not working

        Args:
            trade: Trade dictionary
            full_history: Full trade history

        Returns:
            True if strategy failure detected
        """
        # Get strategy name
        strategy = trade.get("strategy", "unknown")

        # Look at recent trades for this strategy
        recent_cutoff = datetime.now() - timedelta(hours=24)
        recent_strategy_trades = [
            t
            for t in full_history
            if t.get("strategy") == strategy
            and t.get("executed_at", datetime.min) > recent_cutoff
        ]

        if len(recent_strategy_trades) >= 5:
            # Check win rate for this strategy
            losing = [t for t in recent_strategy_trades if t.get("profit", 0) < 0]
            loss_rate = len(losing) / len(recent_strategy_trades)

            # If strategy losing >70% of the time, it's a strategy failure
            if loss_rate > 0.7:
                return True

        return False

    def _is_market_condition_issue(
        self, trade: Dict[str, Any], full_history: List[Dict[str, Any]]
    ) -> bool:
        """
        Check if market conditions have changed

        Args:
            trade: Trade dictionary
            full_history: Full trade history

        Returns:
            True if market condition change detected
        """
        # Check if volatility increased significantly
        volatility = trade.get("market_volatility", "normal")
        if volatility == "high":
            return True

        # Check if opportunity frequency dropped
        recent_cutoff = datetime.now() - timedelta(hours=1)
        recent_trades = [
            t
            for t in full_history
            if t.get("executed_at", datetime.min) > recent_cutoff
        ]

        # If very few opportunities recently, market may have changed
        if len(recent_trades) < 2:
            return True

        return False

    def _is_competition_issue(
        self, trade: Dict[str, Any], full_history: List[Dict[str, Any]]
    ) -> bool:
        """
        Check if competition has increased

        Args:
            trade: Trade dictionary
            full_history: Full trade history

        Returns:
            True if increased competition detected
        """
        # Check if profit margins have been declining over time
        recent_cutoff = datetime.now() - timedelta(days=7)
        recent_trades = [
            t
            for t in full_history
            if t.get("executed_at", datetime.min) > recent_cutoff
        ]

        if len(recent_trades) >= 20:
            # Split into first half and second half
            mid = len(recent_trades) // 2
            first_half = recent_trades[:mid]
            second_half = recent_trades[mid:]

            # Compare average margins
            avg_margin_first = sum(t.get("profit_margin", 0) for t in first_half) / len(
                first_half
            )
            avg_margin_second = sum(
                t.get("profit_margin", 0) for t in second_half
            ) / len(second_half)

            # If margins declined by >30%, competition likely increased
            if avg_margin_second < avg_margin_first * 0.7:
                return True

        return False

    def generate_fix_suggestions(
        self, analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Generate specific recommendations based on analysis

        Args:
            analysis: Analysis results from analyze_losses()

        Returns:
            List of recommendation dictionaries
        """
        recommendations = []

        if analysis.get("insufficient_data"):
            return [
                {
                    "priority": "INFO",
                    "category": "insufficient_data",
                    "recommendation": "Continue trading to gather more data for analysis",
                    "actions": [],
                }
            ]

        # Generate recommendations for each category
        categories = analysis.get("categories", {})

        for category, data in sorted(
            categories.items(),
            key=lambda x: abs(x[1].get("total_loss", 0)),
            reverse=True,
        ):
            if data["count"] > 0:
                rec = self._generate_category_recommendation(category, data)
                recommendations.append(rec)

        # Log recommendations
        self._log_recommendations(recommendations)

        return recommendations

    def _generate_category_recommendation(
        self, category: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate recommendation for a specific loss category

        Args:
            category: Loss category name
            data: Category data from analysis

        Returns:
            Recommendation dictionary
        """
        templates = {
            "partial_fills": {
                "priority": "HIGH",
                "recommendation": "Reduce position sizes to ensure complete fills",
                "actions": [
                    "Lower max_trade_size in config (try 50% of current)",
                    "Avoid thin/low-liquidity markets",
                    "Add liquidity checks before trading",
                    "Consider splitting large orders",
                ],
            },
            "edge_lost_execution": {
                "priority": "CRITICAL",
                "recommendation": "Improve execution speed to capture opportunities faster",
                "actions": [
                    "Reduce request_delay_seconds in config",
                    "Optimize network latency (consider co-location)",
                    "Implement faster order routing",
                    "Use limit orders instead of market orders",
                    "Set tighter execution time limits",
                ],
            },
            "strategy_failure": {
                "priority": "CRITICAL",
                "recommendation": "Strategy logic needs review - market dynamics may have changed",
                "actions": [
                    "Disable failing strategy temporarily",
                    "Review and adjust strategy parameters",
                    "Backtest strategy with recent data",
                    "Consider switching to better-performing strategies",
                    "Check if assumptions are still valid",
                ],
            },
            "market_conditions": {
                "priority": "HIGH",
                "recommendation": "Market conditions changed - adjust strategy or pause trading",
                "actions": [
                    "Increase min_profit_margin threshold",
                    "Add volatility filters",
                    "Reduce position sizes during volatile periods",
                    "Focus on more stable markets",
                    "Consider pausing until conditions improve",
                ],
            },
            "competition": {
                "priority": "HIGH",
                "recommendation": "Increased competition - need faster execution or better edges",
                "actions": [
                    "Improve execution speed (see edge_lost_execution)",
                    "Target less competitive markets",
                    "Increase min_profit_margin to focus on better opportunities",
                    "Consider alternative strategies",
                    "Look for markets with less bot activity",
                ],
            },
            "other": {
                "priority": "MEDIUM",
                "recommendation": "Review individual trades for patterns",
                "actions": [
                    "Manual review of losing trades",
                    "Check for systematic errors",
                    "Verify data quality and API reliability",
                    "Look for edge cases in code",
                ],
            },
        }

        template = templates.get(category, templates["other"])

        return {
            "category": category,
            "priority": template["priority"],
            "count": data["count"],
            "total_loss": data["total_loss"],
            "percentage": data["percentage"],
            "recommendation": template["recommendation"],
            "actions": template["actions"],
        }

    def _log_analysis(self, analysis: Dict[str, Any]) -> None:
        """
        Log analysis results

        Args:
            analysis: Analysis results dictionary
        """
        if analysis.get("insufficient_data"):
            self.logger.log_warning(
                f"Loss Analysis: {analysis['message']} "
                f"({analysis['trade_count']} trades)"
            )
            return

        self.logger.log_critical(
            f"🔍 LOSS ANALYSIS RESULTS - Severity: {analysis['severity']}"
        )
        self.logger.log_critical(
            f"Total Trades: {analysis['total_trades']}, "
            f"Losing: {analysis['losing_trades']} "
            f"({analysis['losing_trades']/analysis['total_trades']*100:.1f}%)"
        )
        self.logger.log_critical(f"Total Loss: ${abs(analysis['total_loss']):.2f}")

        if analysis["primary_issue"]:
            self.logger.log_critical(f"PRIMARY ISSUE: {analysis['primary_issue']}")

        # Log category breakdown
        for category, data in analysis.get("categories", {}).items():
            self.logger.log_warning(
                f"  {category}: {data['count']} trades, "
                f"${abs(data['total_loss']):.2f} loss "
                f"({data['percentage']:.1f}% of losses)"
            )

    def _log_recommendations(self, recommendations: List[Dict[str, Any]]) -> None:
        """
        Log fix recommendations

        Args:
            recommendations: List of recommendation dictionaries
        """
        self.logger.log_critical("💡 FIX RECOMMENDATIONS:")

        for i, rec in enumerate(recommendations, 1):
            self.logger.log_critical(
                f"{i}. [{rec['priority']}] {rec['category']}: {rec['recommendation']}"
            )
            for action in rec["actions"]:
                self.logger.log_warning(f"   - {action}")
