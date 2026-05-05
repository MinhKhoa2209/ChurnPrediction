"""
Error Response Schemas and Error Codes
Structured error handling for the Customer Churn Prediction Platform

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ErrorCode(str, Enum):
    """
    Standard error codes for the platform
    Requirement 20.3: Structured error responses with error codes
    """
    
    # Client errors (4xx)
    VALIDATION_ERROR = "VALIDATION_ERROR"
    AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR"
    AUTHORIZATION_ERROR = "AUTHORIZATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    CONFLICT = "CONFLICT"
    UNPROCESSABLE_ENTITY = "UNPROCESSABLE_ENTITY"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    
    # Server errors (5xx)
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    DATABASE_ERROR = "DATABASE_ERROR"
    STORAGE_ERROR = "STORAGE_ERROR"
    ML_SERVICE_ERROR = "ML_SERVICE_ERROR"


class ErrorDetail(BaseModel):
    """
    Detailed error information for specific fields or issues
    Used in validation errors to provide field-level feedback
    """
    
    field: Optional[str] = Field(
        None,
        description="Field name that caused the error (for validation errors)"
    )
    message: str = Field(
        ...,
        description="Detailed error message"
    )
    code: Optional[str] = Field(
        None,
        description="Specific error code for this detail"
    )


class ErrorResponse(BaseModel):
    """
    Standard error response format for all API errors
    - code: Machine-readable error code
    - message: Human-readable error message
    - details: Optional list of detailed error information
    - requestId: Request ID for tracing and debugging
    - timestamp: ISO 8601 timestamp when the error occurred
    """
    
    error: "ErrorInfo" = Field(
        ...,
        description="Error information"
    )


class ErrorInfo(BaseModel):
    """
    Error information structure
    """
    
    code: ErrorCode = Field(
        ...,
        description="Machine-readable error code"
    )
    message: str = Field(
        ...,
        description="Human-readable error message"
    )
    details: Optional[List[ErrorDetail]] = Field(
        None,
        description="Detailed error information (e.g., validation errors)"
    )
    requestId: Optional[str] = Field(
        None,
        description="Request ID for tracking and debugging",
        alias="requestId"
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat() + "Z",
        description="ISO 8601 timestamp when the error occurred"
    )
    
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid input data",
                "details": [
                    {
                        "field": "tenure",
                        "message": "Must be a non-negative integer"
                    }
                ],
                "requestId": "req_abc123",
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }


# Update ErrorResponse to use ErrorInfo
ErrorResponse.model_rebuild()


def create_error_response(
    code: ErrorCode,
    message: str,
    details: Optional[List[ErrorDetail]] = None,
    request_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Helper function to create a standardized error response
    
    Args:
        code: Error code from ErrorCode enum
        message: Human-readable error message
        details: Optional list of detailed error information
        request_id: Optional request ID for tracking
        
    Returns:
        Dictionary representing the error response
    """
    error_info = ErrorInfo(
        code=code,
        message=message,
        details=details,
        requestId=request_id,
    )
    
    return {"error": error_info.model_dump(by_alias=True)}


def create_validation_error_details(
    validation_errors: List[Dict[str, Any]]
) -> List[ErrorDetail]:
    """
    Convert Pydantic validation errors to ErrorDetail objects
    
    Args:
        validation_errors: List of validation errors from Pydantic
        
    Returns:
        List of ErrorDetail objects
    """
    details = []
    for error in validation_errors:
        field = ".".join(str(loc) for loc in error.get("loc", []))
        message = error.get("msg", "Validation error")
        error_type = error.get("type", "")
        
        details.append(
            ErrorDetail(
                field=field if field else None,
                message=message,
                code=error_type
            )
        )
    
    return details
