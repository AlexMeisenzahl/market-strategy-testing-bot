"""
Rate Limiter

Token bucket rate limiter for API calls.
Thread-safe implementation to prevent exceeding API rate limits.
"""

import time
import threading
from collections import deque
from typing import Optional


class RateLimiter:
    """
    Thread-safe rate limiter using token bucket algorithm.

    Limits API calls to a specified number per minute.
    """

    def __init__(self, calls_per_minute: int):
        """
        Initialize rate limiter.

        Args:
            calls_per_minute: Maximum number of calls allowed per minute
        """
        if calls_per_minute <= 0:
            raise ValueError("calls_per_minute must be positive")

        self.calls_per_minute = calls_per_minute
        self.call_times = deque()
        self.lock = threading.Lock()
        self.window_seconds = 60.0

    def acquire(self, timeout: Optional[float] = None) -> bool:
        """
        Acquire permission to make an API call.

        Blocks if rate limit would be exceeded until a slot is available.

        Args:
            timeout: Maximum time to wait in seconds (None = wait indefinitely)

        Returns:
            True if acquired, False if timeout exceeded
        """
        start_time = time.time()

        while True:
            with self.lock:
                current_time = time.time()

                # Remove expired calls (older than 60 seconds)
                self._remove_expired_calls(current_time)

                # Check if we can make a call
                if len(self.call_times) < self.calls_per_minute:
                    self.call_times.append(current_time)
                    return True

                # Calculate wait time until oldest call expires
                oldest_call = self.call_times[0]
                wait_time = self.window_seconds - (current_time - oldest_call)

            # Check timeout
            if timeout is not None:
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    return False
                if wait_time > (timeout - elapsed):
                    wait_time = timeout - elapsed

            # Wait before retrying
            if wait_time > 0:
                time.sleep(wait_time)

    def get_remaining_calls(self) -> int:
        """
        Get number of remaining calls available in current window.

        Returns:
            Number of calls that can be made immediately
        """
        with self.lock:
            current_time = time.time()
            self._remove_expired_calls(current_time)
            return self.calls_per_minute - len(self.call_times)

    def reset(self):
        """
        Reset the rate limiter, clearing all tracked calls.
        """
        with self.lock:
            self.call_times.clear()

    def _remove_expired_calls(self, current_time: float):
        """
        Remove calls older than the time window.

        Args:
            current_time: Current timestamp
        """
        cutoff_time = current_time - self.window_seconds

        while self.call_times and self.call_times[0] < cutoff_time:
            self.call_times.popleft()

    def get_wait_time(self) -> float:
        """
        Get estimated wait time until next call can be made.

        Returns:
            Wait time in seconds (0 if call can be made immediately)
        """
        with self.lock:
            current_time = time.time()
            self._remove_expired_calls(current_time)

            if len(self.call_times) < self.calls_per_minute:
                return 0.0

            oldest_call = self.call_times[0]
            return self.window_seconds - (current_time - oldest_call)

    def __repr__(self) -> str:
        """String representation of rate limiter state."""
        return (
            f"RateLimiter(calls_per_minute={self.calls_per_minute}, "
            f"remaining={self.get_remaining_calls()})"
        )
