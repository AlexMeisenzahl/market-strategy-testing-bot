"""
Notifier Module - Enhanced multi-channel notification system

Sends alerts through multiple channels:
- Desktop notifications (via plyer)
- Email alerts
- Telegram push notifications
- Sound alerts

Features:
- Granular event-type controls per channel
- Rate limiting to prevent spam
- Quiet hours support
- Priority-based routing
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from logger import get_logger
from notification_rate_limiter import NotificationRateLimiter
from quiet_hours import QuietHours
import platform


class Notifier:
    """
    Multi-channel notification system for trading alerts
    
    Routes notifications based on priority and configuration.
    Supports desktop, SMS, push, and sound alerts.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize notifier
        
        Args:
            config: Configuration dictionary from config.yaml
        """
        self.config = config
        self.logger = get_logger()
        
        # Load notification settings
        notif_config = config.get('notifications', {})
        
        # Desktop notifications
        desktop_config = notif_config.get('desktop', {})
        self.desktop_enabled = desktop_config.get('enabled',
                                                 config.get('desktop_notifications', False))
        self.desktop_event_types = desktop_config.get('event_types', {
            'trade': True,
            'opportunity': True,
            'error': True,
            'summary': True,
            'status_change': True
        })
        
        # Email notifications
        email_notif_config = notif_config.get('email', {})
        email_config = config.get('email', {})
        self.email_enabled = email_config.get('enabled', False)
        self.email_event_types = email_notif_config.get('event_types', {
            'trade': True,
            'opportunity': False,  # Too frequent for email
            'error': True,
            'summary': True,
            'status_change': True
        })
        self.email_from = email_config.get('from_email', '')
        self.email_to = email_config.get('to_email', '')
        self.smtp_server = email_config.get('smtp_server', '')
        self.smtp_port = email_config.get('smtp_port', 587)
        self.email_password = email_config.get('password', '')
        
        # Telegram notifications
        telegram_notif_config = notif_config.get('telegram', {})
        telegram_config = config.get('telegram', {})
        self.telegram_enabled = telegram_config.get('enabled', False)
        self.telegram_event_types = telegram_notif_config.get('event_types', {
            'trade': True,
            'opportunity': True,
            'error': True,
            'summary': True,
            'status_change': True
        })
        self.telegram_token = telegram_config.get('bot_token', '')
        self.telegram_chat_id = telegram_config.get('chat_id', '')
        
        # Sound alerts
        self.sound_enabled = config.get('sound_alerts', False)
        
        # Initialize rate limiter
        rate_limit_config = notif_config.get('rate_limiting', {})
        if rate_limit_config.get('enabled', True):
            self.rate_limiter = NotificationRateLimiter(
                max_per_minute=rate_limit_config.get('max_per_minute', 5),
                max_per_hour=rate_limit_config.get('max_per_hour', 20),
                cooldown_seconds=rate_limit_config.get('cooldown_seconds', 30)
            )
        else:
            self.rate_limiter = None
        
        # Initialize quiet hours
        quiet_hours_config = notif_config.get('quiet_hours', {})
        self.quiet_hours = QuietHours(
            enabled=quiet_hours_config.get('enabled', False),
            start_time=quiet_hours_config.get('start_time', '23:00'),
            end_time=quiet_hours_config.get('end_time', '07:00'),
            timezone=quiet_hours_config.get('timezone', 'UTC')
        )
        
        # Notification triggers
        self.triggers = config.get('notification_triggers', {})

        # Notification history
        self.notification_count = 0
        self.last_notification = None
        
        # Try to import plyer for desktop notifications
        self.plyer_available = False
        try:
            from plyer import notification
            self.plyer_notification = notification
            self.plyer_available = True
        except ImportError:
            self.logger.log_warning(
                "plyer not installed - desktop notifications disabled. "
                "Install with: pip install plyer"
            )
        
        self.logger.log_warning(
            f"Notifier initialized - "
            f"Desktop: {self.desktop_enabled}, Email: {self.email_enabled}, "
            f"Telegram: {self.telegram_enabled}, Sound: {self.sound_enabled}"
        )
    
    
    def should_send(self, event_type: str, channel: str) -> bool:
        """
        Check if notification should be sent based on config and rate limits
        
        Args:
            event_type: Type of event (trade, opportunity, error, summary, status_change)
            channel: Notification channel (desktop, email, telegram)
            
        Returns:
            True if notification should be sent, False otherwise
        """
        # Check if channel is enabled
        if channel == 'desktop' and not self.desktop_enabled:
            return False
        elif channel == 'email' and not self.email_enabled:
            return False
        elif channel == 'telegram' and not self.telegram_enabled:
            return False
        
        # Check if event type is enabled for this channel
        if channel == 'desktop':
            if not self.desktop_event_types.get(event_type, True):
                return False
        elif channel == 'email':
            if not self.email_event_types.get(event_type, True):
                return False
        elif channel == 'telegram':
            if not self.telegram_event_types.get(event_type, True):
                return False
        
        # Check rate limits
        if self.rate_limiter and not self.rate_limiter.allow():
            self.logger.log_warning(
                f"Notification rate limited: {event_type} on {channel}"
            )
            return False
        
        # Check quiet hours
        if self.quiet_hours.is_quiet_time():
            self.logger.log_warning(
                f"Notification suppressed (quiet hours): {event_type} on {channel}"
            )
            return False
        
        return True
    
    def notify(self, title: str, message: str, priority: str = "INFO", event_type: str = "status_change") -> None:
        """
        Send notification through appropriate channels based on priority and event type
        
        Args:
            title: Notification title
            message: Notification message
            priority: Priority level (CRITICAL, WARNING, INFO)
            event_type: Type of event (trade, opportunity, error, summary, status_change)
        """
        # Log the notification
        self.logger.log_warning(f"[{priority}] {title}: {message}")
        
        # Determine which channels to use based on priority (legacy logic)
        channels = self.determine_priority(priority)
        
        # Check each channel and send if allowed
        sent_any = False
        
        if 'desktop' in channels and self.should_send(event_type, 'desktop'):
            if self.send_desktop_notification(title, message):
                sent_any = True
        
        if 'email' in channels and self.should_send(event_type, 'email'):
            if self.send_email(f"{title}: {message}"):
                sent_any = True
        
        if 'telegram' in channels and self.should_send(event_type, 'telegram'):
            if self.send_push(title, message):
                sent_any = True
        
        if 'sound' in channels:
            self.play_alert_sound(priority)
        
        # Record notification if any channel succeeded
        if sent_any:
            self.notification_count += 1
            self.last_notification = datetime.now()
            if self.rate_limiter:
                self.rate_limiter.record()
    
    def determine_priority(self, event: str) -> list:
        """
        Determine which notification channels to use based on event priority
        
        Args:
            event: Event priority (CRITICAL, WARNING, INFO)
            
        Returns:
            List of channels to use
        """
        channels = []
        
        if event == "CRITICAL":
            # Critical: Use all available channels
            if self.email_enabled:
                channels.append('email')
            if self.telegram_enabled:
                channels.append('telegram')
            if self.desktop_enabled:
                channels.append('desktop')
            if self.sound_enabled:
                channels.append('sound')
        
        elif event == "WARNING":
            # Warning: Desktop + Sound
            if self.desktop_enabled:
                channels.append('desktop')
            if self.sound_enabled:
                channels.append('sound')
        
        else:  # INFO
            # Info: Desktop only
            if self.desktop_enabled:
                channels.append('desktop')
        
        return channels
    
    def send_desktop_notification(self, title: str, message: str) -> bool:
        """
        Send desktop notification via OS notification system
        
        Args:
            title: Notification title
            message: Notification message
            
        Returns:
            True if successful
        """
        if not self.desktop_enabled:
            return False
        
        if not self.plyer_available:
            # Fallback: just log it
            print(f"\n[NOTIFICATION] {title}\n{message}\n")
            return True
        
        try:
            # Try plyer first
            self.plyer_notification.notify(
                title=title,
                message=message,
                app_name="Market Strategy Testing Bot",
                timeout=10
            )
            return True
        except:
            # Fallback to osascript for macOS
            try:
                import subprocess
                subprocess.run([
                    'osascript', '-e',
                    f'display notification "{message}" with title "{title}"'
                ])
                return True
            except:
                self.logger.log_error("Desktop notification failed")
                return False

    def send_email(self, message: str) -> bool:
        """
        Send email notification
        
        Args:
            message: Email message
        
        Returns:
            True if successful
        """
        if not self.email_enabled:
            return False
        
        # Send via email
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            msg = MIMEMultipart()
            msg['From'] = self.email_from
            msg['To'] = self.email_to
            msg['Subject'] = "🚨 Market Strategy Bot Alert"
            
            msg.attach(MIMEText(message, 'plain'))
            
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email_from, self.email_password)
            server.send_message(msg)
            server.quit()
            
            self.logger.log_warning(f"[EMAIL SENT] {message}")
            return True
            
        except Exception as e:
            self.logger.log_error(f"Email error: {str(e)}")
            return False
    
    def send_push(self, title: str, message: str) -> bool:
        """
        Send push notification via Telegram
        
        Args:
            title: Notification title
            message: Notification message
        
        Returns:
            True if successful
        """
        if not self.telegram_enabled:
            return False
        
        # Send to Telegram
        try:
            import requests
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            payload = {
                'chat_id': self.telegram_chat_id,
                'text': f"🚨 *{title}*\n\n{message}",
                'parse_mode': 'Markdown'
            }
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                self.logger.log_warning(f"[TELEGRAM SENT] {title}: {message}")
                return True
            else:
                self.logger.log_error(f"Telegram failed: {response.text}")
                return False
                
        except Exception as e:
            self.logger.log_error(f"Telegram error: {str(e)}")
            return False
    
    def play_alert_sound(self, priority: str = "INFO") -> bool:
        """
        Play alert sound based on priority
        
        Args:
            priority: Priority level (CRITICAL, WARNING, INFO)
            
        Returns:
            True if successful
        """
        if not self.sound_enabled:
            return False
        
        # Different beep patterns for different priorities
        try:
            if platform.system() == 'Windows':
                import winsound
                if priority == "CRITICAL":
                    # Three urgent beeps
                    for _ in range(3):
                        winsound.Beep(1000, 200)
                elif priority == "WARNING":
                    # Two warning beeps
                    for _ in range(2):
                        winsound.Beep(800, 150)
                else:
                    # Single info beep
                    winsound.Beep(600, 100)
            else:
                # Unix/Linux/Mac - use system bell
                if priority == "CRITICAL":
                    print('\a\a\a', end='', flush=True)
                elif priority == "WARNING":
                    print('\a\a', end='', flush=True)
                else:
                    print('\a', end='', flush=True)
            
            return True
            
        except Exception as e:
            self.logger.log_error(f"Sound alert failed: {str(e)}")
            return False
    
    def alert_opportunity_found(self, market: str, profit_pct: float) -> None:
        """
        Alert when arbitrage opportunity is found
        
        Args:
            market: Market name
            profit_pct: Profit percentage
        """
        title = "Arbitrage Opportunity Found"
        message = f"{market}: {profit_pct:.2f}% profit potential"
        
        # Check for high-value opportunity trigger
        trigger_config = self.triggers.get('high_value_opportunity', {})
        if trigger_config.get('enabled', True):
            min_profit = trigger_config.get('min_profit_percent', 5.0)
            if profit_pct >= min_profit:
                # High value opportunity - use configured channels
                self.notify(title, message, priority="CRITICAL", event_type="opportunity")
                return
        
        self.notify(title, message, priority="CRITICAL", event_type="opportunity")
    
    def alert_trade_executed(self, market: str, profit_usd: float) -> None:
        """
        Alert when trade is executed
        
        Args:
            market: Market name
            profit_usd: Expected profit in USD
        """
        title = "Trade Executed"
        message = f"{market}: ${profit_usd:.2f} profit expected"
        
        self.notify(title, message, priority="CRITICAL", event_type="trade")
    
    def alert_circuit_breaker(self, reason: str) -> None:
        """
        Alert when circuit breaker is triggered
        
        Args:
            reason: Reason for circuit breaker
        """
        title = "⚠️ CIRCUIT BREAKER TRIGGERED"
        message = f"Trading paused: {reason}"
        
        self.notify(title, message, priority="CRITICAL", event_type="status_change")
    
    def alert_connection_issue(self, message: str) -> None:
        """
        Alert when connection issues detected
        
        Args:
            message: Issue description
        """
        title = "Connection Issue"
        
        # Check for API connection loss trigger
        trigger_config = self.triggers.get('api_connection_loss', {})
        if trigger_config.get('enabled', True):
            self.notify(title, message, priority="WARNING", event_type="error")
        else:
            self.notify(title, message, priority="WARNING", event_type="status_change")
    
    def alert_error(self, error_type: str, details: str) -> None:
        """
        Alert when error occurs
        
        Args:
            error_type: Type of error
            details: Error details
        """
        title = f"Error: {error_type}"
        
        self.notify(title, details, priority="WARNING", event_type="error")
    
    def alert_profit_milestone(self, total_profit: float, milestone: float) -> None:
        """
        Alert when profit milestone reached
        
        Args:
            total_profit: Current total profit
            milestone: Milestone reached
        """
        title = "🎉 Profit Milestone Reached!"
        message = f"Total profit: ${total_profit:.2f} (milestone: ${milestone:.2f})"
        
        # Check for daily profit milestone trigger
        trigger_config = self.triggers.get('daily_profit_milestone', {})
        if trigger_config.get('enabled', True):
            self.notify(title, message, priority="INFO", event_type="summary")
        else:
            self.notify(title, message, priority="INFO", event_type="status_change")
    
    def alert_loss_threshold(self, total_loss: float, threshold: float) -> None:
        """
        Alert when loss threshold exceeded
        
        Args:
            total_loss: Current total loss
            threshold: Loss threshold
        """
        title = "⚠️ Loss Threshold Exceeded"
        message = f"Total loss: ${total_loss:.2f} (threshold: ${threshold:.2f})"
        
        self.notify(title, message, priority="CRITICAL", event_type="error")
    
    def test_notifications(self) -> Dict[str, bool]:
        """
        Test all notification channels
        
        Returns:
            Dictionary with test results for each channel
        """
        results = {}
        
        # Test desktop
        if self.desktop_enabled:
            results['desktop'] = self.send_desktop_notification(
                "Test Notification",
                "This is a test of the desktop notification system"
            )
        
        # Test email
        if self.email_enabled:
            results['email'] = self.send_email(
                "Test Email: Arbitrage bot notification system test"
            )
        
        # Test telegram
        if self.telegram_enabled:
            results['telegram'] = self.send_push(
                "Test Push",
                "This is a test of the Telegram notification system"
            )
        
        # Test sound
        if self.sound_enabled:
            results['sound'] = self.play_alert_sound("INFO")
        
        self.logger.log_warning(f"Notification test results: {results}")
        
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get notification statistics
        
        Returns:
            Dictionary with notification stats
        """
        stats = {
            'total_notifications': self.notification_count,
            'last_notification': self.last_notification.isoformat() if self.last_notification else None,
            'channels_enabled': {
                'desktop': self.desktop_enabled,
                'email': self.email_enabled,
                'telegram': self.telegram_enabled,
                'sound': self.sound_enabled
            },
            'plyer_available': self.plyer_available
        }
        
        # Add rate limiter stats if enabled
        if self.rate_limiter:
            stats['rate_limiter'] = self.rate_limiter.get_stats()
        
        # Add quiet hours status
        stats['quiet_hours'] = self.quiet_hours.get_status()
        
        return stats
