"""
Model API Routes

This module provides REST API endpoints for model training and management with RBAC.
"""

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.api.dependencies import (
    get_current_user,
    require_data_scientist_or_admin,
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


@router.post(
    "/train",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=TrainingJobCreateResponse,
    responses={
        202: {"description": "Training job(s) created"},
        400: {"description": "Bad request - invalid model types or dataset not found"},
        403: {"description": "Forbidden - requires Data_Scientist or Admin role"},
        404: {"description": "Dataset not found"},
    }
)
async def train_model(
    request: TrainingJobCreate,
    # Requirement 19.3: Data_Scientist can train models
    # Requirement 19.2: Admin has full access
    current_user: Annotated[UserResponse, Depends(require_data_scientist_or_admin)],
    db: Session = Depends(get_db)
):
    """
    Create training job(s) for selected model types
    
    **Authorization**: Requires Data_Scientist or Admin role
    
    **RBAC Matrix**:
    - Admin: ✓ Allowed
    - Data_Scientist: ✓ Allowed
    - Analyst: ✗ Forbidden
    
    **Requirements**:
    - 8.5: Create Training_Job for each selected model type
    - 8.6: Execute Training_Jobs asynchronously in background processes
    - 8.7: Display Training_Job status in real-time
    
    Args:
        request: Training job creation request
        current_user: Current authenticated user (must be Data_Scientist or Admin)
        db: Database session
        
    Returns:
        Created training jobs with status
    """
    # Validate dataset exists and user has access
    dataset = DatasetService.get_dataset_by_id(db, request.dataset_id)
    
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset {request.dataset_id} not found"
        )
    
    # Check dataset ownership (users can only train on their own datasets)
    if dataset.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only train models on your own datasets"
        )
    
    # Check dataset is ready for training
    if dataset.status != "ready":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Dataset status is '{dataset.status}'. Must be 'ready' to train models."
        )
    
    # Validate model types
    valid_model_types = {"KNN", "NaiveBayes", "DecisionTree", "SVM"}
    invalid_types = set(request.model_types) - valid_model_types
    
    if invalid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid model types: {', '.join(invalid_types)}. "
                   f"Valid types: {', '.join(valid_model_types)}"
        )
    
    # Create training jobs for each model type
    created_jobs = []
    
    for model_type in request.model_types:
        # Create training job record
        training_job = TrainingService.create_training_job(
            db=db,
            user_id=current_user.id,
            dataset_id=request.dataset_id,
            model_type=model_type
        )
        
        # Queue background training task
        train_model_task.delay(
            job_id=str(training_job.id),
            dataset_id=str(request.dataset_id),
            model_type=model_type,
            hyperparameters=request.hyperparameters
        )
        
        created_jobs.append(training_job)
    
    # Convert to response schema
    job_responses = [TrainingJobResponse.model_validate(job) for job in created_jobs]
    
    return TrainingJobCreateResponse(
        jobs=job_responses,
        message=f"Created {len(created_jobs)} training job(s)"
    )


@router.get(
    "/jobs",
    response_model=TrainingJobListResponse,
    responses={
        200: {"description": "List of training jobs"},
    }
)
async def list_training_jobs(
    current_user: Annotated[UserResponse, Depends(require_any_authenticated_user)],
    db: Session = Depends(get_db),
    status_filter: Optional[str] = Query(
        None,
        description="Filter by status (queued, running, completed, failed)"
    )
):
    """
    List user's training jobs with optional status filter
    
    **Authorization**: Requires any authenticated user
    
    **RBAC Matrix**:
    - Admin: ✓ Allowed (own jobs only)
    - Data_Scientist: ✓ Allowed (own jobs only)
    - Analyst: ✓ Allowed (own jobs only)
    
    **Requirements**:
    - 8.7: Display Training_Job status in real-time
    
    Args:
        status_filter: Optional status filter
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of training jobs
    """
    try:
        jobs = TrainingService.list_training_jobs(
            db=db,
            user_id=current_user.id,
            status_filter=status_filter
        )
        
        job_responses = [TrainingJobResponse.model_validate(job) for job in jobs]
        
        return TrainingJobListResponse(
            jobs=job_responses,
            total=len(job_responses)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/jobs/{job_id}",
    response_model=TrainingJobResponse,
    responses={
        200: {"description": "Training job details"},
        404: {"description": "Training job not found"},
    }
)
async def get_training_job(
    job_id: str,
    current_user: Annotated[UserResponse, Depends(require_any_authenticated_user)],
    db: Session = Depends(get_db)
):
    """
    Get specific training job details
    
    **Authorization**: Requires any authenticated user (own jobs only)
    
    **RBAC Matrix**:
    - Admin: ✓ Allowed (own jobs only)
    - Data_Scientist: ✓ Allowed (own jobs only)
    - Analyst: ✓ Allowed (own jobs only)
    
    **Requirements**:
    - 8.7: Display Training_Job status in real-time
    
    Args:
        job_id: Training job UUID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Training job details
    """
    from uuid import UUID
    
    try:
        job_uuid = UUID(job_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid job_id format"
        )
    
    training_job = TrainingService.get_training_job(
        db=db,
        job_id=job_uuid,
        user_id=current_user.id
    )
    
    if not training_job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Training job {job_id} not found"
        )
    
    return TrainingJobResponse.model_validate(training_job)


@router.delete(
    "/jobs/{job_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        204: {"description": "Training job deleted successfully"},
        400: {"description": "Cannot delete running job"},
        403: {"description": "Forbidden - requires Data_Scientist or Admin role"},
        404: {"description": "Training job not found"},
    }
)
async def delete_training_job(
    job_id: str,
    current_user: Annotated[UserResponse, Depends(require_data_scientist_or_admin)],
    db: Session = Depends(get_db)
):
    """
    Cancel/delete a training job
    
    **Authorization**: Requires Data_Scientist or Admin role (own jobs only)
    
    **RBAC Matrix**:
    - Admin: ✓ Allowed (own jobs only)
    - Data_Scientist: ✓ Allowed (own jobs only)
    - Analyst: ✗ Forbidden
    
    **Note**: Cannot delete running jobs. Only queued or failed jobs can be deleted.
    
    Args:
        job_id: Training job UUID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        No content (204)
    """
    from uuid import UUID
    
    try:
        job_uuid = UUID(job_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid job_id format"
        )
    
    # Check if job exists and get its status
    training_job = TrainingService.get_training_job(
        db=db,
        job_id=job_uuid,
        user_id=current_user.id
    )
    
    if not training_job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Training job {job_id} not found"
        )
    
    if training_job.status == "running":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete running training job. Please wait for it to complete or fail."
        )
    
    # Delete the job
    deleted = TrainingService.delete_training_job(
        db=db,
        job_id=job_uuid,
        user_id=current_user.id
    )
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Training job {job_id} not found"
        )
    
    return None


@router.get(
    "/versions",
    response_model=ModelVersionListResponse,
    responses={
        200: {"description": "List of model versions"},
    }
)
async def list_model_versions(
    # Requirement 19.4: All authenticated users can view models
    current_user: Annotated[UserResponse, Depends(require_any_authenticated_user)],
    db: Session = Depends(get_db),
    model_type: Optional[str] = Query(None, description="Filter by model type"),
    status: Optional[str] = Query(None, description="Filter by status (active, archived)"),
    sort_by: str = Query("trained_at", description="Column to sort by"),
    sort_order: str = Query("desc", description="Sort order (asc, desc)")
):
    """
    List all model versions with optional filtering and sorting
    
    **Authorization**: Requires any authenticated user
    
    **RBAC Matrix**:
    - Admin: ✓ Allowed
    - Data_Scientist: ✓ Allowed
    - Analyst: ✓ Allowed (read-only)
    
    **Requirements**:
    - 11.1: Display comparison table with all metrics
    - 11.5: Allow sorting by any metric column
    
    Args:
        current_user: Current authenticated user
        db: Database session
        model_type: Optional model type filter
        status: Optional status filter
        sort_by: Column to sort by
        sort_order: Sort order (asc or desc)
        
    Returns:
        List of model versions
    """
    try:
        versions = ModelEvaluationService.list_model_versions(
            db=db,
            user_id=current_user.id,
            model_type=model_type,
            status=status,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        # Convert to response schema
        version_responses = []
        for version in versions:
            # Convert metrics dict to ModelMetrics schema
            metrics = ModelMetrics(**version.metrics)
            
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
                "archived_at": version.archived_at
            }
            
            version_responses.append(ModelVersionResponse(**version_dict))
        
        return ModelVersionListResponse(
            versions=version_responses,
            total=len(version_responses)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/versions/{version_id}",
    response_model=ModelVersionResponse,
    responses={
        200: {"description": "Model version details"},
        404: {"description": "Model version not found"},
    }
)
async def get_model_version(
    version_id: str,
    current_user: Annotated[UserResponse, Depends(require_any_authenticated_user)],
    db: Session = Depends(get_db)
):
    """
    Get model version details
    
    **Authorization**: Requires any authenticated user
    
    **RBAC Matrix**:
    - Admin: ✓ Allowed
    - Data_Scientist: ✓ Allowed
    - Analyst: ✓ Allowed (read-only)
    
    **Requirements**:
    - 15.1: Assign unique version identifier
    - 15.2: Store training metadata
    
    Args:
        version_id: Model version UUID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Model version details
    """
    from uuid import UUID
    
    try:
        version_uuid = UUID(version_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid version_id format"
        )
    
    model_version = ModelEvaluationService.get_model_version_by_id(
        db=db,
        version_id=version_uuid,
        user_id=current_user.id
    )
    
    if not model_version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model version {version_id} not found"
        )
    
    # Convert metrics dict to ModelMetrics schema
    metrics = ModelMetrics(**model_version.metrics)
    
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
        "archived_at": model_version.archived_at
    }
    
    return ModelVersionResponse(**version_dict)


@router.get(
    "/versions/{version_id}/metrics",
    response_model=ModelMetrics,
    responses={
        200: {"description": "Model evaluation metrics"},
        404: {"description": "Model version not found"},
    }
)
async def get_model_metrics(
    version_id: str,
    current_user: Annotated[UserResponse, Depends(require_any_authenticated_user)],
    db: Session = Depends(get_db)
):
    """
    Get all evaluation metrics for a model version
    
    **Authorization**: Requires any authenticated user
    
    **RBAC Matrix**:
    - Admin: ✓ Allowed
    - Data_Scientist: ✓ Allowed
    - Analyst: ✓ Allowed (read-only)
    
    **Requirements**:
    - 10.1: Compute accuracy, precision, recall, F1-score
    - 10.3: Compute ROC-AUC score
    - 10.4: Display metrics
    
    Args:
        version_id: Model version UUID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Model evaluation metrics
    """
    from uuid import UUID
    
    try:
        version_uuid = UUID(version_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid version_id format"
        )
    
    model_version = ModelEvaluationService.get_model_version_by_id(
        db=db,
        version_id=version_uuid,
        user_id=current_user.id
    )
    
    if not model_version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model version {version_id} not found"
        )
    
    return ModelMetrics(**model_version.metrics)


@router.get(
    "/versions/{version_id}/confusion-matrix",
    response_model=ConfusionMatrixResponse,
    responses={
        200: {"description": "Confusion matrix"},
        404: {"description": "Model version not found"},
    }
)
async def get_confusion_matrix(
    version_id: str,
    current_user: Annotated[UserResponse, Depends(require_any_authenticated_user)],
    db: Session = Depends(get_db)
):
    """
    Get confusion matrix for a model version
    
    **Authorization**: Requires any authenticated user
    
    **RBAC Matrix**:
    - Admin: ✓ Allowed
    - Data_Scientist: ✓ Allowed
    - Analyst: ✓ Allowed (read-only)
    
    **Requirements**:
    - 10.2: Compute confusion matrix
    - 10.4: Display confusion matrix heatmap
    
    Args:
        version_id: Model version UUID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Confusion matrix data
    """
    from uuid import UUID
    
    try:
        version_uuid = UUID(version_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid version_id format"
        )
    
    model_version = ModelEvaluationService.get_model_version_by_id(
        db=db,
        version_id=version_uuid,
        user_id=current_user.id
    )
    
    if not model_version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model version {version_id} not found"
        )
    
    return ConfusionMatrixResponse(
        matrix=model_version.confusion_matrix,
        labels=["No Churn", "Churn"]
    )


@router.get(
    "/versions/{version_id}/roc-curve",
    response_model=ROCCurveResponse,
    responses={
        200: {"description": "ROC curve data"},
        404: {"description": "Model version not found"},
        500: {"description": "Error computing ROC curve"},
    }
)
async def get_roc_curve(
    version_id: str,
    current_user: Annotated[UserResponse, Depends(require_any_authenticated_user)],
    db: Session = Depends(get_db)
):
    """
    Get ROC curve data for a model version
    
    **Authorization**: Requires any authenticated user
    
    **RBAC Matrix**:
    - Admin: ✓ Allowed
    - Data_Scientist: ✓ Allowed
    - Analyst: ✓ Allowed (read-only)
    
    **Requirements**:
    - 10.3: Compute ROC-AUC score
    - 10.6: Display ROC curve chart
    
    Args:
        version_id: Model version UUID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        ROC curve points and AUC
    """
    from uuid import UUID
    
    try:
        version_uuid = UUID(version_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid version_id format"
        )
    
    try:
        roc_data = ModelEvaluationService.compute_roc_curve(
            db=db,
            version_id=version_uuid,
            user_id=current_user.id
        )
        
        return ROCCurveResponse(**roc_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error computing ROC curve: {str(e)}"
        )


@router.patch(
    "/versions/{version_id}/threshold",
    response_model=ThresholdUpdateResponse,
    responses={
        200: {"description": "Threshold updated successfully"},
        400: {"description": "Invalid threshold value"},
        403: {"description": "Forbidden - requires Data_Scientist or Admin role"},
        404: {"description": "Model version not found"},
    }
)
async def update_threshold(
    version_id: str,
    request: ThresholdUpdateRequest,
    # Requirement 12.9: Data_Scientist can adjust classification threshold
    # Requirement 19.3: Data_Scientist has this permission
    current_user: Annotated[UserResponse, Depends(require_data_scientist_or_admin)],
    db: Session = Depends(get_db)
):
    """
    Update classification threshold for a model version
    
    **Authorization**: Requires Data_Scientist or Admin role
    
    **RBAC Matrix**:
    - Admin: ✓ Allowed
    - Data_Scientist: ✓ Allowed
    - Analyst: ✗ Forbidden
    
    **Business Context**: 
    Requirement 12.9 - Users with Data_Scientist role can adjust the threshold 
    to optimize Recall at the cost of Precision, given that missed churners 
    (False Negatives) carry higher business cost than false alarms.
    
    Args:
        version_id: Model version UUID
        request: Threshold update request
        current_user: Current authenticated user (must be Data_Scientist or Admin)
        db: Database session
        
    Returns:
        Updated model version with new threshold
    """
    from uuid import UUID
    
    try:
        version_uuid = UUID(version_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid version_id format"
        )
    
    try:
        updated_version = ModelEvaluationService.update_classification_threshold(
            db=db,
            version_id=version_uuid,
            threshold=request.threshold,
            user_id=current_user.id
        )
        
        return ThresholdUpdateResponse(
            id=updated_version.id,
            classification_threshold=updated_version.classification_threshold,
            message="Classification threshold updated successfully"
        )
    except ValueError as e:
        if "not found" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )


@router.post(
    "/versions/{version_id}/archive",
    response_model=ArchiveModelResponse,
    responses={
        200: {"description": "Model version archived/unarchived successfully"},
        403: {"description": "Forbidden - requires Data_Scientist or Admin role"},
        404: {"description": "Model version not found"},
    }
)
async def archive_model_version(
    version_id: str,
    request: ArchiveModelRequest,
    current_user: Annotated[UserResponse, Depends(require_data_scientist_or_admin)],
    db: Session = Depends(get_db)
):
    """
    Archive or unarchive a model version
    
    **Authorization**: Requires Data_Scientist or Admin role
    
    **RBAC Matrix**:
    - Admin: ✓ Allowed
    - Data_Scientist: ✓ Allowed (own models only)
    - Analyst: ✗ Forbidden
    
    **Requirements**:
    - 11.6: Allow users to select active model version for predictions
    - 15.6: Allow users to select any model version for prediction serving
    
    Args:
        version_id: Model version UUID
        request: Archive request
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Updated model version status
    """
    from uuid import UUID
    
    try:
        version_uuid = UUID(version_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid version_id format"
        )
    
    try:
        updated_version = ModelEvaluationService.archive_model_version(
            db=db,
            version_id=version_uuid,
            archive=request.archive,
            user_id=current_user.id
        )
        
        action = "archived" if request.archive else "unarchived"
        
        return ArchiveModelResponse(
            id=updated_version.id,
            status=updated_version.status,
            message=f"Model version {action} successfully"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.delete(
    "/versions/{version_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        204: {"description": "Model version deleted successfully"},
        403: {"description": "Forbidden - requires Data_Scientist or Admin role"},
        404: {"description": "Model version not found"},
    }
)
async def delete_model_version(
    version_id: str,
    current_user: Annotated[UserResponse, Depends(require_data_scientist_or_admin)],
    db: Session = Depends(get_db)
):
    """
    Delete a model version
    
    **Authorization**: Requires Data_Scientist or Admin role
    
    **RBAC Matrix**:
    - Admin: ✓ Allowed
    - Data_Scientist: ✓ Allowed (own models only)
    - Analyst: ✗ Forbidden
    
    Args:
        version_id: Model version UUID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        No content (204)
    """
    # TODO: Implement model version deletion with ownership check
    return None
