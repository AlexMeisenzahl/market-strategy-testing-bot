"""
Telegram Notifications Module

Provides formatted notification messages for various trading events.
"""

from typing import Dict, Any, Optional
from datetime import datetime
from telegram_bot.bot import TelegramNotifier
from logger import get_logger


class TelegramNotifications:
    """
    Telegram notification service
    
    Formats and sends notifications for trading bot events.
    """
    
    def __init__(self, notifier: TelegramNotifier):
        """
        Initialize notifications service
        
        Args:
            notifier: TelegramNotifier instance
        """
        self.notifier = notifier
        self.logger = get_logger()
        self._notification_count = 0
        self._last_notification_time = datetime.now()
    
    def _check_rate_limit(self) -> bool:
        """
        Check if rate limit allows sending notification
        
        Returns:
            True if notification can be sent
        """
        if not self.notifier or not self.notifier.is_enabled():
            return False
        
        # Simple rate limiting
        rate_limit_config = self.notifier.config.get('rate_limit', {})
        max_per_minute = rate_limit_config.get('max_per_minute', 10)
        
        # Reset counter if minute has passed
        now = datetime.now()
        if (now - self._last_notification_time).total_seconds() >= 60:
            self._notification_count = 0
            self._last_notification_time = now
        
        # Check limit
        if self._notification_count >= max_per_minute:
            self.logger.log_warning("Telegram rate limit reached, skipping notification")
            return False
        
        self._notification_count += 1
        return True
    
    def send_trade_executed(
        self,
        market_name: str,
        direction: str,
        size: float,
        price: float,
        strategy: Optional[str] = None
    ) -> bool:
        """
        Send trade execution notification
        
        Args:
            market_name: Market name
            direction: Trade direction (buy/sell, long/short)
            size: Trade size in USD
            price: Execution price
            strategy: Strategy name (optional)
            
        Returns:
            True if sent successfully
        """
        if not self.notifier.should_send_notification('trade_executed'):
            return False
        
        if not self._check_rate_limit():
            return False
        
        strategy_text = f"\nStrategy: {strategy}" if strategy else ""
        
        message = f"""🤖 *Trade Executed*

Market: {market_name}
Direction: {direction.upper()}
Size: ${size:.2f}
Price: {price:.4f}{strategy_text}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
        
        return self.notifier.send_message_sync(message)
    
    def send_profit_loss_update(
        self,
        daily_pnl: float,
        daily_pnl_pct: float,
        total_pnl: float,
        win_rate: float
    ) -> bool:
        """
        Send profit/loss update notification
        
        Args:
            daily_pnl: Daily P&L in USD
            daily_pnl_pct: Daily P&L percentage
            total_pnl: Total P&L in USD
            win_rate: Win rate percentage
            
        Returns:
            True if sent successfully
        """
        if not self.notifier.should_send_notification('profit_loss_updates'):
            return False
        
        if not self._check_rate_limit():
            return False
        
        # Choose emoji based on P&L
        emoji = "💰" if daily_pnl >= 0 else "📉"
        
        message = f"""{emoji} *P&L Update*

Today: ${daily_pnl:.2f} ({daily_pnl_pct:+.2f}%)
Total: ${total_pnl:.2f}
Win Rate: {win_rate:.1f}%
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
        
        return self.notifier.send_message_sync(message)
    
    def send_strategy_triggered(
        self,
        strategy_name: str,
        market_name: str,
        confidence: float,
        action: str
    ) -> bool:
        """
        Send strategy trigger notification
        
        Args:
            strategy_name: Strategy name
            market_name: Market name
            confidence: Confidence score (0-100)
            action: Recommended action
            
        Returns:
            True if sent successfully
        """
        if not self.notifier.should_send_notification('strategy_triggered'):
            return False
        
        if not self._check_rate_limit():
            return False
        
        message = f"""🎯 *Opportunity Found*

Strategy: {strategy_name}
Market: {market_name}
Confidence: {confidence:.1f}%
Action: {action}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
        
        return self.notifier.send_message_sync(message)
    
    def send_error_alert(
        self,
        error_type: str,
        error_message: str
    ) -> bool:
        """
        Send error alert notification
        
        Args:
            error_type: Type of error
            error_message: Error message
            
        Returns:
            True if sent successfully
        """
        if not self.notifier.should_send_notification('error_alerts'):
            return False
        
        if not self._check_rate_limit():
            return False
        
        message = f"""⚠️ *Error Alert*

Type: {error_type}
Message: {error_message}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
        
        return self.notifier.send_message_sync(message)
    
    def send_status_change(
        self,
        status: str,
        message: str
    ) -> bool:
        """
        Send bot status change notification
        
        Args:
            status: New status
            message: Status message
            
        Returns:
            True if sent successfully
        """
        if not self.notifier.should_send_notification('status_change'):
            return False
        
        if not self._check_rate_limit():
            return False
        
        # Choose emoji based on status
        emoji_map = {
            'started': '🟢',
            'stopped': '🔴',
            'paused': '🟡',
            'error': '⚠️',
            'running': '▶️'
        }
        emoji = emoji_map.get(status.lower(), '📢')
        
        notification = f"""{emoji} *Bot Status Change*

Status: {status.upper()}
Message: {message}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
        
        return self.notifier.send_message_sync(notification)
    
    def send_daily_summary(
        self,
        trades_count: int,
        pnl: float,
        pnl_pct: float,
        win_rate: float,
        best_trade: Optional[Dict[str, Any]] = None,
        worst_trade: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send daily summary notification
        
        Args:
            trades_count: Number of trades executed
            pnl: Daily P&L in USD
            pnl_pct: Daily P&L percentage
            win_rate: Win rate percentage
            best_trade: Best trade info (optional)
            worst_trade: Worst trade info (optional)
            
        Returns:
            True if sent successfully
        """
        if not self.notifier.should_send_notification('daily_summary'):
            return False
        
        emoji = "📊"
        
        best_trade_text = ""
        if best_trade:
            best_trade_text = f"\n\nBest Trade: {best_trade.get('market', 'N/A')} (${best_trade.get('pnl', 0):.2f})"
        
        worst_trade_text = ""
        if worst_trade:
            worst_trade_text = f"\nWorst Trade: {worst_trade.get('market', 'N/A')} (${worst_trade.get('pnl', 0):.2f})"
        
        message = f"""{emoji} *Daily Summary*

Trades: {trades_count}
P&L: ${pnl:.2f} ({pnl_pct:+.2f}%)
Win Rate: {win_rate:.1f}%{best_trade_text}{worst_trade_text}

Date: {datetime.now().strftime('%Y-%m-%d')}"""
        
        return self.notifier.send_message_sync(message)


def create_notifications_service(notifier: TelegramNotifier) -> Optional[TelegramNotifications]:
    """
    Create notifications service
    
    Args:
        notifier: TelegramNotifier instance
        
    Returns:
        TelegramNotifications instance or None if notifier is None
    """
    if notifier is None:
        return None
    
    return TelegramNotifications(notifier)
