"""Custom application exceptions and centralized error models."""
from typing import Any, Optional


class AppException(Exception):
    """Base application exception."""
    def __init__(
        self,
        message: str,
        status_code: int = 400,
        error_code: str = "BAD_REQUEST",
        details: Optional[Any] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details
        super().__init__(message)


class NotFoundException(AppException):
    def __init__(self, resource: str, identifier: Any):
        super().__init__(
            message=f"{resource} with identifier '{identifier}' was not found.",
            status_code=404,
            error_code="NOT_FOUND",
        )


class ConflictException(AppException):
    def __init__(self, message: str):
        super().__init__(
            message=message,
            status_code=409,
            error_code="CONFLICT",
        )


class UnauthorizedException(AppException):
    def __init__(self, message: str = "Invalid authentication credentials"):
        super().__init__(
            message=message,
            status_code=401,
            error_code="UNAUTHORIZED",
        )


class DatabaseConnectionException(AppException):
    def __init__(self, message: str = "Database service is temporarily unavailable"):
        super().__init__(
            message=message,
            status_code=503,
            error_code="DATABASE_UNAVAILABLE",
        )
