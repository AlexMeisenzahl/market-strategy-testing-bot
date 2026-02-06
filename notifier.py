"""
Notifier Module - Multi-channel notification system

Sends alerts through multiple channels:
- Desktop notifications (via plyer)
- SMS alerts (simulated for paper trading)
- Push notifications (simulated for paper trading)
- Sound alerts

Priority-based routing ensures critical alerts use all channels.
"""

from typing import Dict, Any, Optional
from datetime import datetime
from logger import get_logger
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
        
        self.desktop_enabled = notif_config.get('desktop_enabled', 
                                               config.get('desktop_notifications', False))
        self.sms_enabled = notif_config.get('sms_enabled', False)
        self.push_enabled = notif_config.get('push_enabled', False)
        self.sound_enabled = notif_config.get('sound_enabled', 
                                              config.get('sound_alerts', False))
        
        # Phone number for SMS (if configured)
        self.sms_phone = notif_config.get('sms_phone', '')
        
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
            f"Desktop: {self.desktop_enabled}, SMS: {self.sms_enabled}, "
            f"Push: {self.push_enabled}, Sound: {self.sound_enabled}"
        )
    
    def notify(self, title: str, message: str, priority: str = "INFO") -> None:
        """
        Send notification through appropriate channels based on priority
        
        Args:
            title: Notification title
            message: Notification message
            priority: Priority level (CRITICAL, WARNING, INFO)
        """
        self.notification_count += 1
        self.last_notification = datetime.now()
        
        # Determine which channels to use
        channels = self.determine_priority(priority)
        
        # Log the notification
        self.logger.log_warning(f"[{priority}] {title}: {message}")
        
        # Send through each channel
        if 'desktop' in channels:
            self.send_desktop_notification(title, message)
        
        if 'sms' in channels:
            self.send_sms(f"{title}: {message}")
        
        if 'push' in channels:
            self.send_push(title, message)
        
        if 'sound' in channels:
            self.play_alert_sound(priority)
    
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
            if self.sms_enabled:
                channels.append('sms')
            if self.push_enabled:
                channels.append('push')
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
            self.plyer_notification.notify(
                title=title,
                message=message,
                app_name="Arbitrage Bot",
                timeout=10  # Show for 10 seconds
            )
            return True
            
        except Exception as e:
            self.logger.log_error(f"Desktop notification failed: {str(e)}")
            return False
    
    def send_sms(self, message: str) -> bool:
        """
        Send SMS notification (simulated for paper trading)
        
        Args:
            message: SMS message
            
        Returns:
            True if successful
        """
        if not self.sms_enabled:
            return False
        
        # For paper trading, we simulate SMS
        # In production, this would use Twilio or similar service
        
        self.logger.log_warning(
            f"[SIMULATED SMS to {self.sms_phone}] {message}"
        )
        
        # Log to special SMS log file
        try:
            from pathlib import Path
            sms_log = Path("logs") / "sms_notifications.log"
            with open(sms_log, 'a') as f:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                f.write(f"[{timestamp}] To: {self.sms_phone} - {message}\n")
        except Exception as e:
            self.logger.log_error(f"SMS logging failed: {str(e)}")
        
        return True
    
    def send_push(self, title: str, message: str) -> bool:
        """
        Send push notification (simulated for paper trading)
        
        Args:
            title: Notification title
            message: Notification message
            
        Returns:
            True if successful
        """
        if not self.push_enabled:
            return False
        
        # For paper trading, we simulate push notifications
        # In production, this would use Firebase, Pushover, etc.
        
        self.logger.log_warning(
            f"[SIMULATED PUSH] {title}: {message}"
        )
        
        # Log to special push log file
        try:
            from pathlib import Path
            push_log = Path("logs") / "push_notifications.log"
            with open(push_log, 'a') as f:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                f.write(f"[{timestamp}] {title}: {message}\n")
        except Exception as e:
            self.logger.log_error(f"Push logging failed: {str(e)}")
        
        return True
    
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
        
        self.notify(title, message, priority="INFO")
    
    def alert_trade_executed(self, market: str, profit_usd: float) -> None:
        """
        Alert when trade is executed
        
        Args:
            market: Market name
            profit_usd: Expected profit in USD
        """
        title = "Trade Executed"
        message = f"{market}: ${profit_usd:.2f} profit expected"
        
        self.notify(title, message, priority="INFO")
    
    def alert_circuit_breaker(self, reason: str) -> None:
        """
        Alert when circuit breaker is triggered
        
        Args:
            reason: Reason for circuit breaker
        """
        title = "⚠️ CIRCUIT BREAKER TRIGGERED"
        message = f"Trading paused: {reason}"
        
        self.notify(title, message, priority="CRITICAL")
    
    def alert_connection_issue(self, message: str) -> None:
        """
        Alert when connection issues detected
        
        Args:
            message: Issue description
        """
        title = "Connection Issue"
        
        self.notify(title, message, priority="WARNING")
    
    def alert_error(self, error_type: str, details: str) -> None:
        """
        Alert when error occurs
        
        Args:
            error_type: Type of error
            details: Error details
        """
        title = f"Error: {error_type}"
        
        self.notify(title, details, priority="WARNING")
    
    def alert_profit_milestone(self, total_profit: float, milestone: float) -> None:
        """
        Alert when profit milestone reached
        
        Args:
            total_profit: Current total profit
            milestone: Milestone reached
        """
        title = "🎉 Profit Milestone Reached!"
        message = f"Total profit: ${total_profit:.2f} (milestone: ${milestone:.2f})"
        
        self.notify(title, message, priority="INFO")
    
    def alert_loss_threshold(self, total_loss: float, threshold: float) -> None:
        """
        Alert when loss threshold exceeded
        
        Args:
            total_loss: Current total loss
            threshold: Loss threshold
        """
        title = "⚠️ Loss Threshold Exceeded"
        message = f"Total loss: ${total_loss:.2f} (threshold: ${threshold:.2f})"
        
        self.notify(title, message, priority="CRITICAL")
    
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
        
        # Test SMS
        if self.sms_enabled:
            results['sms'] = self.send_sms(
                "Test SMS: Arbitrage bot notification system test"
            )
        
        # Test push
        if self.push_enabled:
            results['push'] = self.send_push(
                "Test Push",
                "This is a test of the push notification system"
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
        return {
            'total_notifications': self.notification_count,
            'last_notification': self.last_notification.isoformat() if self.last_notification else None,
            'channels_enabled': {
                'desktop': self.desktop_enabled,
                'sms': self.sms_enabled,
                'push': self.push_enabled,
                'sound': self.sound_enabled
            },
            'plyer_available': self.plyer_available
        }
