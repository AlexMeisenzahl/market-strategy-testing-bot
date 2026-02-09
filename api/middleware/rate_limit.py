"""
Rate Limiting Middleware

Implements rate limiting for API endpoints to prevent abuse.

Note: This implementation uses a simple in-memory dictionary which is
suitable for single-instance deployments. For multi-instance deployments,
consider using Redis or another distributed cache.
"""

from fastapi import FastAPI, Request, HTTPException, status
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, Tuple
import asyncio
import threading

from logger import get_logger

logger = get_logger()


class RateLimiter:
    """
    Simple in-memory rate limiter
    
    Tracks request counts per IP address and enforces rate limits.
    
    Note: This uses a simple lock for thread safety. For high-performance
    async applications, consider using an async-compatible lock or
    a distributed cache like Redis.
    """
    
    def __init__(self, requests_per_minute: int = 60, burst: int = 10):
        """
        Initialize rate limiter
        
        Args:
            requests_per_minute: Maximum requests per minute
            burst: Maximum burst requests
        """
        self.requests_per_minute = requests_per_minute
        self.burst = burst
        
        # Track requests: {ip: [(timestamp, count), ...]}
        self.requests: Dict[str, list] = defaultdict(list)
        
        # Thread lock for safe access to shared state
        self._lock = threading.Lock()
        
        # Cleanup task
        self._cleanup_task = None
    
    def _cleanup_old_requests(self):
        """Remove old request records"""
        cutoff = datetime.now() - timedelta(minutes=2)
        
        for ip in list(self.requests.keys()):
            self.requests[ip] = [
                (ts, count) for ts, count in self.requests[ip]
                if ts > cutoff
            ]
            
            # Remove empty entries
            if not self.requests[ip]:
                del self.requests[ip]
    
    async def check_rate_limit(self, ip: str) -> Tuple[bool, str]:
        """
        Check if request should be allowed
        
        Args:
            ip: Client IP address
            
        Returns:
            Tuple of (allowed, reason)
        """
        with self._lock:  # Thread-safe access to shared state
            now = datetime.now()
            minute_ago = now - timedelta(minutes=1)
            
            # Get recent requests
            recent_requests = [
                (ts, count) for ts, count in self.requests[ip]
                if ts > minute_ago
            ]
            
            # Count total requests in the last minute
            total_requests = sum(count for _, count in recent_requests)
            
            # Check burst limit (last 10 seconds)
            ten_seconds_ago = now - timedelta(seconds=10)
            burst_requests = sum(
                count for ts, count in recent_requests
                if ts > ten_seconds_ago
            )
            
            # Enforce limits
            if burst_requests >= self.burst:
                return False, f"Burst limit exceeded ({self.burst} requests per 10 seconds)"
            
            if total_requests >= self.requests_per_minute:
                return False, f"Rate limit exceeded ({self.requests_per_minute} requests per minute)"
            
            # Record this request
            self.requests[ip].append((now, 1))
            
            # Cleanup old requests periodically
            if len(self.requests) > 1000:  # Arbitrary threshold
                self._cleanup_old_requests()
            
            return True, ""


# Global rate limiter instance
_rate_limiter: RateLimiter = None


def get_rate_limiter() -> RateLimiter:
    """Get the global rate limiter instance"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter


def setup_rate_limiting(app: FastAPI, requests_per_minute: int = 60, burst: int = 10):
    """
    Setup rate limiting middleware for FastAPI app
    
    Args:
        app: FastAPI application
        requests_per_minute: Maximum requests per minute
        burst: Maximum burst requests
    """
    global _rate_limiter
    _rate_limiter = RateLimiter(requests_per_minute, burst)
    
    @app.middleware("http")
    async def rate_limit_middleware(request: Request, call_next):
        """Rate limiting middleware"""
        
        # Skip rate limiting for health check
        if request.url.path == "/api/health":
            return await call_next(request)
        
        # Get client IP
        client_ip = request.client.host
        
        # Check rate limit
        allowed, reason = await _rate_limiter.check_rate_limit(client_ip)
        
        if not allowed:
            logger.log_warning(f"Rate limit exceeded for {client_ip}: {reason}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=reason
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(_rate_limiter.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(
            _rate_limiter.requests_per_minute - 
            sum(count for _, count in _rate_limiter.requests.get(client_ip, []))
        )
        
        return response
    
    logger.log_info(f"Rate limiting enabled: {requests_per_minute} req/min, burst: {burst}")
