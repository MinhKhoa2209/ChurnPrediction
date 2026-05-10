from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class DatasetUploadResponse(BaseModel):
    id: UUID = Field(..., description="Dataset unique identifier")
    filename: str = Field(..., description="Original filename")
    status: str = Field(..., description="Processing status: processing, ready, failed")
    message: str = Field(..., description="Status message")
    uploaded_at: datetime = Field(..., description="Upload timestamp")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "filename": "telco_churn.csv",
                "status": "processing",
                "message": "Dataset upload accepted for processing",
                "uploaded_at": "2024-01-15T10:30:00Z",
            }
        },
    }


class DatasetResponse(BaseModel):
    id: UUID
    user_id: UUID
    filename: str
    record_count: int
    status: str
    validation_errors: Optional[dict] = None
    data_quality_score: Optional[float] = None
    uploaded_at: datetime
    processed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class DatasetListResponse(BaseModel):
    datasets: list[DatasetResponse]
    total: int

    model_config = {"from_attributes": True}
