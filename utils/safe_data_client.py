"""
Safe Data Client Wrapper

Provides graceful fallback handling for API calls with automatic retry
and fallback to mock/cached data when APIs are unavailable.
"""

import logging
import time
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union, Tuple
from functools import wraps

from utils.error_handlers import with_retry

logger = logging.getLogger(__name__)

T = TypeVar("T")


class SafeDataClient:
    """
    Wrapper for data clients that provides graceful fallbacks
    and resilient error handling.
    """

    def __init__(
        self,
        primary_client: Any,
        fallback_client: Optional[Any] = None,
        enable_caching: bool = True,
    ):
        """
        Initialize safe data client wrapper.

        Args:
            primary_client: Primary data source client
            fallback_client: Fallback client to use if primary fails
            enable_caching: Whether to cache successful responses
        """
        self.primary_client = primary_client
        self.fallback_client = fallback_client
        self.enable_caching = enable_caching
        self._cache: Dict[str, Tuple[Any, float]] = {}
        self._cache_ttl = 300  # 5 minutes default
        self._primary_failures = 0
        self._max_failures_before_fallback = 3

    def _get_from_cache(self, key: str) -> Optional[Any]:
        """Get cached value if available and not expired."""
        if not self.enable_caching or key not in self._cache:
            return None

        value, timestamp = self._cache[key]
        if time.time() - timestamp < self._cache_ttl:
            logger.debug(f"Cache hit for key: {key}")
            return value
        else:
            # Expired cache entry
            del self._cache[key]
            return None

    def _save_to_cache(self, key: str, value: Any):
        """Save value to cache with current timestamp."""
        if self.enable_caching:
            self._cache[key] = (value, time.time())
            logger.debug(f"Cached value for key: {key}")

    def _should_use_fallback(self) -> bool:
        """Determine if fallback should be used instead of primary."""
        return (
            self.fallback_client is not None
            and self._primary_failures >= self._max_failures_before_fallback
        )

    def safe_call(
        self,
        method_name: str,
        *args,
        cache_key: Optional[str] = None,
        use_fallback_on_error: bool = True,
        **kwargs,
    ) -> Optional[Any]:
        """
        Safely call a method on the data client with automatic fallback.

        Args:
            method_name: Name of method to call
            *args: Positional arguments for the method
            cache_key: Optional cache key for this call
            use_fallback_on_error: Whether to use fallback on error
            **kwargs: Keyword arguments for the method

        Returns:
            Result from the method call, or None if all attempts fail
        """
        # Check cache first
        if cache_key:
            cached_result = self._get_from_cache(cache_key)
            if cached_result is not None:
                return cached_result

        # Try primary client first (unless too many failures)
        if not self._should_use_fallback():
            try:
                # Get method from primary client
                if not hasattr(self.primary_client, method_name):
                    logger.error(f"Primary client has no method: {method_name}")
                    if use_fallback_on_error and self.fallback_client:
                        return self._try_fallback(method_name, *args, **kwargs)
                    return None

                method = getattr(self.primary_client, method_name)
                result = method(*args, **kwargs)

                # Success - reset failure counter
                self._primary_failures = 0

                # Cache the result
                if cache_key:
                    self._save_to_cache(cache_key, result)

                return result

            except Exception as e:
                self._primary_failures += 1
                logger.warning(
                    f"Primary client '{method_name}' failed (failures: {self._primary_failures}): {e}"
                )

                # Try fallback if enabled
                if use_fallback_on_error and self.fallback_client:
                    return self._try_fallback(
                        method_name, *args, cache_key=cache_key, **kwargs
                    )

                return None
        else:
            # Too many primary failures, use fallback directly
            logger.info(
                f"Using fallback client for '{method_name}' due to repeated primary failures"
            )
            return self._try_fallback(method_name, *args, cache_key=cache_key, **kwargs)

    def _try_fallback(
        self, method_name: str, *args, cache_key: Optional[str] = None, **kwargs
    ) -> Optional[Any]:
        """Try calling method on fallback client."""
        if not self.fallback_client:
            return None

        try:
            if not hasattr(self.fallback_client, method_name):
                logger.error(f"Fallback client has no method: {method_name}")
                return None

            method = getattr(self.fallback_client, method_name)
            result = method(*args, **kwargs)

            # Cache fallback result too
            if cache_key:
                self._save_to_cache(cache_key, result)

            logger.info(f"Fallback client '{method_name}' succeeded")
            return result

        except Exception as e:
            logger.error(f"Fallback client '{method_name}' also failed: {e}")
            return None

    def reset_failure_count(self):
        """Reset the primary client failure counter."""
        self._primary_failures = 0
        logger.info("Primary client failure counter reset")

    def clear_cache(self):
        """Clear all cached data."""
        self._cache.clear()
        logger.info("Cache cleared")

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the safe client."""
        return {
            "primary_failures": self._primary_failures,
            "using_fallback": self._should_use_fallback(),
            "cache_entries": len(self._cache),
            "cache_enabled": self.enable_caching,
            "has_fallback": self.fallback_client is not None,
        }


def safe_api_call(
    default_return: Any = None,
    log_errors: bool = True,
    retry_attempts: int = 3,
    retry_backoff: float = 2.0,
) -> Callable:
    """
    Decorator for safe API calls with retry logic and graceful degradation.

    Args:
        default_return: Value to return if all attempts fail
        log_errors: Whether to log errors
        retry_attempts: Number of retry attempts
        retry_backoff: Backoff multiplier for retries

    Returns:
        Decorator function
    """

    def decorator(func: Callable[..., T]) -> Callable[..., Union[T, Any]]:
        @wraps(func)
        @with_retry(max_retries=retry_attempts, backoff_factor=retry_backoff)
        def wrapper(*args, **kwargs) -> Union[T, Any]:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if log_errors:
                    logger.error(f"API call {func.__name__} failed: {e}")
                return default_return

        return wrapper

    return decorator


class DataClientFactory:
    """Factory for creating safe data clients with appropriate fallbacks."""

    @staticmethod
    def create_market_client(
        primary: Any, fallback: Optional[Any] = None, enable_caching: bool = True
    ) -> SafeDataClient:
        """
        Create a safe market data client.

        Args:
            primary: Primary market data client
            fallback: Fallback client (e.g., MockMarketClient)
            enable_caching: Enable response caching

        Returns:
            SafeDataClient instance
        """
        return SafeDataClient(
            primary_client=primary,
            fallback_client=fallback,
            enable_caching=enable_caching,
        )

    @staticmethod
    def create_crypto_client(
        primary: Any, fallback: Optional[Any] = None, enable_caching: bool = True
    ) -> SafeDataClient:
        """
        Create a safe crypto data client.

        Args:
            primary: Primary crypto data client
            fallback: Fallback client (e.g., MockCryptoClient)
            enable_caching: Enable response caching

        Returns:
            SafeDataClient instance
        """
        return SafeDataClient(
            primary_client=primary,
            fallback_client=fallback,
            enable_caching=enable_caching,
        )
