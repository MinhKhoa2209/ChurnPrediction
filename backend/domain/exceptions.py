from typing import Any, Dict, Optional


class ApplicationError(Exception):
    def __init__(
        self, message: str, code: Optional[str] = None, details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code or "APPLICATION_ERROR"
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(ApplicationError):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="VALIDATION_ERROR", details=details)


class AuthenticationError(ApplicationError):
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, code="AUTHENTICATION_ERROR")


class AuthorizationError(ApplicationError):
    def __init__(self, message: str = "Access denied"):
        super().__init__(message, code="AUTHORIZATION_ERROR")


class NotFoundError(ApplicationError):
    def __init__(self, message: str, resource_type: Optional[str] = None):
        details = {"resource_type": resource_type} if resource_type else {}
        super().__init__(message, code="NOT_FOUND", details=details)


class ConflictError(ApplicationError):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="CONFLICT", details=details)


class DatabaseError(ApplicationError):
    def __init__(
        self, message: str = "Database operation failed", details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, code="DATABASE_ERROR", details=details)


class StorageError(ApplicationError):
    def __init__(
        self, message: str = "Storage operation failed", details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, code="STORAGE_ERROR", details=details)


class MLServiceError(ApplicationError):
    def __init__(
        self, message: str = "ML service operation failed", details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, code="ML_SERVICE_ERROR", details=details)


class RateLimitError(ApplicationError):
    def __init__(self, message: str = "Rate limit exceeded", retry_after: int = 60):
        super().__init__(message, code="RATE_LIMIT_EXCEEDED", details={"retry_after": retry_after})


class ServiceUnavailableError(ApplicationError):
    def __init__(
        self, message: str = "Service temporarily unavailable", retry_after: Optional[int] = None
    ):
        details = {"retry_after": retry_after} if retry_after else {}
        super().__init__(message, code="SERVICE_UNAVAILABLE", details=details)
