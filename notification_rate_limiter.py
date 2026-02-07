"""
Rate Limiter for Notification System

Prevents notification spam by limiting the rate of notifications sent.
Tracks notifications across multiple time windows (per minute, per hour).
"""

from datetime import datetime, timedelta
from typing import Dict, List
from collections import deque


class NotificationRateLimiter:
    """
    Rate limiter for notification system to prevent spam
    
    Tracks notifications across:
    - Per-minute limit
    - Per-hour limit
    - Cooldown periods after limit reached
    """
    
    def __init__(
        self, 
        max_per_minute: int = 5,
        max_per_hour: int = 20,
        cooldown_seconds: int = 30
    ):
        """
        Initialize rate limiter
        
        Args:
            max_per_minute: Maximum notifications per minute (default: 5)
            max_per_hour: Maximum notifications per hour (default: 20)
            cooldown_seconds: Cooldown period after limit reached (default: 30)
        """
        self.max_per_minute = max_per_minute
        self.max_per_hour = max_per_hour
        self.cooldown_seconds = cooldown_seconds
        
        # Track notification timestamps
        self.notifications_minute: deque = deque()  # Last minute
        self.notifications_hour: deque = deque()     # Last hour
        
        # Cooldown tracking
        self.cooldown_until: datetime = None
        
        # Statistics
        self.total_notifications = 0
        self.total_blocked = 0
    
    def allow(self) -> bool:
        """
        Check if a notification can be sent
        
        Returns:
            True if notification is allowed, False if rate limited
        """
        now = datetime.now()
        
        # Check if in cooldown period
        if self.cooldown_until and now < self.cooldown_until:
            self.total_blocked += 1
            return False
        
        # Clear cooldown if expired
        if self.cooldown_until and now >= self.cooldown_until:
            self.cooldown_until = None
        
        # Clean old notifications
        self._clean_old_notifications()
        
        # Check per-minute limit
        if len(self.notifications_minute) >= self.max_per_minute:
            self._trigger_cooldown()
            self.total_blocked += 1
            return False
        
        # Check per-hour limit
        if len(self.notifications_hour) >= self.max_per_hour:
            self._trigger_cooldown()
            self.total_blocked += 1
            return False
        
        return True
    
    def record(self) -> None:
        """Record that a notification was sent"""
        now = datetime.now()
        self.notifications_minute.append(now)
        self.notifications_hour.append(now)
        self.total_notifications += 1
    
    def _clean_old_notifications(self) -> None:
        """Remove notifications older than time windows"""
        now = datetime.now()
        
        # Clean minute window
        minute_ago = now - timedelta(minutes=1)
        while self.notifications_minute and self.notifications_minute[0] < minute_ago:
            self.notifications_minute.popleft()
        
        # Clean hour window
        hour_ago = now - timedelta(hours=1)
        while self.notifications_hour and self.notifications_hour[0] < hour_ago:
            self.notifications_hour.popleft()
    
    def _trigger_cooldown(self) -> None:
        """Trigger cooldown period"""
        self.cooldown_until = datetime.now() + timedelta(seconds=self.cooldown_seconds)
    
    def get_stats(self) -> Dict:
        """
        Get rate limiter statistics
        
        Returns:
            Dictionary with statistics
        """
        self._clean_old_notifications()
        
        return {
            'total_notifications': self.total_notifications,
            'total_blocked': self.total_blocked,
            'per_minute_count': len(self.notifications_minute),
            'per_minute_limit': self.max_per_minute,
            'per_hour_count': len(self.notifications_hour),
            'per_hour_limit': self.max_per_hour,
            'in_cooldown': self.cooldown_until is not None and datetime.now() < self.cooldown_until,
            'cooldown_seconds_remaining': (
                int((self.cooldown_until - datetime.now()).total_seconds())
                if self.cooldown_until and datetime.now() < self.cooldown_until
                else 0
            )
        }
    
    def reset(self) -> None:
        """Reset rate limiter (for testing purposes)"""
        self.notifications_minute.clear()
        self.notifications_hour.clear()
        self.cooldown_until = None
