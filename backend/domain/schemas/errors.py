from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ErrorCode(str, Enum):
    VALIDATION_ERROR = "VALIDATION_ERROR"
    AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR"
    AUTHORIZATION_ERROR = "AUTHORIZATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    CONFLICT = "CONFLICT"
    UNPROCESSABLE_ENTITY = "UNPROCESSABLE_ENTITY"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"

    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    DATABASE_ERROR = "DATABASE_ERROR"
    STORAGE_ERROR = "STORAGE_ERROR"
    ML_SERVICE_ERROR = "ML_SERVICE_ERROR"


class ErrorDetail(BaseModel):
    field: Optional[str] = Field(
        None, description="Field name that caused the error (for validation errors)"
    )
    message: str = Field(..., description="Detailed error message")
    code: Optional[str] = Field(None, description="Specific error code for this detail")


class ErrorResponse(BaseModel):
    error: "ErrorInfo" = Field(..., description="Error information")


class ErrorInfo(BaseModel):
    code: ErrorCode = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[List[ErrorDetail]] = Field(
        None, description="Detailed error information (e.g., validation errors)"
    )
    requestId: Optional[str] = Field(
        None, description="Request ID for tracking and debugging", alias="requestId"
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat() + "Z",
        description="ISO 8601 timestamp when the error occurred",
    )

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid input data",
                "details": [{"field": "tenure", "message": "Must be a non-negative integer"}],
                "requestId": "req_abc123",
                "timestamp": "2024-01-15T10:30:00Z",
            }
        }


ErrorResponse.model_rebuild()


def create_error_response(
    code: ErrorCode,
    message: str,
    details: Optional[List[ErrorDetail]] = None,
    request_id: Optional[str] = None,
) -> Dict[str, Any]:
    error_info = ErrorInfo(
        code=code,
        message=message,
        details=details,
        requestId=request_id,
    )

    return {"error": error_info.model_dump(by_alias=True)}


def create_validation_error_details(validation_errors: List[Dict[str, Any]]) -> List[ErrorDetail]:
    details = []
    for error in validation_errors:
        field = ".".join(str(loc) for loc in error.get("loc", []))
        message = error.get("msg", "Validation error")
        error_type = error.get("type", "")

        details.append(
            ErrorDetail(field=field if field else None, message=message, code=error_type)
        )

    return details
