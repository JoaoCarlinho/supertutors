"""Error handling utilities and standardized error responses.

This module provides utilities for creating consistent error responses
across the API and defining common error codes.
"""

from typing import Dict, Any, Optional, Tuple
from flask import jsonify, Response


# Error code constants
class ErrorCodes:
    """Standard error codes used across the application."""
    VALIDATION_ERROR = "VALIDATION_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    CACHE_ERROR = "CACHE_ERROR"
    LLM_TIMEOUT = "LLM_TIMEOUT"
    LLM_ERROR = "LLM_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    NOT_FOUND = "NOT_FOUND"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"


def create_error_response(
    message: str,
    code: str = ErrorCodes.INTERNAL_ERROR,
    status_code: int = 500,
    details: Optional[Dict[str, Any]] = None
) -> Tuple[Response, int]:
    """Create a standardized error response.

    Args:
        message: User-friendly error message
        code: Error code constant from ErrorCodes
        status_code: HTTP status code (default: 500)
        details: Optional technical details for debugging

    Returns:
        Tuple of (Flask Response object, status code)

    Example:
        >>> from app.utils.errors import create_error_response, ErrorCodes
        >>> return create_error_response(
        ...     "Invalid email format",
        ...     ErrorCodes.VALIDATION_ERROR,
        ...     400,
        ...     {"field": "email"}
        ... )
    """
    error_response: Dict[str, Any] = {
        "success": False,
        "error": {
            "message": message,
            "code": code
        }
    }

    if details:
        error_response["error"]["details"] = details

    return jsonify(error_response), status_code


class AppError(Exception):
    """Base application error with error code and status code.

    This exception can be raised anywhere in the application and
    will be caught by the global error handler to return a
    standardized error response.

    Attributes:
        message: User-friendly error message
        code: Error code from ErrorCodes
        status_code: HTTP status code
        details: Optional technical details
    """

    def __init__(
        self,
        message: str,
        code: str = ErrorCodes.INTERNAL_ERROR,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize AppError.

        Args:
            message: User-friendly error message
            code: Error code constant from ErrorCodes
            status_code: HTTP status code (default: 500)
            details: Optional technical details for debugging
        """
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details

    def to_response(self) -> Tuple[Response, int]:
        """Convert error to Flask response.

        Returns:
            Tuple of (Flask Response object, status code)
        """
        return create_error_response(
            self.message,
            self.code,
            self.status_code,
            self.details
        )


class ValidationError(AppError):
    """Error for invalid input data."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, ErrorCodes.VALIDATION_ERROR, 400, details)


class DatabaseError(AppError):
    """Error for database operations."""

    def __init__(self, message: str = "Database error occurred"):
        super().__init__(message, ErrorCodes.DATABASE_ERROR, 500)


class CacheError(AppError):
    """Error for Redis cache operations."""

    def __init__(self, message: str = "Cache error occurred"):
        super().__init__(message, ErrorCodes.CACHE_ERROR, 500)


class LLMTimeoutError(AppError):
    """Error when LLM request exceeds timeout."""

    def __init__(self, message: str = "AI service timed out. Please try again."):
        super().__init__(message, ErrorCodes.LLM_TIMEOUT, 504)


class LLMError(AppError):
    """Error when LLM service is unavailable."""

    def __init__(self, message: str = "AI service is currently unavailable. Please try again later."):
        super().__init__(message, ErrorCodes.LLM_ERROR, 503)


class NotFoundError(AppError):
    """Error for resource not found."""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, ErrorCodes.NOT_FOUND, 404)


class UnauthorizedError(AppError):
    """Error for unauthorized access."""

    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message, ErrorCodes.UNAUTHORIZED, 401)


class ForbiddenError(AppError):
    """Error for forbidden access."""

    def __init__(self, message: str = "Forbidden"):
        super().__init__(message, ErrorCodes.FORBIDDEN, 403)
