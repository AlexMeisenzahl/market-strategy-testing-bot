"""
Standardized API Response Helper

Ensures all API endpoints return consistent response format.
"""

from datetime import datetime
from typing import Any, Dict, Optional
from functools import wraps
import time


class APIResponse:
    """Helper class for creating standardized API responses."""

    VERSION = "1.0"

    @staticmethod
    def success(
        data: Any = None, message: Optional[str] = None, meta: Optional[Dict] = None
    ) -> Dict:
        """
        Create a success response.

        Args:
            data: Response data
            message: Optional success message
            meta: Optional metadata

        Returns:
            Standardized response dictionary
        """
        response = {
            "success": True,
            "data": data,
            "error": None,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            "meta": {"version": APIResponse.VERSION, **(meta or {})},
        }
        return response

    @staticmethod
    def error(
        error_message: str,
        error_code: Optional[str] = None,
        status_code: int = 400,
        meta: Optional[Dict] = None,
    ) -> tuple:
        """
        Create an error response.

        Args:
            error_message: Error message
            error_code: Optional error code
            status_code: HTTP status code
            meta: Optional metadata

        Returns:
            Tuple of (response_dict, status_code)
        """
        response = {
            "success": False,
            "data": None,
            "error": {"message": error_message, "code": error_code},
            "message": None,
            "timestamp": datetime.utcnow().isoformat(),
            "meta": {"version": APIResponse.VERSION, **(meta or {})},
        }
        return response, status_code

    @staticmethod
    def paginated(
        data: list, page: int, per_page: int, total: int, meta: Optional[Dict] = None
    ) -> Dict:
        """
        Create a paginated success response.

        Args:
            data: List of items for current page
            page: Current page number
            per_page: Items per page
            total: Total number of items
            meta: Optional metadata

        Returns:
            Standardized paginated response
        """
        total_pages = (total + per_page - 1) // per_page if per_page > 0 else 0

        response_meta = {
            "version": APIResponse.VERSION,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1,
            },
            **(meta or {}),
        }

        return APIResponse.success(data=data, meta=response_meta)


def timed_endpoint(f):
    """
    Decorator to add execution time to API responses.

    Usage:
        @app.route('/api/data')
        @timed_endpoint
        def get_data():
            return APIResponse.success(data={...})
    """

    @wraps(f)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = f(*args, **kwargs)
        execution_time = (time.time() - start_time) * 1000  # Convert to milliseconds

        # If result is a tuple (response, status_code), unpack it
        if isinstance(result, tuple):
            response, status_code = result
        else:
            response = result
            status_code = 200

        # Add execution time to meta
        if isinstance(response, dict) and "meta" in response:
            response["meta"]["execution_time_ms"] = round(execution_time, 2)

        # Return with status code if it was originally a tuple
        if isinstance(result, tuple):
            return response, status_code
        return response

    return wrapper


def handle_api_errors(f):
    """
    Decorator to catch and format exceptions as API errors.

    Usage:
        @app.route('/api/data')
        @handle_api_errors
        def get_data():
            # Any exception will be caught and returned as API error
            return APIResponse.success(data={...})
    """

    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValueError as e:
            return APIResponse.error(
                str(e), error_code="VALIDATION_ERROR", status_code=400
            )
        except PermissionError as e:
            return APIResponse.error(
                str(e), error_code="PERMISSION_DENIED", status_code=403
            )
        except FileNotFoundError as e:
            return APIResponse.error(str(e), error_code="NOT_FOUND", status_code=404)
        except Exception as e:
            # Log the full exception but return generic error
            import logging

            logging.error(f"API error in {f.__name__}: {e}", exc_info=True)
            return APIResponse.error(
                "Internal server error", error_code="INTERNAL_ERROR", status_code=500
            )

    return wrapper


# Convenience function
def create_response(
    success: bool = True,
    data: Any = None,
    error: Optional[str] = None,
    status_code: int = 200,
    **kwargs,
) -> tuple:
    """
    Create a standardized API response (legacy support).

    Args:
        success: Success status
        data: Response data
        error: Error message
        status_code: HTTP status code
        **kwargs: Additional fields

    Returns:
        Tuple of (response_dict, status_code)
    """
    if success:
        return APIResponse.success(data=data, **kwargs), status_code
    else:
        return APIResponse.error(
            error or "Unknown error", status_code=status_code, **kwargs
        )
