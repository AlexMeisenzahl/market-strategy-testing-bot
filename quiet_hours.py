"""
Quiet Hours Utility for Notification System

Allows configuration of quiet hours during which notifications are suppressed.
Supports timezone-aware time checking.
"""

from datetime import datetime, time, timedelta
from typing import Optional
import pytz


class QuietHours:
    """
    Quiet hours manager for notification system

    Prevents notifications during configured quiet hours
    (e.g., nighttime hours when user doesn't want to be disturbed).
    """

    def __init__(
        self,
        enabled: bool = False,
        start_time: str = "23:00",
        end_time: str = "07:00",
        timezone: str = "UTC",
    ):
        """
        Initialize quiet hours

        Args:
            enabled: Whether quiet hours are enabled (default: False)
            start_time: Start time in HH:MM format (default: "23:00")
            end_time: End time in HH:MM format (default: "07:00")
            timezone: Timezone name (default: "UTC")
        """
        self.enabled = enabled

        # Parse start and end times
        try:
            start_parts = start_time.split(":")
            self.start_hour = int(start_parts[0])
            self.start_minute = int(start_parts[1])

            end_parts = end_time.split(":")
            self.end_hour = int(end_parts[0])
            self.end_minute = int(end_parts[1])
        except (ValueError, IndexError):
            # Default to 23:00 - 07:00 if parsing fails
            self.start_hour = 23
            self.start_minute = 0
            self.end_hour = 7
            self.end_minute = 0

        # Load timezone
        try:
            self.timezone = pytz.timezone(timezone)
        except pytz.exceptions.UnknownTimeZoneError:
            # Default to UTC if timezone is invalid
            self.timezone = pytz.UTC

    def is_quiet_time(self) -> bool:
        """
        Check if current time is within quiet hours

        Returns:
            True if currently in quiet hours, False otherwise
        """
        if not self.enabled:
            return False

        # Get current time in configured timezone
        now = datetime.now(self.timezone)
        current_time = now.time()

        # Create time objects for start and end
        start = time(self.start_hour, self.start_minute)
        end = time(self.end_hour, self.end_minute)

        # Check if quiet hours span midnight
        if start < end:
            # Same day: e.g., 09:00 - 17:00
            return start <= current_time < end
        else:
            # Spans midnight: e.g., 23:00 - 07:00
            return current_time >= start or current_time < end

    def get_next_active_time(self) -> Optional[datetime]:
        """
        Get the next time when notifications will be active

        Returns:
            Datetime when quiet hours end, or None if not in quiet hours
        """
        if not self.enabled or not self.is_quiet_time():
            return None

        # Get current time in configured timezone
        now = datetime.now(self.timezone)

        # Create datetime for end time today
        end_today = now.replace(
            hour=self.end_hour, minute=self.end_minute, second=0, microsecond=0
        )

        # If end time is in the past today, it's tomorrow
        if end_today <= now:
            end_today += timedelta(days=1)

        return end_today

    def get_status(self) -> dict:
        """
        Get quiet hours status

        Returns:
            Dictionary with quiet hours information
        """
        return {
            "enabled": self.enabled,
            "is_quiet_now": self.is_quiet_time() if self.enabled else False,
            "start_time": f"{self.start_hour:02d}:{self.start_minute:02d}",
            "end_time": f"{self.end_hour:02d}:{self.end_minute:02d}",
            "timezone": str(self.timezone),
            "next_active_time": (
                self.get_next_active_time().isoformat()
                if self.is_quiet_time()
                else None
            ),
        }
