"""
Prediction API Routes

This module provides REST API endpoints for predictions with RBAC.
"""

import io
import logging
import time
from typing import Annotated
from uuid import UUID, uuid4
from datetime import datetime

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import redis
import pandas as pd  # Still needed for batch upload validation

from backend.api.dependencies import (
    get_current_user,
    require_any_authenticated_user,
)
from backend.api.middleware import get_redis_client
from backend.domain.schemas.auth import UserResponse
from backend.domain.schemas.prediction import (
    SinglePredictionRequest,
    PredictionResponse,
    BatchPredictionUploadResponse,
    BatchPredictionResultsResponse,
    BatchPredictionResult,
    PaginationMetadata,
)
from backend.infrastructure.database import get_db
from backend.services.prediction_service import (
    PredictionService,
    ModelNotFoundError,
    PredictionServiceError,
    PredictionPreprocessingError,
)
from backend.infrastructure.storage import storage_client

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
    }
)
async def create_single_prediction(
    request: SinglePredictionRequest,
    # Requirement 12.1: All authenticated users can make predictions
    # Requirement 19.4: Analyst role can generate predictions
    current_user: Annotated[UserResponse, Depends(require_any_authenticated_user)],
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis_client)
):
    """
    Create a single customer churn prediction
    
    **Authorization**: Requires any authenticated user
    
    **RBAC Matrix**:
    - Admin: ✓ Allowed
    - Data_Scientist: ✓ Allowed
    - Analyst: ✓ Allowed
    
    **Requirements**:
    - 12.1: Provides form accepting all customer feature inputs
    - 12.2: Validates all required fields are present
    - 12.3: Returns descriptive error messages within 100ms
    - 12.4: Preprocesses input data using stored preprocessing parameters
    - 12.5: Generates prediction using selected model version
    - 12.6: Returns prediction probability (0.0 to 1.0) within 200ms
    - 12.7: Displays probability as percentage with color coding
    - 12.8: Displays feature contributions using SHAP values
    
    **Color Coding**:
    - Green: probability < 30% (low churn risk)
    - Yellow: 30% ≤ probability < 70% (medium churn risk)
    - Red: probability ≥ 70% (high churn risk)
    
    Args:
        request: Prediction request with model_version_id and customer input features
        current_user: Current authenticated user
        db: Database session
        redis_client: Redis client for caching
        
    Returns:
        Prediction result with probability, binary prediction, SHAP values, and threshold
        
    Raises:
        HTTPException: 400 if validation fails, 404 if model not found, 500 if prediction fails
    """
    try:
        # Parse model_version_id
        try:
            model_version_id = UUID(request.model_version_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid model_version_id format: {request.model_version_id}"
            )
        
        # Convert Pydantic model to dict for service layer
        input_data = request.input.model_dump()
        
        # Initialize prediction service with Redis caching
        prediction_service = PredictionService(redis_client=redis_client)
        
        # Generate prediction
        prediction = prediction_service.generate_prediction(
            db=db,
            user_id=UUID(current_user.id),
            model_version_id=model_version_id,
            input_data=input_data,
            store_prediction=True
        )
        
        # Convert to response schema
        response = PredictionResponse(
            id=str(prediction.id),
            model_version_id=str(prediction.model_version_id),
            probability=prediction.probability,
            threshold=prediction.threshold,
            prediction="Churn" if prediction.prediction else "No Churn",
            shap_values=prediction.shap_values,
            created_at=prediction.created_at.isoformat()
        )
        
        logger.info(
            f"User {current_user.id} created prediction {prediction.id} "
            f"with model {model_version_id}: probability={prediction.probability:.4f}"
        )
        
        return response
        
    except ModelNotFoundError as e:
        logger.warning(f"Model not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    
    except PredictionPreprocessingError as e:
        logger.warning(f"Preprocessing error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Preprocessing failed: {str(e)}"
        )
    
    except PredictionServiceError as e:
        logger.error(f"Prediction service error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {str(e)}"
        )
    
    except Exception as e:
        logger.error(f"Unexpected error in single prediction: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during prediction"
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
    }
)
async def create_batch_prediction(
    model_version_id: str,
    file: UploadFile = File(..., description="CSV file containing customer data for batch prediction"),
    # Requirement 19.4: All roles can create batch predictions
    current_user: Annotated[UserResponse, Depends(require_any_authenticated_user)] = None,
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis_client)
):
    """
    Create a batch prediction job from CSV file upload
    
    **Authorization**: Requires any authenticated user
    
    **RBAC Matrix**:
    - Admin: ✓ Allowed
    - Data_Scientist: ✓ Allowed
    - Analyst: ✓ Allowed
    
    **Requirements**:
    - 13.1: Accept CSV file uploads containing customer data for batch prediction
    - 13.2: Validate file format within 1 second
    
    **File Requirements**:
    - Format: CSV (UTF-8 encoded)
    - Maximum size: 50MB
    - Required columns: All customer features (same as single prediction)
      - gender, SeniorCitizen, Partner, Dependents, tenure
      - PhoneService, MultipleLines
      - InternetService, OnlineSecurity, OnlineBackup, DeviceProtection, TechSupport, StreamingTV, StreamingMovies
      - Contract, PaperlessBilling, PaymentMethod
      - MonthlyCharges, TotalCharges
    
    Args:
        model_version_id: UUID of the model version to use for predictions
        file: Uploaded CSV file with customer data
        current_user: Current authenticated user
        db: Database session
        redis_client: Redis client for caching
        
    Returns:
        Batch prediction job details with batch_id and status
        
    Raises:
        HTTPException: If file is invalid, too large, model not found, or validation fails
    """
    start_time = time.time()
    
    # Validate file type
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only CSV files are accepted."
        )
    
    # Read file content
    file_content = await file.read()
    
    # Check file size (Requirement 13.1: max 50MB, same as dataset upload)
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size is 50MB. Uploaded file is {len(file_content) / (1024 * 1024):.2f}MB."
        )
    
    # Parse model_version_id
    try:
        model_version_uuid = UUID(model_version_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid model_version_id format: {model_version_id}"
        )
    
    # Verify model version exists and is active
    from backend.domain.models.model_version import ModelVersion
    model_version = db.query(ModelVersion).filter(
        ModelVersion.id == model_version_uuid
    ).first()
    
    if not model_version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model version {model_version_id} not found"
        )
    
    if model_version.status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Model version {model_version_id} is {model_version.status} and cannot be used for predictions"
        )
    
    # Validate CSV format and required columns (Requirement 13.2: within 1 second)
    try:
        # Parse CSV
        df = pd.read_csv(io.BytesIO(file_content))
        
        # Required columns for prediction (same as PredictionInput schema)
        required_columns = [
            'gender', 'SeniorCitizen', 'Partner', 'Dependents', 'tenure',
            'PhoneService', 'MultipleLines',
            'InternetService', 'OnlineSecurity', 'OnlineBackup', 'DeviceProtection',
            'TechSupport', 'StreamingTV', 'StreamingMovies',
            'Contract', 'PaperlessBilling', 'PaymentMethod',
            'MonthlyCharges', 'TotalCharges'
        ]
        
        # Check for missing columns
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing required columns: {', '.join(missing_columns)}"
            )
        
        # Check for empty dataframe
        if len(df) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CSV file is empty. Please provide at least one customer record."
            )
        
        record_count = len(df)
        
        # Basic validation: check for completely empty rows
        # Remove rows where all required columns are NaN
        df_clean = df[required_columns].dropna(how='all')
        
        if len(df_clean) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CSV file contains no valid records. All rows are empty."
            )
        
        if len(df_clean) < record_count:
            logger.warning(
                f"Removed {record_count - len(df_clean)} empty rows from batch upload. "
                f"Processing {len(df_clean)} valid records."
            )
            record_count = len(df_clean)
        
    except pd.errors.EmptyDataError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CSV file is empty or invalid."
        )
    except pd.errors.ParserError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to parse CSV file: {str(e)}"
        )
    except HTTPException:
        # Re-raise HTTPExceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected error parsing CSV: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to parse CSV file: {str(e)}"
        )
    
    # Check validation time (Requirement 13.2: within 1 second)
    validation_time = time.time() - start_time
    if validation_time > 1.0:
        logger.warning(
            f"CSV validation took {validation_time:.2f}s, exceeding 1 second target "
            f"for {record_count} records"
        )
    
    # Generate batch_id
    batch_id = uuid4()
    
    # Queue background job for batch prediction processing (Requirement 13.3, 13.4)
    from backend.workers.prediction_tasks import process_batch_prediction
    
    # Queue the Celery task with CSV data
    task = process_batch_prediction.delay(
        batch_id=str(batch_id),
        model_version_id=model_version_id,
        user_id=current_user.id,
        csv_data=file_content
    )
    
    logger.info(
        f"User {current_user.id} uploaded batch prediction CSV: "
        f"batch_id={batch_id}, model={model_version_id}, records={record_count}, "
        f"validation_time={validation_time:.3f}s, task_id={task.id}"
    )
    
    # Return 202 Accepted with batch details
    return BatchPredictionUploadResponse(
        batch_id=str(batch_id),
        model_version_id=model_version_id,
        record_count=record_count,
        status="queued",
        message=f"Batch prediction job queued for processing. {record_count} records will be processed.",
        created_at=datetime.utcnow().isoformat() + "Z"
    )


@router.get(
    "",
    responses={
        200: {"description": "List of predictions"},
    }
)
async def list_predictions(
    current_user: Annotated[UserResponse, Depends(require_any_authenticated_user)],
    db: Session = Depends(get_db)
):
    """
    List all predictions for the current user
    
    **Authorization**: Requires any authenticated user
    
    **RBAC Matrix**:
    - Admin: ✓ Allowed (can see all predictions)
    - Data_Scientist: ✓ Allowed (can see own predictions)
    - Analyst: ✓ Allowed (can see own predictions)
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of predictions
    """
    # TODO: Implement prediction listing with user scoping
    return {
        "message": "List predictions endpoint",
        "user": current_user.email,
        "role": current_user.role
    }


@router.get(
    "/{prediction_id}",
    responses={
        200: {"description": "Prediction details"},
        404: {"description": "Prediction not found"},
    }
)
async def get_prediction(
    prediction_id: str,
    current_user: Annotated[UserResponse, Depends(require_any_authenticated_user)],
    db: Session = Depends(get_db)
):
    """
    Get prediction details
    
    **Authorization**: Requires any authenticated user
    
    **RBAC Matrix**:
    - Admin: ✓ Allowed
    - Data_Scientist: ✓ Allowed
    - Analyst: ✓ Allowed
    
    Args:
        prediction_id: Prediction UUID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Prediction details
    """
    # TODO: Implement prediction retrieval with ownership check
    return {
        "message": f"Get prediction {prediction_id}",
        "user": current_user.email,
        "role": current_user.role
    }


@router.get(
    "/batch/{batch_id}",
    status_code=status.HTTP_200_OK,
    response_model=BatchPredictionResultsResponse,
    responses={
        200: {"description": "Batch prediction results retrieved successfully"},
        404: {"description": "Batch not found"},
    }
)
async def get_batch_results(
    batch_id: str,
    page: int = 1,
    page_size: int = 50,
    current_user: Annotated[UserResponse, Depends(require_any_authenticated_user)] = None,
    db: Session = Depends(get_db)
):
    """
    Get batch prediction results with pagination
    
    **Authorization**: Requires any authenticated user
    
    **RBAC Matrix**:
    - Admin: ✓ Allowed
    - Data_Scientist: ✓ Allowed
    - Analyst: ✓ Allowed
    
    **Requirements**:
    - 13.5: Store batch predictions in database
    - 13.6: Display batch prediction results in paginated table with 50 rows per page
    
    Args:
        batch_id: Unique batch identifier
        page: Page number (1-indexed, default: 1)
        page_size: Number of items per page (default: 50, max: 100)
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Batch metadata and paginated prediction results
        
    Raises:
        HTTPException: 404 if batch not found
    """
    from backend.domain.models.prediction import Prediction
    from math import ceil
    
    # Validate and parse batch_id
    try:
        batch_uuid = UUID(batch_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid batch_id format: {batch_id}"
        )
    
    # Validate pagination parameters
    if page < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page number must be >= 1"
        )
    
    if page_size < 1 or page_size > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page size must be between 1 and 100"
        )
    
    # Query batch predictions
    # First, check if batch exists and get total count
    total_count = db.query(Prediction).filter(
        Prediction.batch_id == batch_uuid,
        Prediction.user_id == UUID(current_user.id)
    ).count()
    
    if total_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch {batch_id} not found or you don't have access to it"
        )
    
    # Get first prediction to extract batch metadata
    first_prediction = db.query(Prediction).filter(
        Prediction.batch_id == batch_uuid
    ).first()
    
    # Calculate pagination
    total_pages = ceil(total_count / page_size)
    offset = (page - 1) * page_size
    
    # Query paginated predictions
    predictions = db.query(Prediction).filter(
        Prediction.batch_id == batch_uuid,
        Prediction.user_id == UUID(current_user.id)
    ).order_by(
        Prediction.created_at.asc()
    ).offset(offset).limit(page_size).all()
    
    # Convert to response format
    prediction_results = [
        BatchPredictionResult(
            id=str(pred.id),
            probability=pred.probability,
            prediction="Churn" if pred.prediction else "No Churn",
            input_features=pred.input_features,
            created_at=pred.created_at.isoformat()
        )
        for pred in predictions
    ]
    
    # Determine batch status based on record count
    # If we have predictions, the batch is completed
    # (The Celery worker would have created all predictions)
    batch_status = "completed"
    
    response = BatchPredictionResultsResponse(
        batch_id=batch_id,
        model_version_id=str(first_prediction.model_version_id),
        status=batch_status,
        record_count=total_count,
        created_at=first_prediction.created_at.isoformat(),
        predictions=prediction_results,
        pagination=PaginationMetadata(
            total=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
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
        200: {
            "description": "CSV file download",
            "content": {"text/csv": {}}
        },
        404: {"description": "Batch not found"},
    }
)
async def export_batch_results(
    batch_id: str,
    current_user: Annotated[UserResponse, Depends(require_any_authenticated_user)] = None,
    db: Session = Depends(get_db)
):
    """
    Export batch prediction results as CSV file
    
    **Authorization**: Requires any authenticated user
    
    **RBAC Matrix**:
    - Admin: ✓ Allowed
    - Data_Scientist: ✓ Allowed
    - Analyst: ✓ Allowed
    
    **Requirements**:
    - 13.7: Allow users to download batch prediction results as CSV file
    - 14.1: Format customer records and predictions into CSV format
    - 14.2: Include all original columns plus Churn_Probability column
    - 14.3: Format numeric values with 2 decimal places
    - 14.4: Escape special characters according to RFC 4180
    - 14.5: Generate CSV file within 3 seconds for 10,000 records
    - 14.6: Trigger browser download of CSV file
    
    Args:
        batch_id: Unique batch identifier
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        CSV file with all batch predictions
        
    Raises:
        HTTPException: 404 if batch not found
    """
    from backend.domain.models.prediction import Prediction
    from backend.utils.csv_printer import CSVPrettyPrinter
    
    start_time = time.time()
    
    # Validate and parse batch_id
    try:
        batch_uuid = UUID(batch_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid batch_id format: {batch_id}"
        )
    
    # Query all batch predictions
    predictions = db.query(Prediction).filter(
        Prediction.batch_id == batch_uuid,
        Prediction.user_id == UUID(current_user.id)
    ).order_by(
        Prediction.created_at.asc()
    ).all()
    
    if not predictions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch {batch_id} not found or you don't have access to it"
        )
    
    # Convert predictions to list of dictionaries for CSV Pretty Printer
    # Requirement 14.1: Format Customer_Records and Predictions into CSV format
    # Requirement 14.2: Include all original columns plus Churn_Probability column
    records = []
    for pred in predictions:
        # Combine input features with prediction results
        record = pred.input_features.copy()
        record['Churn_Probability'] = pred.probability
        record['Churn_Prediction'] = "Yes" if pred.prediction else "No"
        records.append(record)
    
    # Use CSV Pretty Printer to format the CSV
    # Requirement 14.3: Format numeric values with 2 decimal places
    # Requirement 14.4: Escape special characters according to RFC 4180
    csv_printer = CSVPrettyPrinter()
    csv_content = csv_printer.format(records, include_probability=True)
    
    # Store CSV in R2 storage (Requirement 33.4)
    try:
        csv_bytes = csv_content.encode('utf-8')
        s3_key = storage_client.upload_batch_export(
            user_id=UUID(current_user.id),
            batch_id=batch_uuid,
            csv_data=csv_bytes
        )
        logger.info(f"Stored batch export in R2: {s3_key}")
    except Exception as e:
        # Log error but don't fail the request - user can still download
        logger.error(f"Failed to store batch export in R2: {e}", exc_info=True)
    
    # Check if we met the 3-second performance requirement (Requirement 14.5)
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
    
    # Return CSV as downloadable file (Requirement 14.6)
    return StreamingResponse(
        io.BytesIO(csv_content.encode('utf-8')),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=batch_predictions_{batch_id}.csv"
        }
    )

