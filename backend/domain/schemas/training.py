"""
Training Job Pydantic Schemas
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class TrainingJobCreate(BaseModel):
    """Request schema for creating training job(s)"""
    
    dataset_id: UUID = Field(..., description="Dataset UUID to train on")
    model_types: list[str] = Field(
        ..., 
        description="List of model types to train (KNN, NaiveBayes, DecisionTree, SVM)",
        min_length=1
    )
    hyperparameters: Optional[dict] = Field(
        None,
        description="Optional hyperparameters for training (if not provided, will use optimization)"
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "dataset_id": "550e8400-e29b-41d4-a716-446655440000",
                "model_types": ["KNN", "DecisionTree", "SVM"],
                "hyperparameters": None
            }
        }
    }


class TrainingJobResponse(BaseModel):
    """Response schema for training job details"""
    
    id: UUID = Field(..., description="Training job unique identifier")
    user_id: UUID = Field(..., description="User who created the job")
    dataset_id: UUID = Field(..., description="Dataset being used for training")
    model_version_id: Optional[UUID] = Field(None, description="Model version ID (set when completed)")
    model_type: str = Field(..., description="Model type (KNN, NaiveBayes, DecisionTree, SVM)")
    status: str = Field(..., description="Job status (queued, running, completed, failed)")
    progress_percent: int = Field(..., description="Progress percentage (0-100)")
    current_iteration: Optional[int] = Field(None, description="Current training iteration")
    total_iterations: Optional[int] = Field(None, description="Total training iterations")
    estimated_seconds_remaining: Optional[int] = Field(None, description="Estimated seconds remaining")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    created_at: datetime = Field(..., description="Job creation timestamp")
    started_at: Optional[datetime] = Field(None, description="Job start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Job completion timestamp")
    
    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "660e8400-e29b-41d4-a716-446655440000",
                "user_id": "770e8400-e29b-41d4-a716-446655440000",
                "dataset_id": "550e8400-e29b-41d4-a716-446655440000",
                "model_version_id": None,
                "model_type": "KNN",
                "status": "running",
                "progress_percent": 45,
                "current_iteration": 23,
                "total_iterations": 50,
                "estimated_seconds_remaining": 15,
                "error_message": None,
                "created_at": "2024-01-15T10:30:00Z",
                "started_at": "2024-01-15T10:30:05Z",
                "completed_at": None
            }
        }
    }


class TrainingJobListResponse(BaseModel):
    """Response schema for training job list"""
    
    jobs: list[TrainingJobResponse] = Field(..., description="List of training jobs")
    total: int = Field(..., description="Total number of jobs")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "jobs": [],
                "total": 0
            }
        }
    }


class TrainingJobCreateResponse(BaseModel):
    """Response schema for training job creation"""
    
    jobs: list[TrainingJobResponse] = Field(..., description="Created training jobs")
    message: str = Field(..., description="Status message")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "jobs": [],
                "message": "Created 3 training jobs"
            }
        }
    }
