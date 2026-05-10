from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ModelMetrics(BaseModel):
    accuracy: float = Field(..., description="Accuracy score (0.0 to 1.0)")
    precision: float = Field(..., description="Precision score (0.0 to 1.0)")
    recall: float = Field(..., description="Recall score (0.0 to 1.0)")
    f1_score: float = Field(..., description="F1 score (0.0 to 1.0)")
    roc_auc: float = Field(..., description="ROC-AUC score (0.0 to 1.0)")

    model_config = {
        "json_schema_extra": {
            "example": {
                "accuracy": 0.8234,
                "precision": 0.7891,
                "recall": 0.7456,
                "f1_score": 0.7667,
                "roc_auc": 0.8567,
            }
        }
    }


class ConfusionMatrixResponse(BaseModel):
    matrix: list[list[int]] = Field(..., description="2x2 confusion matrix [[TN, FP], [FN, TP]]")
    labels: list[str] = Field(default=["No Churn", "Churn"], description="Class labels")

    model_config = {
        "json_schema_extra": {
            "example": {"matrix": [[850, 120], [95, 340]], "labels": ["No Churn", "Churn"]}
        }
    }


class ROCCurvePoint(BaseModel):
    fpr: float = Field(..., description="False positive rate")
    tpr: float = Field(..., description="True positive rate")
    threshold: float = Field(..., description="Classification threshold")


class ROCCurveResponse(BaseModel):
    points: list[ROCCurvePoint] = Field(..., description="ROC curve points")
    auc: float = Field(..., description="Area under the curve (ROC-AUC)")

    model_config = {
        "json_schema_extra": {
            "example": {
                "points": [
                    {"fpr": 0.0, "tpr": 0.0, "threshold": 1.0},
                    {"fpr": 0.1, "tpr": 0.6, "threshold": 0.7},
                    {"fpr": 0.3, "tpr": 0.85, "threshold": 0.5},
                    {"fpr": 1.0, "tpr": 1.0, "threshold": 0.0},
                ],
                "auc": 0.8567,
            }
        }
    }


class ModelVersionResponse(BaseModel):
    id: UUID = Field(..., description="Model version unique identifier")
    user_id: UUID = Field(..., description="User who trained the model")
    dataset_id: UUID = Field(..., description="Dataset used for training")
    preprocessing_config_id: UUID = Field(..., description="Preprocessing configuration ID")
    model_type: str = Field(..., description="Model type (KNN, NaiveBayes, DecisionTree, SVM)")
    version: str = Field(..., description="Version identifier")
    hyperparameters: dict = Field(..., description="Model hyperparameters")
    metrics: ModelMetrics = Field(..., description="Evaluation metrics")
    confusion_matrix: list[list[int]] = Field(..., description="Confusion matrix")
    training_time_seconds: float = Field(..., description="Training time in seconds")
    artifact_path: str = Field(..., description="Path to model artifact in R2 storage")
    mlflow_run_id: Optional[str] = Field(None, description="MLflow run ID")
    status: str = Field(..., description="Model status (active, archived)")
    classification_threshold: float = Field(
        ..., description="Classification threshold (0.0 to 1.0)"
    )
    trained_at: datetime = Field(..., description="Training timestamp")
    archived_at: Optional[datetime] = Field(None, description="Archive timestamp")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "880e8400-e29b-41d4-a716-446655440000",
                "user_id": "770e8400-e29b-41d4-a716-446655440000",
                "dataset_id": "550e8400-e29b-41d4-a716-446655440000",
                "preprocessing_config_id": "990e8400-e29b-41d4-a716-446655440000",
                "model_type": "KNN",
                "version": "KNN_550e8400_20240115_103045",
                "hyperparameters": {"n_neighbors": 7, "weights": "distance", "metric": "euclidean"},
                "metrics": {
                    "accuracy": 0.8234,
                    "precision": 0.7891,
                    "recall": 0.7456,
                    "f1_score": 0.7667,
                    "roc_auc": 0.8567,
                },
                "confusion_matrix": [[850, 120], [95, 340]],
                "training_time_seconds": 12.45,
                "artifact_path": "models/770e8400-e29b-41d4-a716-446655440000/880e8400-e29b-41d4-a716-446655440000/model.joblib",
                "mlflow_run_id": "abc123def456",
                "status": "active",
                "classification_threshold": 0.5,
                "trained_at": "2024-01-15T10:30:45Z",
                "archived_at": None,
            }
        },
    }


class ModelVersionListResponse(BaseModel):
    versions: list[ModelVersionResponse] = Field(..., description="List of model versions")
    total: int = Field(..., description="Total number of versions")

    model_config = {"json_schema_extra": {"example": {"versions": [], "total": 0}}}


class ThresholdUpdateRequest(BaseModel):
    threshold: float = Field(
        ..., description="New classification threshold (0.0 to 1.0)", ge=0.0, le=1.0
    )

    model_config = {"json_schema_extra": {"example": {"threshold": 0.3}}}


class ThresholdUpdateResponse(BaseModel):
    id: UUID = Field(..., description="Model version ID")
    classification_threshold: float = Field(..., description="Updated threshold")
    message: str = Field(..., description="Status message")

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "880e8400-e29b-41d4-a716-446655440000",
                "classification_threshold": 0.3,
                "message": "Classification threshold updated successfully",
            }
        }
    }


class ArchiveModelRequest(BaseModel):
    archive: bool = Field(..., description="True to archive, False to unarchive")

    model_config = {"json_schema_extra": {"example": {"archive": True}}}


class ArchiveModelResponse(BaseModel):
    id: UUID = Field(..., description="Model version ID")
    status: str = Field(..., description="New status (active or archived)")
    message: str = Field(..., description="Status message")

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "880e8400-e29b-41d4-a716-446655440000",
                "status": "archived",
                "message": "Model version archived successfully",
            }
        }
    }
