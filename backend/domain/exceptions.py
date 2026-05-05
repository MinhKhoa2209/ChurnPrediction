"""
Custom Exception Classes
These exceptions are caught by the global exception handlers and converted to structured error responses.
"""

from typing import Any, Dict, Optional


class ApplicationError(Exception):
    """
    Base exception class for all application-specific errors
    
    Attributes:
        message: Human-readable error message
        code: Machine-readable error code
        details: Optional additional error details
    """
    
    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code or "APPLICATION_ERROR"
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(ApplicationError):
    """
    Raised when input validation fails
    Requirement 20.3: Structured validation errors
    """
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="VALIDATION_ERROR", details=details)


class AuthenticationError(ApplicationError):
    """
    Raised when authentication fails
    Requirement 20.3: Authentication error handling
    """
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, code="AUTHENTICATION_ERROR")


class AuthorizationError(ApplicationError):
    """
    Raised when user lacks required permissions
    Requirement 20.3: Authorization error handling
    """
    
    def __init__(self, message: str = "Access denied"):
        super().__init__(message, code="AUTHORIZATION_ERROR")


class NotFoundError(ApplicationError):
    """
    Raised when a requested resource is not found
    Requirement 20.3: Not found error handling
    """
    
    def __init__(self, message: str, resource_type: Optional[str] = None):
        details = {"resource_type": resource_type} if resource_type else {}
        super().__init__(message, code="NOT_FOUND", details=details)


class ConflictError(ApplicationError):
    """
    Raised when a resource conflict occurs (e.g., duplicate entries)
    Requirement 20.3: Conflict error handling
    """
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="CONFLICT", details=details)


class DatabaseError(ApplicationError):
    """
    Raised when a database operation fails
    Requirement 20.1: Database error logging with full context
    """
    
    def __init__(self, message: str = "Database operation failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="DATABASE_ERROR", details=details)


class StorageError(ApplicationError):
    """
    Raised when a storage operation fails (e.g., R2/S3 operations)
    Requirement 20.1: Storage error handling
    """
    
    def __init__(self, message: str = "Storage operation failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="STORAGE_ERROR", details=details)


class MLServiceError(ApplicationError):
    """
    Raised when an ML service operation fails
    Requirement 20.1: ML service error handling
    """
    
    def __init__(self, message: str = "ML service operation failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="ML_SERVICE_ERROR", details=details)


class RateLimitError(ApplicationError):
    """
    Raised when rate limit is exceeded
    Requirement 23.5: Rate limiting error handling
    """
    
    def __init__(self, message: str = "Rate limit exceeded", retry_after: int = 60):
        super().__init__(
            message,
            code="RATE_LIMIT_EXCEEDED",
            details={"retry_after": retry_after}
        )


class ServiceUnavailableError(ApplicationError):
    """
    Raised when a service is temporarily unavailable
    Requirement 30.2: Service unavailability handling
    """
    
    def __init__(self, message: str = "Service temporarily unavailable", retry_after: Optional[int] = None):
        details = {"retry_after": retry_after} if retry_after else {}
        super().__init__(message, code="SERVICE_UNAVAILABLE", details=details)
