"""Pydantic schemas package"""

from backend.domain.schemas.auth import (
    AuthResponse,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from backend.domain.schemas.dataset import (
    DatasetUploadResponse,
    DatasetResponse,
    DatasetListResponse,
)
from backend.domain.schemas.training import (
    TrainingJobCreate,
    TrainingJobCreateResponse,
    TrainingJobListResponse,
    TrainingJobResponse,
)
from backend.domain.schemas.prediction import (
    PredictionInput,
    SinglePredictionRequest,
    PredictionResponse,
    ValidationErrorDetail,
    ValidationErrorResponse,
)
from backend.domain.schemas.errors import (
    ErrorCode,
    ErrorDetail,
    ErrorInfo,
    ErrorResponse,
    create_error_response,
    create_validation_error_details,
)

__all__ = [
    "AuthResponse",
    "LoginRequest",
    "RegisterRequest",
    "TokenResponse",
    "UserResponse",
    "DatasetUploadResponse",
    "DatasetResponse",
    "DatasetListResponse",
    "TrainingJobCreate",
    "TrainingJobCreateResponse",
    "TrainingJobListResponse",
    "TrainingJobResponse",
    "PredictionInput",
    "SinglePredictionRequest",
    "PredictionResponse",
    "ValidationErrorDetail",
    "ValidationErrorResponse",
    "ErrorCode",
    "ErrorDetail",
    "ErrorInfo",
    "ErrorResponse",
    "create_error_response",
    "create_validation_error_details",
]
