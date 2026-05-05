"""
Global Exception Handlers for FastAPI
Centralized error handling for the Customer Churn Prediction Platform

import logging
from typing import Union

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.domain.schemas.errors import (
    ErrorCode,
    ErrorDetail,
    create_error_response,
    create_validation_error_details,
)
from backend.domain.exceptions import (
    ApplicationError,
    AuthenticationError as CustomAuthenticationError,
    AuthorizationError as CustomAuthorizationError,
    NotFoundError,
    ConflictError,
    DatabaseError,
    StorageError,
    MLServiceError,
    RateLimitError,
    ServiceUnavailableError,
)

logger = logging.getLogger(__name__)


async def validation_exception_handler(
    request: Request,
    exc: Union[RequestValidationError, ValidationError]
) -> JSONResponse:
    """
    Handle Pydantic validation errors
    Requirement 20.3: Return structured error responses with VALIDATION_ERROR code
    
    Args:
        request: FastAPI request object
        exc: Validation error exception
        
    Returns:
        JSONResponse with structured error format
    """
    request_id = getattr(request.state, "request_id", None)
    
    # Convert Pydantic errors to our ErrorDetail format
    details = create_validation_error_details(exc.errors())
    
    # Log the validation error
    logger.warning(
        f"Validation error for request {request_id}: {exc.errors()}",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
        }
    )
    
    error_response = create_error_response(
        code=ErrorCode.VALIDATION_ERROR,
        message="Invalid input data",
        details=details,
        request_id=request_id,
    )
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=error_response,
    )


async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException
) -> JSONResponse:
    """
    Handle HTTP exceptions (401, 403, 404, etc.)
    Requirement 20.3: Return structured error responses with appropriate error codes
    
    Args:
        request: FastAPI request object
        exc: HTTP exception
        
    Returns:
        JSONResponse with structured error format
    """
    request_id = getattr(request.state, "request_id", None)
    
    # Map HTTP status codes to error codes
    status_to_error_code = {
        status.HTTP_400_BAD_REQUEST: ErrorCode.VALIDATION_ERROR,
        status.HTTP_401_UNAUTHORIZED: ErrorCode.AUTHENTICATION_ERROR,
        status.HTTP_403_FORBIDDEN: ErrorCode.AUTHORIZATION_ERROR,
        status.HTTP_404_NOT_FOUND: ErrorCode.NOT_FOUND,
        status.HTTP_409_CONFLICT: ErrorCode.CONFLICT,
        status.HTTP_422_UNPROCESSABLE_ENTITY: ErrorCode.UNPROCESSABLE_ENTITY,
        status.HTTP_429_TOO_MANY_REQUESTS: ErrorCode.RATE_LIMIT_EXCEEDED,
        status.HTTP_503_SERVICE_UNAVAILABLE: ErrorCode.SERVICE_UNAVAILABLE,
    }
    
    error_code = status_to_error_code.get(
        exc.status_code,
        ErrorCode.INTERNAL_ERROR
    )
    
    # Log the HTTP exception
    log_level = logging.WARNING if exc.status_code < 500 else logging.ERROR
    logger.log(
        log_level,
        f"HTTP {exc.status_code} error for request {request_id}: {exc.detail}",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
            "status_code": exc.status_code,
        }
    )
    
    error_response = create_error_response(
        code=error_code,
        message=str(exc.detail),
        request_id=request_id,
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response,
    )


async def database_exception_handler(
    request: Request,
    exc: SQLAlchemyError
) -> JSONResponse:
    """
    Handle database errors
    Requirement 20.1: Log errors with timestamp, user ID, request ID, and stack trace
    
    Args:
        request: FastAPI request object
        exc: SQLAlchemy exception
        
    Returns:
        JSONResponse with structured error format
    """
    request_id = getattr(request.state, "request_id", None)
    user_id = getattr(request.state, "user_id", None)
    
    # Log the database error with full context
    logger.error(
        f"Database error for request {request_id}: {str(exc)}",
        exc_info=True,
        extra={
            "request_id": request_id,
            "user_id": user_id,
            "path": request.url.path,
            "method": request.method,
        }
    )
    
    error_response = create_error_response(
        code=ErrorCode.DATABASE_ERROR,
        message="A database error occurred. Please try again later.",
        request_id=request_id,
    )
    
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content=error_response,
    )


async def generic_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """
    Handle all other unhandled exceptions
    Requirement 20.1: Log errors with timestamp, user ID, request ID, and stack trace
    
    Args:
        request: FastAPI request object
        exc: Generic exception
        
    Returns:
        JSONResponse with structured error format
    """
    request_id = getattr(request.state, "request_id", None)
    user_id = getattr(request.state, "user_id", None)
    
    # Handle ExceptionGroup (Python 3.11+) by extracting the first exception
    actual_exc = exc
    if hasattr(exc, 'exceptions') and exc.exceptions:
        actual_exc = exc.exceptions[0]
    
    # Log the unexpected error with full context
    logger.error(
        f"Unexpected error for request {request_id}: {str(actual_exc)}",
        exc_info=actual_exc,
        extra={
            "request_id": request_id,
            "user_id": user_id,
            "path": request.url.path,
            "method": request.method,
            "exception_type": type(actual_exc).__name__,
        }
    )
    
    # Don't expose internal error details to clients
    error_response = create_error_response(
        code=ErrorCode.INTERNAL_ERROR,
        message="An internal server error occurred. Please try again later.",
        request_id=request_id,
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response,
    )


async def custom_authentication_error_handler(
    request: Request,
    exc: CustomAuthenticationError
) -> JSONResponse:
    """
    Handle custom authentication errors
    Requirement 20.1: Log authentication errors with context
    
    Args:
        request: FastAPI request object
        exc: Custom authentication error
        
    Returns:
        JSONResponse with structured error format
    """
    request_id = getattr(request.state, "request_id", None)
    user_id = getattr(request.state, "user_id", None)
    
    logger.warning(
        f"Authentication error for request {request_id}: {exc.message}",
        extra={
            "request_id": request_id,
            "user_id": user_id,
            "path": request.url.path,
            "method": request.method,
        }
    )
    
    error_response = create_error_response(
        code=ErrorCode.AUTHENTICATION_ERROR,
        message=exc.message,
        request_id=request_id,
    )
    
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content=error_response,
        headers={"WWW-Authenticate": "Bearer"},
    )


async def custom_authorization_error_handler(
    request: Request,
    exc: CustomAuthorizationError
) -> JSONResponse:
    """
    Handle custom authorization errors
    Requirement 20.1: Log authorization errors with context
    
    Args:
        request: FastAPI request object
        exc: Custom authorization error
        
    Returns:
        JSONResponse with structured error format
    """
    request_id = getattr(request.state, "request_id", None)
    user_id = getattr(request.state, "user_id", None)
    
    logger.warning(
        f"Authorization error for request {request_id}: {exc.message}",
        extra={
            "request_id": request_id,
            "user_id": user_id,
            "path": request.url.path,
            "method": request.method,
        }
    )
    
    error_response = create_error_response(
        code=ErrorCode.AUTHORIZATION_ERROR,
        message=exc.message,
        request_id=request_id,
    )
    
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content=error_response,
    )


async def not_found_error_handler(
    request: Request,
    exc: NotFoundError
) -> JSONResponse:
    """
    Handle not found errors
    Requirement 20.1: Log not found errors with context
    
    Args:
        request: FastAPI request object
        exc: Not found error
        
    Returns:
        JSONResponse with structured error format
    """
    request_id = getattr(request.state, "request_id", None)
    user_id = getattr(request.state, "user_id", None)
    
    logger.info(
        f"Resource not found for request {request_id}: {exc.message}",
        extra={
            "request_id": request_id,
            "user_id": user_id,
            "path": request.url.path,
            "method": request.method,
            "resource_type": exc.details.get("resource_type"),
        }
    )
    
    error_response = create_error_response(
        code=ErrorCode.NOT_FOUND,
        message=exc.message,
        request_id=request_id,
    )
    
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=error_response,
    )


async def conflict_error_handler(
    request: Request,
    exc: ConflictError
) -> JSONResponse:
    """
    Handle conflict errors
    Requirement 20.1: Log conflict errors with context
    
    Args:
        request: FastAPI request object
        exc: Conflict error
        
    Returns:
        JSONResponse with structured error format
    """
    request_id = getattr(request.state, "request_id", None)
    user_id = getattr(request.state, "user_id", None)
    
    logger.warning(
        f"Conflict error for request {request_id}: {exc.message}",
        extra={
            "request_id": request_id,
            "user_id": user_id,
            "path": request.url.path,
            "method": request.method,
            "details": exc.details,
        }
    )
    
    # Convert details to ErrorDetail list if present
    details = None
    if exc.details:
        details = [
            ErrorDetail(
                field=None,
                message=f"{key}: {value}",
                code="conflict"
            )
            for key, value in exc.details.items()
        ]
    
    error_response = create_error_response(
        code=ErrorCode.CONFLICT,
        message=exc.message,
        details=details,
        request_id=request_id,
    )
    
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content=error_response,
    )


async def storage_error_handler(
    request: Request,
    exc: StorageError
) -> JSONResponse:
    """
    Handle storage errors (R2/S3 operations)
    Requirement 20.1: Log storage errors with full context
    
    Args:
        request: FastAPI request object
        exc: Storage error
        
    Returns:
        JSONResponse with structured error format
    """
    request_id = getattr(request.state, "request_id", None)
    user_id = getattr(request.state, "user_id", None)
    
    logger.error(
        f"Storage error for request {request_id}: {exc.message}",
        exc_info=True,
        extra={
            "request_id": request_id,
            "user_id": user_id,
            "path": request.url.path,
            "method": request.method,
            "details": exc.details,
        }
    )
    
    error_response = create_error_response(
        code=ErrorCode.STORAGE_ERROR,
        message="A storage error occurred. Please try again later.",
        request_id=request_id,
    )
    
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content=error_response,
    )


async def ml_service_error_handler(
    request: Request,
    exc: MLServiceError
) -> JSONResponse:
    """
    Handle ML service errors
    Requirement 20.1: Log ML service errors with full context
    
    Args:
        request: FastAPI request object
        exc: ML service error
        
    Returns:
        JSONResponse with structured error format
    """
    request_id = getattr(request.state, "request_id", None)
    user_id = getattr(request.state, "user_id", None)
    
    logger.error(
        f"ML service error for request {request_id}: {exc.message}",
        exc_info=True,
        extra={
            "request_id": request_id,
            "user_id": user_id,
            "path": request.url.path,
            "method": request.method,
            "details": exc.details,
        }
    )
    
    error_response = create_error_response(
        code=ErrorCode.ML_SERVICE_ERROR,
        message="An ML service error occurred. Please try again later.",
        request_id=request_id,
    )
    
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content=error_response,
    )


async def rate_limit_error_handler(
    request: Request,
    exc: RateLimitError
) -> JSONResponse:
    """
    Handle rate limit errors
    Requirement 23.5: Rate limiting error handling
    
    Args:
        request: FastAPI request object
        exc: Rate limit error
        
    Returns:
        JSONResponse with structured error format
    """
    request_id = getattr(request.state, "request_id", None)
    user_id = getattr(request.state, "user_id", None)
    
    logger.warning(
        f"Rate limit exceeded for request {request_id}",
        extra={
            "request_id": request_id,
            "user_id": user_id,
            "path": request.url.path,
            "method": request.method,
        }
    )
    
    retry_after = exc.details.get("retry_after", 60)
    
    error_response = create_error_response(
        code=ErrorCode.RATE_LIMIT_EXCEEDED,
        message=exc.message,
        request_id=request_id,
    )
    
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content=error_response,
        headers={"Retry-After": str(retry_after)},
    )


async def service_unavailable_error_handler(
    request: Request,
    exc: ServiceUnavailableError
) -> JSONResponse:
    """
    Handle service unavailable errors
    Requirement 30.2: Service unavailability handling
    
    Args:
        request: FastAPI request object
        exc: Service unavailable error
        
    Returns:
        JSONResponse with structured error format
    """
    request_id = getattr(request.state, "request_id", None)
    user_id = getattr(request.state, "user_id", None)
    
    logger.error(
        f"Service unavailable for request {request_id}: {exc.message}",
        extra={
            "request_id": request_id,
            "user_id": user_id,
            "path": request.url.path,
            "method": request.method,
        }
    )
    
    retry_after = exc.details.get("retry_after")
    headers = {"Retry-After": str(retry_after)} if retry_after else {}
    
    error_response = create_error_response(
        code=ErrorCode.SERVICE_UNAVAILABLE,
        message=exc.message,
        request_id=request_id,
    )
    
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content=error_response,
        headers=headers,
    )


async def application_error_handler(
    request: Request,
    exc: ApplicationError
) -> JSONResponse:
    """
    Handle generic application errors
    Requirement 20.1: Log application errors with full context
    
    Args:
        request: FastAPI request object
        exc: Application error
        
    Returns:
        JSONResponse with structured error format
    """
    request_id = getattr(request.state, "request_id", None)
    user_id = getattr(request.state, "user_id", None)
    
    logger.error(
        f"Application error for request {request_id}: {exc.message}",
        exc_info=True,
        extra={
            "request_id": request_id,
            "user_id": user_id,
            "path": request.url.path,
            "method": request.method,
            "error_code": exc.code,
            "details": exc.details,
        }
    )
    
    error_response = create_error_response(
        code=ErrorCode.INTERNAL_ERROR,
        message=exc.message,
        request_id=request_id,
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response,
    )


def register_exception_handlers(app) -> None:
    """
    Register all exception handlers with the FastAPI application
    1. Custom application exceptions (most specific)
    2. Framework exceptions (Pydantic, HTTP, SQLAlchemy)
    3. Generic exception handler (catch-all)
    
    Args:
        app: FastAPI application instance
    """
    # Custom application exceptions
    app.add_exception_handler(CustomAuthenticationError, custom_authentication_error_handler)
    app.add_exception_handler(CustomAuthorizationError, custom_authorization_error_handler)
    app.add_exception_handler(NotFoundError, not_found_error_handler)
    app.add_exception_handler(ConflictError, conflict_error_handler)
    app.add_exception_handler(DatabaseError, database_exception_handler)
    app.add_exception_handler(StorageError, storage_error_handler)
    app.add_exception_handler(MLServiceError, ml_service_error_handler)
    app.add_exception_handler(RateLimitError, rate_limit_error_handler)
    app.add_exception_handler(ServiceUnavailableError, service_unavailable_error_handler)
    app.add_exception_handler(ApplicationError, application_error_handler)
    
    # Framework exceptions
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ValidationError, validation_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(SQLAlchemyError, database_exception_handler)
    
    # Catch-all for unexpected exceptions
    app.add_exception_handler(Exception, generic_exception_handler)
