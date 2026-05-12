import logging
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.api.dependencies import (
    require_admin,
    require_any_authenticated_user,
)
from backend.domain.schemas.auth import UserResponse
from backend.domain.schemas.model import (
    ArchiveModelRequest,
    ArchiveModelResponse,
    ConfusionMatrixResponse,
    ModelMetrics,
    ModelVersionListResponse,
    ModelVersionResponse,
    ROCCurveResponse,
    ThresholdUpdateRequest,
    ThresholdUpdateResponse,
)
from backend.domain.schemas.training import (
    TrainingJobCreate,
    TrainingJobCreateResponse,
    TrainingJobListResponse,
    TrainingJobResponse,
)
from backend.infrastructure.database import get_db
from backend.services.dataset_service import DatasetService
from backend.services.model_evaluation_service import ModelEvaluationService
from backend.services.training_service import TrainingService
from backend.workers.training_tasks import train_model_task

router = APIRouter(prefix="/models", tags=["Models"])

logger = logging.getLogger(__name__)


@router.post(
    "/train",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=TrainingJobCreateResponse,
    responses={
        202: {"description": "Training job(s) created"},
        400: {"description": "Bad request - invalid model types or dataset not found"},
        403: {"description": "Forbidden - requires Admin role"},
        404: {"description": "Dataset not found"},
    },
)
async def train_model(
    request: TrainingJobCreate,
    current_user: Annotated[UserResponse, Depends(require_admin)],
    db: Session = Depends(get_db),
):
    dataset = DatasetService.get_dataset_by_id(db, request.dataset_id)

    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Dataset {request.dataset_id} not found"
        )

    # Admin can train on any dataset; non-Admin can only train on their own
    # Note: dataset.user_id is a UUID object, current_user.id is a string
    if str(dataset.user_id) != str(current_user.id):
        if current_user.role != "Admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only train models on your own datasets",
            )

    if dataset.status != "ready":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Dataset status is '{dataset.status}'. Must be 'ready' to train models.",
        )

    valid_model_types = {"KNN", "NaiveBayes", "DecisionTree", "SVM"}
    invalid_types = set(request.model_types) - valid_model_types

    if invalid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid model types: {', '.join(invalid_types)}. "
            f"Valid types: {', '.join(valid_model_types)}",
        )

    # Check for existing active models AND running/queued training jobs to prevent duplicates
    from backend.domain.models.model_version import ModelVersion
    from backend.domain.models.training_job import TrainingJob
    
    # Check for existing active model versions
    existing_models = (
        db.query(ModelVersion)
        .filter(
            ModelVersion.dataset_id == request.dataset_id,
            ModelVersion.user_id == current_user.id,
            ModelVersion.status == "active"
        )
        .all()
    )
    
    existing_model_types = {model.model_type for model in existing_models}
    
    # Also check for running or queued training jobs
    active_training_jobs = (
        db.query(TrainingJob)
        .filter(
            TrainingJob.dataset_id == request.dataset_id,
            TrainingJob.user_id == current_user.id,
            TrainingJob.status.in_(["queued", "running"])
        )
        .all()
    )
    
    training_model_types = {job.model_type for job in active_training_jobs}
    
    # Combine both sets to get all model types that exist or are being trained
    all_existing_types = existing_model_types | training_model_types
    
    # Filter out model types that already exist or are being trained
    models_to_train = [mt for mt in request.model_types if mt not in all_existing_types]
    
    if len(models_to_train) < len(request.model_types):
        skipped = [mt for mt in request.model_types if mt in all_existing_types]
        skipped_reasons = []
        for mt in skipped:
            if mt in existing_model_types:
                skipped_reasons.append(f"{mt} (already exists)")
            elif mt in training_model_types:
                skipped_reasons.append(f"{mt} (training in progress)")
        
        logger.warning(
            f"Skipping training for: {', '.join(skipped_reasons)}. "
            f"Archive existing models or wait for training to complete."
        )
    
    if not models_to_train:
        error_details = []
        if existing_model_types:
            error_details.append(f"Existing models: {', '.join(existing_model_types)}")
        if training_model_types:
            error_details.append(f"Training in progress: {', '.join(training_model_types)}")
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"All selected model types already exist or are being trained for this dataset. "
                   f"{'. '.join(error_details)}. "
                   f"Please archive existing models or wait for training to complete."
        )

    created_jobs = []

    for model_type in models_to_train:
        training_job = TrainingService.create_training_job(
            db=db, user_id=current_user.id, dataset_id=request.dataset_id, model_type=model_type
        )

        train_model_task.delay(
            job_id=str(training_job.id),
            dataset_id=str(request.dataset_id),
            model_type=model_type,
            hyperparameters=request.hyperparameters,
        )

        created_jobs.append(training_job)

    job_responses = [TrainingJobResponse.model_validate(job) for job in created_jobs]

    return TrainingJobCreateResponse(
        jobs=job_responses, message=f"Created {len(created_jobs)} training job(s)"
    )


@router.get(
    "/jobs",
    response_model=TrainingJobListResponse,
    responses={
        200: {"description": "List of training jobs"},
    },
)
async def list_training_jobs(
    current_user: Annotated[UserResponse, Depends(require_any_authenticated_user)],
    db: Session = Depends(get_db),
    status_filter: Optional[str] = Query(
        None, description="Filter by status (queued, running, completed, failed)"
    ),
):
    try:
        jobs = TrainingService.list_training_jobs(
            db=db, user_id=None, status_filter=status_filter
        )

        job_responses = [TrainingJobResponse.model_validate(job) for job in jobs]

        return TrainingJobListResponse(jobs=job_responses, total=len(job_responses))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/jobs/{job_id}",
    response_model=TrainingJobResponse,
    responses={
        200: {"description": "Training job details"},
        404: {"description": "Training job not found"},
    },
)
async def get_training_job(
    job_id: str,
    current_user: Annotated[UserResponse, Depends(require_any_authenticated_user)],
    db: Session = Depends(get_db),
):
    from uuid import UUID

    try:
        job_uuid = UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid job_id format")

    training_job = TrainingService.get_training_job(db=db, job_id=job_uuid, user_id=None)

    if not training_job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Training job {job_id} not found"
        )

    return TrainingJobResponse.model_validate(training_job)


@router.delete(
    "/jobs/{job_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        204: {"description": "Training job deleted successfully"},
        400: {"description": "Cannot delete running job"},
        403: {"description": "Forbidden - requires Admin role"},
        404: {"description": "Training job not found"},
    },
)
async def delete_training_job(
    job_id: str,
    current_user: Annotated[UserResponse, Depends(require_admin)],
    db: Session = Depends(get_db),
):
    from uuid import UUID

    try:
        job_uuid = UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid job_id format")

    training_job = TrainingService.get_training_job(db=db, job_id=job_uuid, user_id=current_user.id)

    if not training_job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Training job {job_id} not found"
        )

    if training_job.status == "running":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete running training job. Please wait for it to complete or fail.",
        )

    deleted = TrainingService.delete_training_job(db=db, job_id=job_uuid, user_id=current_user.id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Training job {job_id} not found"
        )

    return None


@router.get(
    "/versions",
    response_model=ModelVersionListResponse,
    responses={
        200: {"description": "List of model versions"},
    },
)
async def list_model_versions(
    current_user: Annotated[UserResponse, Depends(require_any_authenticated_user)],
    db: Session = Depends(get_db),
    model_type: Optional[str] = Query(None, description="Filter by model type"),
    status: Optional[str] = Query(None, description="Filter by status (active, archived)"),
    sort_by: str = Query("trained_at", description="Column to sort by"),
    sort_order: str = Query("desc", description="Sort order (asc, desc)"),
):
    try:
        versions = ModelEvaluationService.list_model_versions(
            db=db,
            user_id=None,
            model_type=model_type,
            status=status,
            sort_by=sort_by,
            sort_order=sort_order,
        )

        version_responses = []
        for version in versions:
            metrics_data = version.metrics or {}
            if not metrics_data:
                metrics_data = {"accuracy": 0.0, "precision": 0.0, "recall": 0.0, "f1_score": 0.0, "roc_auc": 0.0}
            metrics = ModelMetrics(**metrics_data)

            version_dict = {
                "id": version.id,
                "user_id": version.user_id,
                "dataset_id": version.dataset_id,
                "preprocessing_config_id": version.preprocessing_config_id,
                "model_type": version.model_type,
                "version": version.version,
                "hyperparameters": version.hyperparameters,
                "metrics": metrics,
                "confusion_matrix": version.confusion_matrix,
                "training_time_seconds": version.training_time_seconds,
                "artifact_path": version.artifact_path,
                "mlflow_run_id": version.mlflow_run_id,
                "status": version.status,
                "classification_threshold": version.classification_threshold,
                "trained_at": version.trained_at,
                "archived_at": version.archived_at,
            }

            version_responses.append(ModelVersionResponse(**version_dict))

        return ModelVersionListResponse(versions=version_responses, total=len(version_responses))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/versions/{version_id}",
    response_model=ModelVersionResponse,
    responses={
        200: {"description": "Model version details"},
        404: {"description": "Model version not found"},
    },
)
async def get_model_version(
    version_id: str,
    current_user: Annotated[UserResponse, Depends(require_any_authenticated_user)],
    db: Session = Depends(get_db),
):
    from uuid import UUID

    try:
        version_uuid = UUID(version_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid version_id format"
        )

    model_version = ModelEvaluationService.get_model_version_by_id(
        db=db, version_id=version_uuid, user_id=None
    )

    if not model_version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Model version {version_id} not found"
        )

    metrics_data = model_version.metrics or {}
    if not metrics_data:
        metrics_data = {"accuracy": 0.0, "precision": 0.0, "recall": 0.0, "f1_score": 0.0, "roc_auc": 0.0}
    metrics = ModelMetrics(**metrics_data)

    version_dict = {
        "id": model_version.id,
        "user_id": model_version.user_id,
        "dataset_id": model_version.dataset_id,
        "preprocessing_config_id": model_version.preprocessing_config_id,
        "model_type": model_version.model_type,
        "version": model_version.version,
        "hyperparameters": model_version.hyperparameters,
        "metrics": metrics,
        "confusion_matrix": model_version.confusion_matrix,
        "training_time_seconds": model_version.training_time_seconds,
        "artifact_path": model_version.artifact_path,
        "mlflow_run_id": model_version.mlflow_run_id,
        "status": model_version.status,
        "classification_threshold": model_version.classification_threshold,
        "trained_at": model_version.trained_at,
        "archived_at": model_version.archived_at,
    }

    return ModelVersionResponse(**version_dict)


@router.get(
    "/versions/{version_id}/metrics",
    response_model=ModelMetrics,
    responses={
        200: {"description": "Model evaluation metrics"},
        404: {"description": "Model version not found"},
    },
)
async def get_model_metrics(
    version_id: str,
    current_user: Annotated[UserResponse, Depends(require_any_authenticated_user)],
    db: Session = Depends(get_db),
):
    from uuid import UUID

    try:
        version_uuid = UUID(version_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid version_id format"
        )

    model_version = ModelEvaluationService.get_model_version_by_id(
        db=db, version_id=version_uuid, user_id=None
    )

    if not model_version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Model version {version_id} not found"
        )

    metrics_data = model_version.metrics or {}
    if not metrics_data:
        metrics_data = {"accuracy": 0.0, "precision": 0.0, "recall": 0.0, "f1_score": 0.0, "roc_auc": 0.0}
    return ModelMetrics(**metrics_data)


@router.get(
    "/versions/{version_id}/confusion-matrix",
    response_model=ConfusionMatrixResponse,
    responses={
        200: {"description": "Confusion matrix"},
        404: {"description": "Model version not found"},
    },
)
async def get_confusion_matrix(
    version_id: str,
    current_user: Annotated[UserResponse, Depends(require_any_authenticated_user)],
    db: Session = Depends(get_db),
):
    from uuid import UUID

    try:
        version_uuid = UUID(version_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid version_id format"
        )

    model_version = ModelEvaluationService.get_model_version_by_id(
        db=db, version_id=version_uuid, user_id=None
    )

    if not model_version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Model version {version_id} not found"
        )

    return ConfusionMatrixResponse(
        matrix=model_version.confusion_matrix, labels=["No Churn", "Churn"]
    )


@router.get(
    "/versions/{version_id}/roc-curve",
    response_model=ROCCurveResponse,
    responses={
        200: {"description": "ROC curve data"},
        404: {"description": "Model version not found"},
        500: {"description": "Error computing ROC curve"},
    },
)
async def get_roc_curve(
    version_id: str,
    current_user: Annotated[UserResponse, Depends(require_any_authenticated_user)],
    db: Session = Depends(get_db),
):
    from uuid import UUID

    try:
        version_uuid = UUID(version_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid version_id format"
        )

    try:
        roc_data = ModelEvaluationService.compute_roc_curve(
            db=db, version_id=version_uuid, user_id=None
        )

        return ROCCurveResponse(**roc_data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error computing ROC curve: {str(e)}",
        )


@router.patch(
    "/versions/{version_id}/threshold",
    response_model=ThresholdUpdateResponse,
    responses={
        200: {"description": "Threshold updated successfully"},
        400: {"description": "Invalid threshold value"},
        403: {"description": "Forbidden - requires Admin role"},
        404: {"description": "Model version not found"},
    },
)
async def update_threshold(
    version_id: str,
    request: ThresholdUpdateRequest,
    current_user: Annotated[UserResponse, Depends(require_admin)],
    db: Session = Depends(get_db),
):
    from uuid import UUID

    try:
        version_uuid = UUID(version_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid version_id format"
        )

    try:
        updated_version = ModelEvaluationService.update_classification_threshold(
            db=db, version_id=version_uuid, threshold=request.threshold, user_id=current_user.id
        )

        return ThresholdUpdateResponse(
            id=updated_version.id,
            classification_threshold=updated_version.classification_threshold,
            message="Classification threshold updated successfully",
        )
    except ValueError as e:
        if "not found" in str(e):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/versions/{version_id}/archive",
    response_model=ArchiveModelResponse,
    responses={
        200: {"description": "Model version archived/unarchived successfully"},
        403: {"description": "Forbidden - requires Admin role"},
        404: {"description": "Model version not found"},
    },
)
async def archive_model_version(
    version_id: str,
    request: ArchiveModelRequest,
    current_user: Annotated[UserResponse, Depends(require_admin)],
    db: Session = Depends(get_db),
):
    from uuid import UUID

    try:
        version_uuid = UUID(version_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid version_id format"
        )

    try:
        updated_version = ModelEvaluationService.archive_model_version(
            db=db, version_id=version_uuid, archive=request.archive, user_id=current_user.id
        )

        action = "archived" if request.archive else "unarchived"

        return ArchiveModelResponse(
            id=updated_version.id,
            status=updated_version.status,
            message=f"Model version {action} successfully",
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete(
    "/versions/{version_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        204: {"description": "Model version deleted successfully"},
        403: {"description": "Forbidden - requires Admin role"},
        404: {"description": "Model version not found"},
    },
)
async def delete_model_version(
    version_id: str,
    current_user: Annotated[UserResponse, Depends(require_admin)],
    db: Session = Depends(get_db),
):
    return None
