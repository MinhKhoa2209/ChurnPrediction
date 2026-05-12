import io
import logging
import time
from datetime import datetime
from typing import Annotated
from uuid import UUID, uuid4

import pandas as pd
import redis
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.api.dependencies import (
    require_any_authenticated_user,
)
from backend.api.middleware import get_redis_client
from backend.domain.schemas.auth import UserResponse
from backend.domain.schemas.prediction import (
    BatchPredictionResult,
    BatchPredictionResultsResponse,
    BatchPredictionUploadResponse,
    PaginationMetadata,
    PredictionResponse,
    SinglePredictionRequest,
)
from backend.infrastructure.database import get_db
from backend.infrastructure.storage import storage_client
from backend.services.prediction_service import (
    ModelNotFoundError,
    PredictionPreprocessingError,
    PredictionService,
    PredictionServiceError,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/predictions", tags=["Predictions"])


@router.post(
    "/single",
    status_code=status.HTTP_200_OK,
    response_model=PredictionResponse,
    responses={
        200: {"description": "Prediction created successfully"},
        400: {"description": "Invalid input data or model version"},
        404: {"description": "Model version not found"},
        500: {"description": "Internal server error during prediction"},
    },
)
async def create_single_prediction(
    request: SinglePredictionRequest,
    current_user: Annotated[UserResponse, Depends(require_any_authenticated_user)],
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis_client),
):
    try:
        try:
            model_version_id = UUID(request.model_version_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid model_version_id format: {request.model_version_id}",
            )

        input_data = request.input.model_dump()

        prediction_service = PredictionService(redis_client=redis_client)

        prediction = prediction_service.generate_prediction(
            db=db,
            user_id=UUID(current_user.id),
            model_version_id=model_version_id,
            input_data=input_data,
            store_prediction=True,
        )

        response = PredictionResponse(
            id=str(prediction.id),
            model_version_id=str(prediction.model_version_id),
            probability=prediction.probability,
            threshold=prediction.threshold,
            prediction="Churn" if prediction.prediction else "No Churn",
            shap_values=prediction.shap_values,
            created_at=prediction.created_at.isoformat(),
        )

        try:
            from backend.services.dashboard_service import DashboardService

            DashboardService.invalidate_cache(redis_client, UUID(current_user.id))
        except Exception as cache_error:
            logger.warning(
                f"Failed to invalidate dashboard cache for user {current_user.id}: {cache_error}"
            )

        logger.info(
            f"User {current_user.id} created prediction {prediction.id} "
            f"with model {model_version_id}: probability={prediction.probability:.4f}"
        )

        return response

    except ModelNotFoundError as e:
        logger.warning(f"Model not found: {e}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    except PredictionPreprocessingError as e:
        logger.warning(f"Preprocessing error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Preprocessing failed: {str(e)}"
        )

    except PredictionServiceError as e:
        logger.error(f"Prediction service error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Prediction failed: {str(e)}"
        )

    except Exception as e:
        logger.error(f"Unexpected error in single prediction: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during prediction",
        )


@router.post(
    "/batch",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=BatchPredictionUploadResponse,
    responses={
        202: {"description": "Batch prediction job created and queued"},
        400: {"description": "Invalid file format or validation error"},
        404: {"description": "Model version not found"},
        413: {"description": "File too large - maximum 50MB"},
    },
)
async def create_batch_prediction(
    model_version_id: str,
    file: UploadFile = File(
        ..., description="CSV file containing customer data for batch prediction"
    ),
    current_user: Annotated[UserResponse, Depends(require_any_authenticated_user)] = None,
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis_client),
):
    start_time = time.time()

    if not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only CSV files are accepted.",
        )

    file_content = await file.read()

    MAX_FILE_SIZE = 50 * 1024 * 1024
    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size is 50MB. Uploaded file is {len(file_content) / (1024 * 1024):.2f}MB.",
        )

    try:
        model_version_uuid = UUID(model_version_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid model_version_id format: {model_version_id}",
        )

    from backend.domain.models.model_version import ModelVersion

    model_version = db.query(ModelVersion).filter(ModelVersion.id == model_version_uuid).first()

    if not model_version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model version {model_version_id} not found",
        )

    if model_version.status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Model version {model_version_id} is {model_version.status} and cannot be used for predictions",
        )

    try:
        df = pd.read_csv(io.BytesIO(file_content))

        required_columns = [
            "gender",
            "SeniorCitizen",
            "Partner",
            "Dependents",
            "tenure",
            "PhoneService",
            "MultipleLines",
            "InternetService",
            "OnlineSecurity",
            "OnlineBackup",
            "DeviceProtection",
            "TechSupport",
            "StreamingTV",
            "StreamingMovies",
            "Contract",
            "PaperlessBilling",
            "PaymentMethod",
            "MonthlyCharges",
            "TotalCharges",
        ]

        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing required columns: {', '.join(missing_columns)}",
            )

        if len(df) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CSV file is empty. Please provide at least one customer record.",
            )

        record_count = len(df)

        df_clean = df[required_columns].dropna(how="all")

        if len(df_clean) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CSV file contains no valid records. All rows are empty.",
            )

        if len(df_clean) < record_count:
            logger.warning(
                f"Removed {record_count - len(df_clean)} empty rows from batch upload. "
                f"Processing {len(df_clean)} valid records."
            )
            record_count = len(df_clean)

    except pd.errors.EmptyDataError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="CSV file is empty or invalid."
        )
    except pd.errors.ParserError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failed to parse CSV file: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error parsing CSV: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failed to parse CSV file: {str(e)}"
        )

    validation_time = time.time() - start_time
    if validation_time > 1.0:
        logger.warning(
            f"CSV validation took {validation_time:.2f}s, exceeding 1 second target "
            f"for {record_count} records"
        )

    batch_id = uuid4()

    from backend.workers.prediction_tasks import process_batch_prediction

    task = process_batch_prediction.delay(
        batch_id=str(batch_id),
        model_version_id=model_version_id,
        user_id=current_user.id,
        csv_data=file_content,
    )

    logger.info(
        f"User {current_user.id} uploaded batch prediction CSV: "
        f"batch_id={batch_id}, model={model_version_id}, records={record_count}, "
        f"validation_time={validation_time:.3f}s, task_id={task.id}"
    )

    return BatchPredictionUploadResponse(
        batch_id=str(batch_id),
        model_version_id=model_version_id,
        record_count=record_count,
        status="queued",
        message=f"Batch prediction job queued for processing. {record_count} records will be processed.",
        created_at=datetime.utcnow().isoformat() + "Z",
    )


@router.get(
    "",
    responses={
        200: {"description": "List of predictions"},
    },
)
async def list_predictions(
    current_user: Annotated[UserResponse, Depends(require_any_authenticated_user)],
    db: Session = Depends(get_db),
):
    return {
        "message": "List predictions endpoint",
        "user": current_user.email,
        "role": current_user.role,
    }


@router.get(
    "/{prediction_id}",
    responses={
        200: {"description": "Prediction details"},
        404: {"description": "Prediction not found"},
    },
)
async def get_prediction(
    prediction_id: str,
    current_user: Annotated[UserResponse, Depends(require_any_authenticated_user)],
    db: Session = Depends(get_db),
):
    return {
        "message": f"Get prediction {prediction_id}",
        "user": current_user.email,
        "role": current_user.role,
    }


@router.get(
    "/batch/{batch_id}",
    status_code=status.HTTP_200_OK,
    response_model=BatchPredictionResultsResponse,
    responses={
        200: {"description": "Batch prediction results retrieved successfully"},
        404: {"description": "Batch not found"},
    },
)
async def get_batch_results(
    batch_id: str,
    page: int = 1,
    page_size: int = 50,
    current_user: Annotated[UserResponse, Depends(require_any_authenticated_user)] = None,
    db: Session = Depends(get_db),
):
    from math import ceil

    from backend.domain.models.prediction import Prediction

    try:
        batch_uuid = UUID(batch_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid batch_id format: {batch_id}"
        )

    if page < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Page number must be >= 1"
        )

    if page_size < 1 or page_size > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Page size must be between 1 and 100"
        )

    total_count = (
        db.query(Prediction)
        .filter(Prediction.batch_id == batch_uuid, Prediction.user_id == UUID(current_user.id))
        .count()
    )

    if total_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch {batch_id} not found or you don't have access to it",
        )

    first_prediction = db.query(Prediction).filter(Prediction.batch_id == batch_uuid).first()

    total_pages = ceil(total_count / page_size)
    offset = (page - 1) * page_size

    predictions = (
        db.query(Prediction)
        .filter(Prediction.batch_id == batch_uuid, Prediction.user_id == UUID(current_user.id))
        .order_by(Prediction.created_at.asc())
        .offset(offset)
        .limit(page_size)
        .all()
    )

    prediction_results = [
        BatchPredictionResult(
            id=str(pred.id),
            probability=pred.probability,
            prediction="Churn" if pred.prediction else "No Churn",
            input_features=pred.input_features,
            created_at=pred.created_at.isoformat(),
        )
        for pred in predictions
    ]

    batch_status = "completed"

    response = BatchPredictionResultsResponse(
        batch_id=batch_id,
        model_version_id=str(first_prediction.model_version_id),
        status=batch_status,
        record_count=total_count,
        created_at=first_prediction.created_at.isoformat(),
        predictions=prediction_results,
        pagination=PaginationMetadata(
            total=total_count, page=page, page_size=page_size, total_pages=total_pages
        ),
    )

    logger.info(
        f"User {current_user.id} retrieved batch {batch_id} results: "
        f"page={page}, page_size={page_size}, total={total_count}"
    )

    return response


@router.get(
    "/batch/{batch_id}/export",
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "CSV file download", "content": {"text/csv": {}}},
        404: {"description": "Batch not found"},
    },
)
async def export_batch_results(
    batch_id: str,
    current_user: Annotated[UserResponse, Depends(require_any_authenticated_user)] = None,
    db: Session = Depends(get_db),
):
    from backend.domain.models.prediction import Prediction
    from backend.utils.csv_printer import CSVPrettyPrinter

    start_time = time.time()

    try:
        batch_uuid = UUID(batch_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid batch_id format: {batch_id}"
        )

    predictions = (
        db.query(Prediction)
        .filter(Prediction.batch_id == batch_uuid, Prediction.user_id == UUID(current_user.id))
        .order_by(Prediction.created_at.asc())
        .all()
    )

    if not predictions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch {batch_id} not found or you don't have access to it",
        )

    records = []
    for pred in predictions:
        record = pred.input_features.copy()
        record["Churn_Probability"] = pred.probability
        record["Churn_Prediction"] = "Yes" if pred.prediction else "No"
        records.append(record)

    csv_printer = CSVPrettyPrinter()
    csv_content = csv_printer.format(records, include_probability=True)

    try:
        csv_bytes = csv_content.encode("utf-8")
        s3_key = storage_client.upload_batch_export(
            user_id=UUID(current_user.id), batch_id=batch_uuid, csv_data=csv_bytes
        )
        logger.info(f"Stored batch export in R2: {s3_key}")
    except Exception as e:
        logger.error(f"Failed to store batch export in R2: {e}", exc_info=True)

    elapsed_time = time.time() - start_time
    if elapsed_time > 3.0:
        logger.warning(
            f"CSV export for batch {batch_id} took {elapsed_time:.2f}s, "
            f"exceeding 3-second target for {len(predictions)} records"
        )

    logger.info(
        f"User {current_user.id} exported batch {batch_id} results: "
        f"{len(predictions)} predictions in {elapsed_time:.2f}s"
    )

    return StreamingResponse(
        io.BytesIO(csv_content.encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=batch_predictions_{batch_id}.csv"},
    )
