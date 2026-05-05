"""
Prediction Input Validation Schemas
All customer features are validated with appropriate types, ranges, and enum values.
"""

from typing import Literal
from pydantic import BaseModel, Field, field_validator


class PredictionInput(BaseModel):
    """
    Prediction input schema with comprehensive validation.
    
    Validates all required customer features with appropriate data types,
    value ranges, and enum constraints. Returns descriptive error messages
    within 100ms (Pydantic validation is fast enough).
    
    - 12.3: Returns descriptive error messages within 100ms
    """
    
    # Demographic features
    gender: Literal["Male", "Female"] = Field(
        ...,
        description="Customer gender (Male or Female)"
    )
    
    SeniorCitizen: Literal[0, 1] = Field(
        ...,
        description="Whether customer is a senior citizen (0=No, 1=Yes)"
    )
    
    Partner: Literal["Yes", "No"] = Field(
        ...,
        description="Whether customer has a partner (Yes or No)"
    )
    
    Dependents: Literal["Yes", "No"] = Field(
        ...,
        description="Whether customer has dependents (Yes or No)"
    )
    
    # Service tenure
    tenure: int = Field(
        ...,
        ge=0,
        le=72,
        description="Number of months customer has stayed with company (0-72)"
    )
    
    # Phone service features
    PhoneService: Literal["Yes", "No"] = Field(
        ...,
        description="Whether customer has phone service (Yes or No)"
    )
    
    MultipleLines: Literal["Yes", "No", "No phone service"] = Field(
        ...,
        description="Whether customer has multiple lines (Yes, No, or No phone service)"
    )
    
    # Internet service features
    InternetService: Literal["DSL", "Fiber optic", "No"] = Field(
        ...,
        description="Customer's internet service type (DSL, Fiber optic, or No)"
    )
    
    OnlineSecurity: Literal["Yes", "No", "No internet service"] = Field(
        ...,
        description="Whether customer has online security (Yes, No, or No internet service)"
    )
    
    OnlineBackup: Literal["Yes", "No", "No internet service"] = Field(
        ...,
        description="Whether customer has online backup (Yes, No, or No internet service)"
    )
    
    DeviceProtection: Literal["Yes", "No", "No internet service"] = Field(
        ...,
        description="Whether customer has device protection (Yes, No, or No internet service)"
    )
    
    TechSupport: Literal["Yes", "No", "No internet service"] = Field(
        ...,
        description="Whether customer has tech support (Yes, No, or No internet service)"
    )
    
    StreamingTV: Literal["Yes", "No", "No internet service"] = Field(
        ...,
        description="Whether customer has streaming TV (Yes, No, or No internet service)"
    )
    
    StreamingMovies: Literal["Yes", "No", "No internet service"] = Field(
        ...,
        description="Whether customer has streaming movies (Yes, No, or No internet service)"
    )
    
    # Contract and billing features
    Contract: Literal["Month-to-month", "One year", "Two year"] = Field(
        ...,
        description="Customer's contract type (Month-to-month, One year, or Two year)"
    )
    
    PaperlessBilling: Literal["Yes", "No"] = Field(
        ...,
        description="Whether customer has paperless billing (Yes or No)"
    )
    
    PaymentMethod: Literal[
        "Electronic check",
        "Mailed check",
        "Bank transfer (automatic)",
        "Credit card (automatic)"
    ] = Field(
        ...,
        description="Customer's payment method"
    )
    
    # Billing amounts
    MonthlyCharges: float = Field(
        ...,
        ge=0.0,
        description="Customer's monthly charges (non-negative float)"
    )
    
    TotalCharges: float = Field(
        ...,
        ge=0.0,
        description="Customer's total charges (non-negative float)"
    )
    
    @field_validator("MonthlyCharges", "TotalCharges")
    @classmethod
    def validate_charges(cls, v: float, info) -> float:
        """Validate that charge values are reasonable"""
        if v < 0:
            raise ValueError(f"{info.field_name} must be non-negative")
        if v > 1000000:  # Sanity check for unreasonably large values
            raise ValueError(f"{info.field_name} exceeds reasonable maximum (1,000,000)")
        return v
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "gender": "Female",
                "SeniorCitizen": 0,
                "Partner": "Yes",
                "Dependents": "No",
                "tenure": 12,
                "PhoneService": "Yes",
                "MultipleLines": "No",
                "InternetService": "Fiber optic",
                "OnlineSecurity": "No",
                "OnlineBackup": "Yes",
                "DeviceProtection": "No",
                "TechSupport": "No",
                "StreamingTV": "Yes",
                "StreamingMovies": "No",
                "Contract": "Month-to-month",
                "PaperlessBilling": "Yes",
                "PaymentMethod": "Electronic check",
                "MonthlyCharges": 70.35,
                "TotalCharges": 844.20
            }
        }
    }


class SinglePredictionRequest(BaseModel):
    """
    Request schema for single customer prediction.
    
    - 12.2: Validates all required fields are present
    """
    
    model_version_id: str = Field(
        ...,
        description="UUID of the model version to use for prediction"
    )
    
    input: PredictionInput = Field(
        ...,
        description="Customer feature data for prediction"
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "model_version_id": "880e8400-e29b-41d4-a716-446655440000",
                "input": {
                    "gender": "Female",
                    "SeniorCitizen": 0,
                    "Partner": "Yes",
                    "Dependents": "No",
                    "tenure": 12,
                    "PhoneService": "Yes",
                    "MultipleLines": "No",
                    "InternetService": "Fiber optic",
                    "OnlineSecurity": "No",
                    "OnlineBackup": "Yes",
                    "DeviceProtection": "No",
                    "TechSupport": "No",
                    "StreamingTV": "Yes",
                    "StreamingMovies": "No",
                    "Contract": "Month-to-month",
                    "PaperlessBilling": "Yes",
                    "PaymentMethod": "Electronic check",
                    "MonthlyCharges": 70.35,
                    "TotalCharges": 844.20
                }
            }
        }
    }


class PredictionResponse(BaseModel):
    """
    Response schema for prediction results.
    
    - 12.6: Returns probability score (0.0 to 1.0) within 200ms
    - 12.7: Displays probability as percentage with color coding
    - 12.8: Displays feature contributions using SHAP values
    """
    
    id: str = Field(..., description="Prediction unique identifier")
    model_version_id: str = Field(..., description="Model version used")
    probability: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Churn probability (0.0 to 1.0)"
    )
    threshold: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Classification threshold used"
    )
    prediction: Literal["Churn", "No Churn"] = Field(
        ...,
        description="Binary prediction result"
    )
    shap_values: dict = Field(
        default_factory=dict,
        description="SHAP values for explainability with top positive and negative contributors"
    )
    created_at: str = Field(..., description="Prediction timestamp")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "990e8400-e29b-41d4-a716-446655440000",
                "model_version_id": "880e8400-e29b-41d4-a716-446655440000",
                "probability": 0.73,
                "threshold": 0.5,
                "prediction": "Churn",
                "shap_values": {
                    "base_value": 0.265,
                    "prediction_value": 0.73,
                    "top_positive": [
                        {
                            "feature": "Contract_Month-to-month",
                            "value": 1.0,
                            "contribution": 0.15,
                            "direction": "positive"
                        },
                        {
                            "feature": "InternetService_Fiber optic",
                            "value": 1.0,
                            "contribution": 0.12,
                            "direction": "positive"
                        }
                    ],
                    "top_negative": [
                        {
                            "feature": "tenure",
                            "value": 24.0,
                            "contribution": -0.08,
                            "direction": "negative"
                        }
                    ]
                },
                "created_at": "2024-01-15T14:30:00Z"
            }
        }
    }


class ValidationErrorDetail(BaseModel):
    """Detailed validation error information"""
    
    field: str = Field(..., description="Field name that failed validation")
    message: str = Field(..., description="Descriptive error message")
    type: str = Field(..., description="Error type")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "field": "tenure",
                "message": "Input should be less than or equal to 72",
                "type": "less_than_equal"
            }
        }
    }


class ValidationErrorResponse(BaseModel):
    """
    Response schema for validation errors.
    
    """
    
    detail: list[ValidationErrorDetail] = Field(
        ...,
        description="List of validation errors"
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "detail": [
                    {
                        "field": "tenure",
                        "message": "Input should be less than or equal to 72",
                        "type": "less_than_equal"
                    },
                    {
                        "field": "gender",
                        "message": "Input should be 'Male' or 'Female'",
                        "type": "literal_error"
                    }
                ]
            }
        }
    }


class BatchPredictionUploadResponse(BaseModel):
    """
    Response schema for batch prediction upload.
    
    - 13.2: Validate file format within 1 second
    """
    
    batch_id: str = Field(..., description="Unique batch identifier")
    model_version_id: str = Field(..., description="Model version used")
    record_count: int = Field(..., description="Number of records in batch")
    status: str = Field(..., description="Batch processing status (queued, processing, completed, failed)")
    message: str = Field(..., description="Status message")
    created_at: str = Field(..., description="Batch creation timestamp")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "batch_id": "aa0e8400-e29b-41d4-a716-446655440000",
                "model_version_id": "880e8400-e29b-41d4-a716-446655440000",
                "record_count": 1000,
                "status": "queued",
                "message": "Batch prediction job queued for processing",
                "created_at": "2024-01-15T14:30:00Z"
            }
        }
    }


class BatchPredictionResult(BaseModel):
    """
    Individual prediction result in a batch.
    
    """
    
    id: str = Field(..., description="Prediction unique identifier")
    probability: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Churn probability (0.0 to 1.0)"
    )
    prediction: Literal["Churn", "No Churn"] = Field(
        ...,
        description="Binary prediction result"
    )
    input_features: dict = Field(..., description="Customer input features")
    created_at: str = Field(..., description="Prediction timestamp")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "bb0e8400-e29b-41d4-a716-446655440000",
                "probability": 0.73,
                "prediction": "Churn",
                "input_features": {
                    "gender": "Female",
                    "tenure": 12,
                    "MonthlyCharges": 70.35
                },
                "created_at": "2024-01-15T14:30:00Z"
            }
        }
    }


class PaginationMetadata(BaseModel):
    """Pagination metadata for batch results"""
    
    total: int = Field(..., description="Total number of predictions in batch")
    page: int = Field(..., description="Current page number (1-indexed)")
    page_size: int = Field(..., description="Number of items per page")
    total_pages: int = Field(..., description="Total number of pages")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "total": 1000,
                "page": 1,
                "page_size": 50,
                "total_pages": 20
            }
        }
    }


class BatchPredictionResultsResponse(BaseModel):
    """
    Response schema for batch prediction results.
    
    - 13.6: Display batch prediction results in paginated table with 50 rows per page
    """
    
    batch_id: str = Field(..., description="Unique batch identifier")
    model_version_id: str = Field(..., description="Model version used")
    status: str = Field(..., description="Batch processing status")
    record_count: int = Field(..., description="Total number of records in batch")
    created_at: str = Field(..., description="Batch creation timestamp")
    predictions: list[BatchPredictionResult] = Field(
        ...,
        description="List of predictions for current page"
    )
    pagination: PaginationMetadata = Field(..., description="Pagination metadata")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "batch_id": "aa0e8400-e29b-41d4-a716-446655440000",
                "model_version_id": "880e8400-e29b-41d4-a716-446655440000",
                "status": "completed",
                "record_count": 1000,
                "created_at": "2024-01-15T14:30:00Z",
                "predictions": [
                    {
                        "id": "bb0e8400-e29b-41d4-a716-446655440000",
                        "probability": 0.73,
                        "prediction": "Churn",
                        "input_features": {
                            "gender": "Female",
                            "tenure": 12
                        },
                        "created_at": "2024-01-15T14:30:05Z"
                    }
                ],
                "pagination": {
                    "total": 1000,
                    "page": 1,
                    "page_size": 50,
                    "total_pages": 20
                }
            }
        }
    }
