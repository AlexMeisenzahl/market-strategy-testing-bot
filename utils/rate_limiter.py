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


class PriorityRateLimiter(RateLimiter):
    """
    Rate limiter with priority queue for API requests
    
    Priority levels:
    - 1: Emergency (cancel order, stop-loss)
    - 5: Normal (check prices, execute trades)
    - 10: Low (historical data, analytics)
    
    Processes high-priority requests first while respecting rate limits.
    """

    def __init__(self, calls_per_minute: int):
        """
        Initialize priority rate limiter
        
        Args:
            calls_per_minute: Maximum number of calls allowed per minute
        """
        super().__init__(calls_per_minute)
        import heapq
        self.request_queue = []  # Min heap by priority
        self.processing = False
        self.heapq = heapq
    
    def queue_request(self, api_func, args=None, kwargs=None, priority: int = 5):
        """
        Queue an API request with priority
        
        Args:
            api_func: Function to call
            args: Positional arguments
            kwargs: Keyword arguments
            priority: Priority level (1=highest, 10=lowest)
            
        Returns:
            Request ID for tracking
        """
        import uuid
        
        request_id = str(uuid.uuid4())
        request = {
            'id': request_id,
            'priority': priority,
            'func': api_func,
            'args': args or [],
            'kwargs': kwargs or {},
            'queued_at': time.time(),
            'result': None,
            'error': None,
            'completed': False
        }
        
        with self.lock:
            self.heapq.heappush(
                self.request_queue,
                (priority, time.time(), request)
            )
        
        self.logger.debug(
            f"Request queued: {request_id} (priority: {priority})"
        )
        
        return request_id
    
    def process_queue(self, max_requests: int = None) -> Dict:
        """
        Process queued requests
        
        Args:
            max_requests: Maximum number of requests to process (None = all)
            
        Returns:
            Dict with processing results
        """
        if self.processing:
            self.logger.warning("Queue processing already in progress")
            return {'success': False, 'error': 'Already processing'}
        
        self.processing = True
        processed = 0
        succeeded = 0
        failed = 0
        results = []
        
        try:
            while self.request_queue:
                if max_requests and processed >= max_requests:
                    break
                
                # Get highest priority request
                with self.lock:
                    if not self.request_queue:
                        break
                    priority, queued_time, request = self.heapq.heappop(
                        self.request_queue
                    )
                
                # Acquire rate limit permission
                acquired = self.acquire(timeout=30.0)
                
                if not acquired:
                    # Put request back in queue
                    with self.lock:
                        self.heapq.heappush(
                            self.request_queue,
                            (priority, queued_time, request)
                        )
                    self.logger.warning("Rate limit timeout, requeueing")
                    break
                
                # Execute request
                try:
                    result = request['func'](
                        *request['args'],
                        **request['kwargs']
                    )
                    request['result'] = result
                    request['completed'] = True
                    succeeded += 1
                    
                    self.logger.debug(
                        f"Request completed: {request['id']} "
                        f"(priority: {priority})"
                    )
                    
                except Exception as e:
                    request['error'] = str(e)
                    request['completed'] = True
                    failed += 1
                    
                    self.logger.error(
                        f"Request failed: {request['id']} - {e}"
                    )
                
                processed += 1
                results.append(request)
            
            return {
                'success': True,
                'processed': processed,
                'succeeded': succeeded,
                'failed': failed,
                'remaining_in_queue': len(self.request_queue),
                'results': results
            }
            
        finally:
            self.processing = False
    
    def get_queue_status(self) -> Dict:
        """
        Get queue status
        
        Returns:
            Dict with queue metrics
        """
        with self.lock:
            queue_size = len(self.request_queue)
            
            # Count by priority
            priority_counts = {}
            for priority, _, _ in self.request_queue:
                priority_counts[priority] = priority_counts.get(priority, 0) + 1
        
        return {
            'queue_size': queue_size,
            'processing': self.processing,
            'priority_counts': priority_counts,
            'remaining_calls': self.get_remaining_calls()
        }
    
    def clear_queue(self):
        """Clear all queued requests"""
        with self.lock:
            self.request_queue.clear()
        self.logger.info("Request queue cleared")


# Add logging to PriorityRateLimiter
import logging
PriorityRateLimiter.logger = logging.getLogger(__name__)
