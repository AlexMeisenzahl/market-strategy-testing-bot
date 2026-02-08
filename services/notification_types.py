"""
Notification Types

Defines all 40+ notification types grouped by category.
"""

from typing import List, Dict, Optional
from enum import Enum


class NotificationCategory(Enum):
    """Notification categories"""

    OPPORTUNITIES = "opportunities"
    TRADES = "trades"
    PRICE_ALERTS = "price_alerts"
    SYSTEM = "system"
    RISK = "risk"
    PERFORMANCE = "performance"


class NotificationType:
    """Notification type definitions"""

    # OPPORTUNITIES (12 types)
    OPPORTUNITY_DETECTED = "opportunity_detected"
    SIMPLE_ARBITRAGE = "simple_arbitrage"
    CROSS_EXCHANGE_ARBITRAGE = "cross_exchange_arbitrage"
    CORRELATED_MARKETS = "correlated_markets"
    TIME_BASED_ARBITRAGE = "time_based_arbitrage"
    EVENT_DRIVEN_ARBITRAGE = "event_driven_arbitrage"
    REALITY_ARBITRAGE = "reality_arbitrage"
    MOMENTUM_SIGNAL = "momentum_signal"
    NEWS_SIGNAL = "news_signal"
    STATISTICAL_ARB_SIGNAL = "statistical_arb_signal"
    HIGH_PROFIT_OPPORTUNITY = "high_profit_opportunity"
    VERY_HIGH_CONFIDENCE_OPPORTUNITY = "very_high_confidence_opportunity"

    # TRADES (8 types)
    TRADE_EXECUTED = "trade_executed"
    TRADE_CLOSED = "trade_closed"
    TRADE_PROFITABLE = "trade_profitable"
    TRADE_LOSS = "trade_loss"
    LARGE_WIN = "large_win"
    LARGE_LOSS = "large_loss"
    TRADE_ERROR = "trade_error"
    PAPER_TRADE_EXECUTED = "paper_trade_executed"

    # PRICE ALERTS (6 types)
    PRICE_ALERT_TRIGGERED = "price_alert_triggered"
    PRICE_ABOVE_THRESHOLD = "price_above_threshold"
    PRICE_BELOW_THRESHOLD = "price_below_threshold"
    LARGE_PRICE_MOVE = "large_price_move"
    PRICE_DISCREPANCY = "price_discrepancy"
    ATH_ALERT = "ath_alert"

    # SYSTEM (8 types)
    BOT_STARTED = "bot_started"
    BOT_STOPPED = "bot_stopped"
    BOT_ERROR = "bot_error"
    API_ERROR = "api_error"
    API_RATE_LIMITED = "api_rate_limited"
    DATABASE_ERROR = "database_error"
    LOW_BALANCE_WARNING = "low_balance_warning"
    SYSTEM_HEALTH_CHECK = "system_health_check"

    # RISK (6 types)
    POSITION_SIZE_WARNING = "position_size_warning"
    DAILY_LOSS_LIMIT_APPROACHING = "daily_loss_limit_approaching"
    DAILY_LOSS_LIMIT_REACHED = "daily_loss_limit_reached"
    DRAWDOWN_WARNING = "drawdown_warning"
    CONSECUTIVE_LOSSES = "consecutive_losses"
    LOW_WIN_RATE = "low_win_rate"

    # PERFORMANCE (6 types)
    DAILY_SUMMARY = "daily_summary"
    WEEKLY_SUMMARY = "weekly_summary"
    MONTHLY_SUMMARY = "monthly_summary"
    PROFIT_TARGET_REACHED = "profit_target_reached"
    NEW_RECORD_PROFIT = "new_record_profit"
    STRATEGY_UNDERPERFORMING = "strategy_underperforming"

    # Category mappings
    _CATEGORY_MAP = {
        # Opportunities
        OPPORTUNITY_DETECTED: NotificationCategory.OPPORTUNITIES,
        SIMPLE_ARBITRAGE: NotificationCategory.OPPORTUNITIES,
        CROSS_EXCHANGE_ARBITRAGE: NotificationCategory.OPPORTUNITIES,
        CORRELATED_MARKETS: NotificationCategory.OPPORTUNITIES,
        TIME_BASED_ARBITRAGE: NotificationCategory.OPPORTUNITIES,
        EVENT_DRIVEN_ARBITRAGE: NotificationCategory.OPPORTUNITIES,
        REALITY_ARBITRAGE: NotificationCategory.OPPORTUNITIES,
        MOMENTUM_SIGNAL: NotificationCategory.OPPORTUNITIES,
        NEWS_SIGNAL: NotificationCategory.OPPORTUNITIES,
        STATISTICAL_ARB_SIGNAL: NotificationCategory.OPPORTUNITIES,
        HIGH_PROFIT_OPPORTUNITY: NotificationCategory.OPPORTUNITIES,
        VERY_HIGH_CONFIDENCE_OPPORTUNITY: NotificationCategory.OPPORTUNITIES,
        # Trades
        TRADE_EXECUTED: NotificationCategory.TRADES,
        TRADE_CLOSED: NotificationCategory.TRADES,
        TRADE_PROFITABLE: NotificationCategory.TRADES,
        TRADE_LOSS: NotificationCategory.TRADES,
        LARGE_WIN: NotificationCategory.TRADES,
        LARGE_LOSS: NotificationCategory.TRADES,
        TRADE_ERROR: NotificationCategory.TRADES,
        PAPER_TRADE_EXECUTED: NotificationCategory.TRADES,
        # Price Alerts
        PRICE_ALERT_TRIGGERED: NotificationCategory.PRICE_ALERTS,
        PRICE_ABOVE_THRESHOLD: NotificationCategory.PRICE_ALERTS,
        PRICE_BELOW_THRESHOLD: NotificationCategory.PRICE_ALERTS,
        LARGE_PRICE_MOVE: NotificationCategory.PRICE_ALERTS,
        PRICE_DISCREPANCY: NotificationCategory.PRICE_ALERTS,
        ATH_ALERT: NotificationCategory.PRICE_ALERTS,
        # System
        BOT_STARTED: NotificationCategory.SYSTEM,
        BOT_STOPPED: NotificationCategory.SYSTEM,
        BOT_ERROR: NotificationCategory.SYSTEM,
        API_ERROR: NotificationCategory.SYSTEM,
        API_RATE_LIMITED: NotificationCategory.SYSTEM,
        DATABASE_ERROR: NotificationCategory.SYSTEM,
        LOW_BALANCE_WARNING: NotificationCategory.SYSTEM,
        SYSTEM_HEALTH_CHECK: NotificationCategory.SYSTEM,
        # Risk
        POSITION_SIZE_WARNING: NotificationCategory.RISK,
        DAILY_LOSS_LIMIT_APPROACHING: NotificationCategory.RISK,
        DAILY_LOSS_LIMIT_REACHED: NotificationCategory.RISK,
        DRAWDOWN_WARNING: NotificationCategory.RISK,
        CONSECUTIVE_LOSSES: NotificationCategory.RISK,
        LOW_WIN_RATE: NotificationCategory.RISK,
        # Performance
        DAILY_SUMMARY: NotificationCategory.PERFORMANCE,
        WEEKLY_SUMMARY: NotificationCategory.PERFORMANCE,
        MONTHLY_SUMMARY: NotificationCategory.PERFORMANCE,
        PROFIT_TARGET_REACHED: NotificationCategory.PERFORMANCE,
        NEW_RECORD_PROFIT: NotificationCategory.PERFORMANCE,
        STRATEGY_UNDERPERFORMING: NotificationCategory.PERFORMANCE,
    }

    # Display names
    _DISPLAY_NAMES = {
        # Opportunities
        OPPORTUNITY_DETECTED: "Opportunity Detected",
        SIMPLE_ARBITRAGE: "Simple Arbitrage",
        CROSS_EXCHANGE_ARBITRAGE: "Cross-Exchange Arbitrage",
        CORRELATED_MARKETS: "Correlated Markets",
        TIME_BASED_ARBITRAGE: "Time-Based Arbitrage",
        EVENT_DRIVEN_ARBITRAGE: "Event-Driven Arbitrage",
        REALITY_ARBITRAGE: "Reality Arbitrage",
        MOMENTUM_SIGNAL: "Momentum Signal",
        NEWS_SIGNAL: "News Signal",
        STATISTICAL_ARB_SIGNAL: "Statistical Arbitrage Signal",
        HIGH_PROFIT_OPPORTUNITY: "High Profit Opportunity",
        VERY_HIGH_CONFIDENCE_OPPORTUNITY: "Very High Confidence Opportunity",
        # Trades
        TRADE_EXECUTED: "Trade Executed",
        TRADE_CLOSED: "Trade Closed",
        TRADE_PROFITABLE: "Profitable Trade",
        TRADE_LOSS: "Trade Loss",
        LARGE_WIN: "Large Win",
        LARGE_LOSS: "Large Loss",
        TRADE_ERROR: "Trade Error",
        PAPER_TRADE_EXECUTED: "Paper Trade Executed",
        # Price Alerts
        PRICE_ALERT_TRIGGERED: "Price Alert Triggered",
        PRICE_ABOVE_THRESHOLD: "Price Above Threshold",
        PRICE_BELOW_THRESHOLD: "Price Below Threshold",
        LARGE_PRICE_MOVE: "Large Price Move",
        PRICE_DISCREPANCY: "Price Discrepancy",
        ATH_ALERT: "All-Time High Alert",
        # System
        BOT_STARTED: "Bot Started",
        BOT_STOPPED: "Bot Stopped",
        BOT_ERROR: "Bot Error",
        API_ERROR: "API Error",
        API_RATE_LIMITED: "API Rate Limited",
        DATABASE_ERROR: "Database Error",
        LOW_BALANCE_WARNING: "Low Balance Warning",
        SYSTEM_HEALTH_CHECK: "System Health Check",
        # Risk
        POSITION_SIZE_WARNING: "Position Size Warning",
        DAILY_LOSS_LIMIT_APPROACHING: "Daily Loss Limit Approaching",
        DAILY_LOSS_LIMIT_REACHED: "Daily Loss Limit Reached",
        DRAWDOWN_WARNING: "Drawdown Warning",
        CONSECUTIVE_LOSSES: "Consecutive Losses",
        LOW_WIN_RATE: "Low Win Rate",
        # Performance
        DAILY_SUMMARY: "Daily Summary",
        WEEKLY_SUMMARY: "Weekly Summary",
        MONTHLY_SUMMARY: "Monthly Summary",
        PROFIT_TARGET_REACHED: "Profit Target Reached",
        NEW_RECORD_PROFIT: "New Record Profit",
        STRATEGY_UNDERPERFORMING: "Strategy Underperforming",
    }

    @classmethod
    def get_all_types(cls) -> List[str]:
        """
        Get all notification type constants.

        Returns:
            List of all notification type strings
        """
        return list(cls._CATEGORY_MAP.keys())

    @classmethod
    def get_display_name(cls, notification_type: str) -> str:
        """
        Get display name for a notification type.

        Args:
            notification_type: Notification type constant

        Returns:
            Human-readable display name
        """
        return cls._DISPLAY_NAMES.get(
            notification_type, notification_type.replace("_", " ").title()
        )

    @classmethod
    def get_category(cls, notification_type: str) -> Optional[NotificationCategory]:
        """
        Get category for a notification type.

        Args:
            notification_type: Notification type constant

        Returns:
            NotificationCategory enum value or None
        """
        return cls._CATEGORY_MAP.get(notification_type)

    @classmethod
    def get_types_by_category(cls, category: NotificationCategory) -> List[str]:
        """
        Get all notification types in a category.

        Args:
            category: NotificationCategory enum value

        Returns:
            List of notification type strings
        """
        return [
            notif_type
            for notif_type, cat in cls._CATEGORY_MAP.items()
            if cat == category
        ]

    @classmethod
    def get_all_categories(cls) -> List[NotificationCategory]:
        """
        Get all notification categories.

        Returns:
            List of NotificationCategory enum values
        """
        return list(NotificationCategory)

    @classmethod
    def get_category_display_name(cls, category: NotificationCategory) -> str:
        """
        Get display name for a category.

        Args:
            category: NotificationCategory enum value

        Returns:
            Human-readable category name
        """
        names = {
            NotificationCategory.OPPORTUNITIES: "Opportunities",
            NotificationCategory.TRADES: "Trades",
            NotificationCategory.PRICE_ALERTS: "Price Alerts",
            NotificationCategory.SYSTEM: "System",
            NotificationCategory.RISK: "Risk Management",
            NotificationCategory.PERFORMANCE: "Performance",
        }
        return names.get(category, category.value.title())

    @classmethod
    def get_structured_types(cls) -> Dict[str, List[Dict[str, str]]]:
        """
        Get all notification types structured by category.

        Returns:
            Dictionary mapping category names to lists of type info
        """
        result = {}

        for category in cls.get_all_categories():
            category_name = cls.get_category_display_name(category)
            types = cls.get_types_by_category(category)

            result[category_name] = [
                {"type": notif_type, "display_name": cls.get_display_name(notif_type)}
                for notif_type in types
            ]

        return result
