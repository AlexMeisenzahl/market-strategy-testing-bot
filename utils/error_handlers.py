"""
Error Handlers

Standard decorators for API error handling with retry logic.
"""

import time
import logging
import functools
from typing import Callable, Any, Optional, Type, Tuple

try:
    import requests
except ImportError:
    requests = None


logger = logging.getLogger(__name__)


def with_retry(
    max_retries: int = 3,
    backoff_factor: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
) -> Callable:
    """
    Decorator to retry a function with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        backoff_factor: Multiplier for exponential backoff (sleep = backoff_factor ** attempt)
        exceptions: Tuple of exception types to catch and retry

    Returns:
        Decorated function

    Example:
        @with_retry(max_retries=3, backoff_factor=2)
        def fetch_data():
            return api.get_data()
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt < max_retries:
                        # Calculate exponential backoff
                        sleep_time = backoff_factor**attempt

                        # Special handling for rate limit errors
                        if requests and isinstance(e, requests.HTTPError):
                            if e.response.status_code == 429:
                                logger.warning(
                                    f"{func.__name__}: Rate limit hit, "
                                    f"retrying in {sleep_time}s (attempt {attempt + 1}/{max_retries})"
                                )
                            elif 500 <= e.response.status_code < 600:
                                logger.warning(
                                    f"{func.__name__}: Server error {e.response.status_code}, "
                                    f"retrying in {sleep_time}s (attempt {attempt + 1}/{max_retries})"
                                )
                        else:
                            logger.warning(
                                f"{func.__name__}: {type(e).__name__}: {e}, "
                                f"retrying in {sleep_time}s (attempt {attempt + 1}/{max_retries})"
                            )

                        time.sleep(sleep_time)
                    else:
                        logger.error(
                            f"{func.__name__}: Failed after {max_retries} retries: {e}"
                        )

            # If all retries failed, raise the last exception
            raise last_exception

        return wrapper

    return decorator


def handle_api_error(default_return: Any = None) -> Callable:
    """
    Decorator to handle API errors gracefully by returning a default value.

    Args:
        default_return: Value to return if an error occurs

    Returns:
        Decorated function

    Example:
        @handle_api_error(default_return={})
        def fetch_data():
            return api.get_data()
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Log the error
                error_type = type(e).__name__

                if requests and isinstance(e, requests.Timeout):
                    logger.error(f"{func.__name__}: Request timeout: {e}")
                elif requests and isinstance(e, requests.HTTPError):
                    status_code = e.response.status_code if e.response else "unknown"
                    if status_code == 429:
                        logger.error(f"{func.__name__}: Rate limit exceeded")
                    elif isinstance(status_code, int) and 500 <= status_code < 600:
                        logger.error(f"{func.__name__}: Server error {status_code}")
                    else:
                        logger.error(f"{func.__name__}: HTTP error {status_code}: {e}")
                elif requests and isinstance(e, requests.RequestException):
                    logger.error(f"{func.__name__}: Request error: {e}")
                else:
                    logger.error(f"{func.__name__}: {error_type}: {e}")

                return default_return

        return wrapper

    return decorator


def handle_timeout(timeout_seconds: float, default_return: Any = None) -> Callable:
    """
    Decorator to handle function timeouts.

    Note: This is a simple timeout handler. For production use,
    consider using concurrent.futures or threading with proper timeout handling.

    Args:
        timeout_seconds: Maximum time to allow function to run
        default_return: Value to return if timeout occurs

    Returns:
        Decorated function
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            import signal

            def timeout_handler(signum, frame):
                raise TimeoutError(
                    f"{func.__name__} timed out after {timeout_seconds}s"
                )

            # Set up signal handler (Unix-like systems only)
            try:
                old_handler = signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(int(timeout_seconds))

                try:
                    result = func(*args, **kwargs)
                finally:
                    signal.alarm(0)
                    signal.signal(signal.SIGALRM, old_handler)

                return result
            except (AttributeError, ValueError):
                # signal.SIGALRM not available (Windows) or invalid timeout
                # Just run the function without timeout
                logger.warning(f"Timeout handling not available for {func.__name__}")
                return func(*args, **kwargs)
            except TimeoutError as e:
                logger.error(str(e))
                return default_return

        return wrapper

    return decorator


def log_errors(logger_instance: Optional[logging.Logger] = None) -> Callable:
    """
    Decorator to log errors without suppressing them.

    Args:
        logger_instance: Logger to use (defaults to module logger)

    Returns:
        Decorated function
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            log = logger_instance or logger
            try:
                return func(*args, **kwargs)
            except Exception as e:
                log.error(f"{func.__name__}: {type(e).__name__}: {e}", exc_info=True)
                raise

        return wrapper

    return decorator
