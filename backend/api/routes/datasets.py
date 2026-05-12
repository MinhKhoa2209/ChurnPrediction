import base64
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status
from sqlalchemy.orm import Session

from backend.api.dependencies import (
    require_admin,
    require_any_authenticated_user,
)
from backend.domain.models.dataset import Dataset
from backend.domain.schemas.auth import UserResponse
from backend.domain.schemas.dataset import (
    DatasetListResponse,
    DatasetProgressResponse,
    DatasetResponse,
    DatasetUploadResponse,
)
from backend.infrastructure.database import get_db
from backend.services.dataset_service import DatasetService
from backend.workers.dataset_tasks import process_csv_file

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/datasets", tags=["Datasets"])


MAX_FILE_SIZE = 50 * 1024 * 1024


@router.post(
    "/upload",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=DatasetUploadResponse,
    responses={
        202: {"description": "Dataset upload accepted for processing"},
        400: {"description": "Invalid file format or validation error"},
        403: {"description": "Forbidden - requires Admin role"},
        413: {"description": "File too large - maximum 50MB"},
    },
)
async def upload_dataset(
    file: UploadFile = File(..., description="CSV file containing customer data"),
    response: Response = None,
    current_user: Annotated[UserResponse, Depends(require_admin)] = None,
    db: Session = Depends(get_db),
) -> DatasetUploadResponse:
    if not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only CSV files are accepted.",
        )

    file_content = await file.read()

    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size is 50MB. Uploaded file is {len(file_content) / (1024 * 1024):.2f}MB.",
        )

    is_valid, error_message, row_count = DatasetService.validate_csv_file(file_content)

    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_message)

    file_hash = DatasetService.calculate_file_hash(file_content)
    existing_dataset = DatasetService.get_dataset_by_file_hash(
        db,
        file_hash=file_hash,
        statuses={"processing", "ready"},
    )
    if existing_dataset:
        message = (
            "This dataset is already being processed. Reusing the existing upload."
            if existing_dataset.status == "processing"
            else "This dataset is already ready. Reusing the existing processed dataset."
        )
        if response is not None and existing_dataset.status == "ready":
            response.status_code = status.HTTP_200_OK

        logger.info(
            "Reused existing dataset %s for upload request by user %s",
            existing_dataset.id,
            current_user.email,
        )

        return DatasetUploadResponse(
            id=existing_dataset.id,
            filename=existing_dataset.filename,
            status=existing_dataset.status,
            message=message,
            uploaded_at=existing_dataset.uploaded_at,
        )

    dataset = DatasetService.create_dataset(
        db=db,
        user_id=current_user.id,
        filename=file.filename,
        record_count=row_count,
        status="processing",
        file_hash=file_hash,
    )

    file_content_base64 = base64.b64encode(file_content).decode("utf-8")

    try:
        process_csv_file.delay(str(dataset.id), file_content_base64)
        logger.info(f"Queued processing job for dataset {dataset.id}")
    except Exception as e:
        logger.error(f"Failed to queue processing job for dataset {dataset.id}: {e}")

        DatasetService.update_dataset_status(
            db,
            dataset.id,
            status="failed",
            validation_errors={"error": "Failed to queue processing job"},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to queue dataset processing job",
        )

    return DatasetUploadResponse(
        id=dataset.id,
        filename=dataset.filename,
        status=dataset.status,
        message="Dataset upload accepted for processing",
        uploaded_at=dataset.uploaded_at,
    )


@router.get(
    "/{dataset_id}/progress",
    response_model=DatasetProgressResponse,
    responses={
        200: {"description": "Dataset processing progress"},
        404: {"description": "Dataset not found"},
        403: {"description": "Access denied"},
    },
)
async def get_dataset_progress(
    dataset_id: str,
    current_user: Annotated[UserResponse, Depends(require_any_authenticated_user)],
    db: Session = Depends(get_db),
):
    """Get real-time processing progress for a dataset"""
    from uuid import UUID
    import json

    try:
        dataset_uuid = UUID(dataset_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid dataset ID format"
        )

    # Check dataset exists and user has access
    dataset = db.query(Dataset).filter(Dataset.id == dataset_uuid).first()
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )

    # Get progress from Redis
    try:
        from backend.infrastructure.cache import cache_client
        
        progress_key = f"dataset:progress:{dataset_id}"
        logger.info(f"Fetching progress for dataset {dataset_id} from Redis key: {progress_key}")
        
        progress = cache_client.get_json(progress_key)

        if progress:
            logger.info(f"Progress found for dataset {dataset_id}: {progress}")
            return DatasetProgressResponse(**progress)
        else:
            logger.info(f"No progress data found in Redis for dataset {dataset_id}")
    except Exception as e:
        logger.error(f"Failed to fetch progress from Redis for dataset {dataset_id}: {e}", exc_info=True)
        # Fall through to default response

    # No progress data in Redis - fall back to DB status
    logger.info(f"Returning fallback progress for dataset {dataset_id}, DB status: {dataset.status}")
    
    # Map DB statuses to the status names the frontend expects
    # DB uses 'ready' but frontend expects 'completed'
    if dataset.status == "processing":
        return DatasetProgressResponse(
            status="processing",
            progress=0,
            total_records=dataset.record_count or 0,
            processed_records=0,
            current_step="Initializing...",
        )
    
    if dataset.status == "ready":
        return DatasetProgressResponse(
            status="completed",
            progress=100,
            total_records=dataset.record_count or 0,
            processed_records=dataset.record_count or 0,
            current_step="Complete",
        )
    
    if dataset.status == "failed":
        error_msg = None
        if dataset.validation_errors and isinstance(dataset.validation_errors, dict):
            error_msg = dataset.validation_errors.get("error") or dataset.validation_errors.get("duplicates")
        return DatasetProgressResponse(
            status="failed",
            progress=100,
            total_records=dataset.record_count or 0,
            processed_records=0,
            current_step="Failed",
            error=error_msg or "Processing failed",
        )
    
    return DatasetProgressResponse(
        status=dataset.status,
        progress=0,
        total_records=dataset.record_count or 0,
        processed_records=0,
        current_step=dataset.status.capitalize() if dataset.status else "Unknown",
    )


@router.get(
    "",
    response_model=DatasetListResponse,
    responses={
        200: {"description": "List of datasets"},
    },
)
async def list_datasets(
    current_user: Annotated[UserResponse, Depends(require_any_authenticated_user)],
    db: Session = Depends(get_db),
):
    datasets = db.query(Dataset).order_by(Dataset.uploaded_at.desc()).all()

    dataset_responses = [DatasetResponse.model_validate(ds) for ds in datasets]

    return DatasetListResponse(datasets=dataset_responses, total=len(dataset_responses))


@router.get(
    "/{dataset_id}",
    response_model=DatasetResponse,
    responses={
        200: {"description": "Dataset details"},
        404: {"description": "Dataset not found"},
    },
)
async def get_dataset(
    dataset_id: str,
    current_user: Annotated[UserResponse, Depends(require_any_authenticated_user)],
    db: Session = Depends(get_db),
):
    from uuid import UUID

    try:
        dataset_uuid = UUID(dataset_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")

    dataset = DatasetService.get_dataset_by_id(db, dataset_uuid)

    if not dataset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")

    return DatasetResponse.model_validate(dataset)


@router.delete(
    "/{dataset_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        204: {"description": "Dataset deleted successfully"},
        403: {"description": "Forbidden - requires Admin role"},
        404: {"description": "Dataset not found"},
    },
)
async def delete_dataset(
    dataset_id: str,
    current_user: Annotated[UserResponse, Depends(require_admin)],
    db: Session = Depends(get_db),
):
    from uuid import UUID

    from backend.domain.models.model_version import ModelVersion

    try:
        dataset_uuid = UUID(dataset_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")

    dataset = DatasetService.get_dataset_by_id(db, dataset_uuid)

    if not dataset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")

    artifact_paths = [
        artifact_path
        for (artifact_path,) in (
            db.query(ModelVersion.artifact_path)
            .filter(
                ModelVersion.dataset_id == dataset_uuid,
                ModelVersion.artifact_path.isnot(None),
            )
            .all()
        )
        if artifact_path
    ]

    db.delete(dataset)
    db.commit()

    try:
        from backend.infrastructure.cache import cache_client
        from backend.services.dashboard_service import DashboardService
        from backend.infrastructure.storage import storage_client

        for artifact_path in artifact_paths:
            try:
                storage_client.delete_artifact(artifact_path)
            except Exception as storage_error:
                logger.warning(
                    "Failed to delete model artifact %s during dataset cleanup: %s",
                    artifact_path,
                    storage_error,
                )

        if cache_client.is_available and cache_client.redis_client:
            DashboardService.invalidate_cache(cache_client.redis_client)
    except Exception as cache_error:
        logger.warning(f"Failed to invalidate dashboard cache after dataset delete: {cache_error}")

    logger.info(f"Deleted dataset {dataset_id} by user {current_user.email}")

    return None


@router.get(
    "/{dataset_id}/records",
    response_model=dict,
    responses={
        200: {"description": "Paginated dataset records"},
        404: {"description": "Dataset not found"},
        400: {"description": "Invalid pagination parameters"},
    },
)
async def get_dataset_records(
    dataset_id: str,
    page: int = 1,
    page_size: int = 50,
    current_user: Annotated[UserResponse, Depends(require_any_authenticated_user)] = None,
    db: Session = Depends(get_db),
):
    from uuid import UUID

    from backend.domain.models.customer_record import CustomerRecord

    if page < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Page number must be >= 1"
        )

    if page_size < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Page size must be >= 1"
        )

    if page_size > 1000:
        page_size = 1000

    try:
        dataset_uuid = UUID(dataset_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")

    dataset = DatasetService.get_dataset_by_id(db, dataset_uuid)

    if not dataset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")

    total_count = db.query(CustomerRecord).filter(CustomerRecord.dataset_id == dataset_uuid).count()

    offset = (page - 1) * page_size
    total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 0

    records = (
        db.query(CustomerRecord)
        .filter(CustomerRecord.dataset_id == dataset_uuid)
        .offset(offset)
        .limit(page_size)
        .all()
    )

    records_data = []
    for record in records:
        record_dict = {
            "id": str(record.id),
            "dataset_id": str(record.dataset_id),
            "gender": record.gender,
            "senior_citizen": record.senior_citizen,
            "partner": record.partner,
            "dependents": record.dependents,
            "tenure": record.tenure,
            "phone_service": record.phone_service,
            "multiple_lines": record.multiple_lines,
            "internet_service": record.internet_service,
            "online_security": record.online_security,
            "online_backup": record.online_backup,
            "device_protection": record.device_protection,
            "tech_support": record.tech_support,
            "streaming_tv": record.streaming_tv,
            "streaming_movies": record.streaming_movies,
            "contract": record.contract,
            "paperless_billing": record.paperless_billing,
            "monthly_charges": record.monthly_charges,
            "total_charges": record.total_charges,
            "churn": record.churn,
            "created_at": record.created_at.isoformat() if record.created_at else None,
        }
        records_data.append(record_dict)

    return {
        "records": records_data,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total_records": total_count,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_previous": page > 1,
        },
    }


@router.get(
    "/{dataset_id}/quality",
    response_model=dict,
    responses={
        200: {"description": "Data quality report"},
        404: {"description": "Dataset not found"},
    },
)
async def get_dataset_quality(
    dataset_id: str,
    current_user: Annotated[UserResponse, Depends(require_any_authenticated_user)],
    db: Session = Depends(get_db),
):
    from uuid import UUID

    from backend.services.data_quality_service import DataQualityService

    try:
        dataset_uuid = UUID(dataset_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")

    dataset = DatasetService.get_dataset_by_id(db, dataset_uuid)

    if not dataset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")

    try:
        quality_report = DataQualityService.analyze_data_quality(db, dataset_uuid)
        return quality_report
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/{dataset_id}/statistics",
    response_model=dict,
    responses={
        200: {"description": "Descriptive statistics"},
        404: {"description": "Dataset not found"},
    },
)
async def get_dataset_statistics(
    dataset_id: str,
    current_user: Annotated[UserResponse, Depends(require_any_authenticated_user)],
    db: Session = Depends(get_db),
):
    from collections import Counter
    from uuid import UUID

    import numpy as np

    from backend.domain.models.customer_record import CustomerRecord

    try:
        dataset_uuid = UUID(dataset_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")

    dataset = DatasetService.get_dataset_by_id(db, dataset_uuid)

    if not dataset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")

    records = db.query(CustomerRecord).filter(CustomerRecord.dataset_id == dataset_uuid).all()

    if not records:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No customer records found for dataset"
        )

    numeric_columns = ["tenure", "monthly_charges", "total_charges"]
    numeric_stats = {}

    for column in numeric_columns:
        values = []
        for record in records:
            value = getattr(record, column, None)
            if value is not None:
                try:
                    values.append(float(value))
                except (ValueError, TypeError):
                    continue

        if values:
            values_array = np.array(values)
            numeric_stats[column] = {
                "count": len(values),
                "mean": round(float(np.mean(values_array)), 2),
                "median": round(float(np.median(values_array)), 2),
                "std": round(float(np.std(values_array)), 2),
                "min": round(float(np.min(values_array)), 2),
                "max": round(float(np.max(values_array)), 2),
                "q1": round(float(np.percentile(values_array, 25)), 2),
                "q3": round(float(np.percentile(values_array, 75)), 2),
            }
        else:
            numeric_stats[column] = {
                "count": 0,
                "mean": None,
                "median": None,
                "std": None,
                "min": None,
                "max": None,
                "q1": None,
                "q3": None,
            }

    categorical_columns = [
        "gender",
        "partner",
        "dependents",
        "phone_service",
        "multiple_lines",
        "internet_service",
        "online_security",
        "online_backup",
        "device_protection",
        "tech_support",
        "streaming_tv",
        "streaming_movies",
        "contract",
        "paperless_billing",
    ]
    categorical_stats = {}

    for column in categorical_columns:
        values = []
        for record in records:
            value = getattr(record, column, None)
            if value is not None:
                values.append(value)

        if values:
            value_counts = Counter(values)
            categorical_stats[column] = {
                "count": len(values),
                "unique_values": len(value_counts),
                "value_counts": dict(value_counts.most_common()),
            }
        else:
            categorical_stats[column] = {"count": 0, "unique_values": 0, "value_counts": {}}

    return {
        "dataset_id": str(dataset_uuid),
        "total_records": len(records),
        "numeric_statistics": numeric_stats,
        "categorical_statistics": categorical_stats,
    }
