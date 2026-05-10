from typing import Any, Dict

ERROR_RESPONSES: Dict[int, Dict[str, Any]] = {
    400: {
        "description": "Bad Request - Invalid request data or parameters",
        "content": {
            "application/json": {
                "example": {
                    "error": "VALIDATION_ERROR",
                    "message": "Invalid request parameters",
                    "details": {"field": "email", "issue": "Invalid email format"},
                    "requestId": "req_abc123xyz",
                    "timestamp": "2024-01-15T10:30:00Z",
                }
            }
        },
    },
    401: {
        "description": "Unauthorized - Missing or invalid authentication token",
        "content": {
            "application/json": {
                "example": {
                    "error": "UNAUTHORIZED",
                    "message": "Authentication required",
                    "details": "Missing or invalid access token",
                    "requestId": "req_abc123xyz",
                    "timestamp": "2024-01-15T10:30:00Z",
                }
            }
        },
    },
    403: {
        "description": "Forbidden - Insufficient permissions for the requested resource",
        "content": {
            "application/json": {
                "example": {
                    "error": "FORBIDDEN",
                    "message": "Access denied",
                    "details": "User does not have permission to access this resource. Required role: Admin",
                    "requestId": "req_abc123xyz",
                    "timestamp": "2024-01-15T10:30:00Z",
                }
            }
        },
    },
    404: {
        "description": "Not Found - Resource not found",
        "content": {
            "application/json": {
                "example": {
                    "error": "NOT_FOUND",
                    "message": "Resource not found",
                    "details": "Dataset with ID 'dataset_123' does not exist or you do not have access",
                    "requestId": "req_abc123xyz",
                    "timestamp": "2024-01-15T10:30:00Z",
                }
            }
        },
    },
    422: {
        "description": "Unprocessable Entity - Validation error in request body",
        "content": {
            "application/json": {
                "example": {
                    "error": "VALIDATION_ERROR",
                    "message": "Request validation failed",
                    "details": [
                        {
                            "loc": ["body", "email"],
                            "msg": "field required",
                            "type": "value_error.missing",
                        },
                        {
                            "loc": ["body", "password"],
                            "msg": "ensure this value has at least 8 characters",
                            "type": "value_error.any_str.min_length",
                        },
                    ],
                    "requestId": "req_abc123xyz",
                    "timestamp": "2024-01-15T10:30:00Z",
                }
            }
        },
    },
    503: {
        "description": "Service Unavailable - Service temporarily unavailable (degraded mode)",
        "content": {
            "application/json": {
                "example": {
                    "error": "SERVICE_UNAVAILABLE",
                    "message": "Service temporarily unavailable",
                    "details": "Database connection failed. Please try again later.",
                    "requestId": "req_abc123xyz",
                    "timestamp": "2024-01-15T10:30:00Z",
                }
            }
        },
        "headers": {
            "Retry-After": {
                "description": "Number of seconds to wait before retrying",
                "schema": {"type": "integer", "example": 60},
            }
        },
    },
}


def get_common_responses(*status_codes: int) -> Dict[int, Dict[str, Any]]:
    return {code: ERROR_RESPONSES[code] for code in status_codes if code in ERROR_RESPONSES}


def get_all_error_responses() -> Dict[int, Dict[str, Any]]:
    return ERROR_RESPONSES.copy()
