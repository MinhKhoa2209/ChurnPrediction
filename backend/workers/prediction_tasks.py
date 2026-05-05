"""
Prediction Celery Tasks
"""

import io
import logging
import time
from uuid import UUID

import pandas as pd
from celery.exceptions import MaxRetriesExceededError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.config import settings
from backend.services.prediction_service import PredictionService
from backend.workers.celery_app import celery_app

logger = logging.getLogger(__name__)

# Create database engine for Celery workers
# Note: Using synchronous engine since Celery doesn't support async
engine = create_engine(
    settings.database_url.replace("postgresql+asyncpg://", "postgresql://"),
    pool_size=5,
    max_overflow=10
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@celery_app.task(
    name="backend.workers.prediction_tasks.process_batch_prediction",
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 2},
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True
)
def process_batch_prediction(
    self,
    batch_id: str,
    model_version_id: str,
    user_id: str,
    csv_data: bytes
) -> dict:
    """
    Background task for processing batch predictions
    
    This task reads a CSV file, generates predictions for all records,
    and stores them in the database with the batch_id.
    
    - 13.4: Complete processing within 10 seconds for 1,000 records
    - 13.5: Store batch Predictions in the Database
    
    Performance Optimization:
    - Batch database inserts (commit every 100 predictions)
    - Reuse loaded model from cache
    - Minimize SHAP computation overhead
    
    Args:
        self: Celery task instance (for progress updates and retries)
        batch_id: Batch UUID as string
        model_version_id: Model version UUID as string
        user_id: User UUID as string
        csv_data: CSV file content as bytes
        
    Returns:
        Dictionary with batch processing results
    """
    db = SessionLocal()
    start_time = time.time()
    
    try:
        batch_uuid = UUID(batch_id)
        model_version_uuid = UUID(model_version_id)
        user_uuid = UUID(user_id)
        
        # Get retry information
        retry_count = self.request.retries
        max_retries = self.max_retries
        
        logger.info(
            f"Starting batch prediction {batch_id}: model={model_version_id}, "
            f"user={user_id} (attempt {retry_count + 1}/{max_retries + 1})"
        )
        
        # Parse CSV data
        try:
            df = pd.read_csv(io.BytesIO(csv_data))
            record_count = len(df)
            logger.info(f"Parsed CSV with {record_count} records")
        except Exception as e:
            logger.error(f"Failed to parse CSV: {e}")
            raise ValueError(f"Failed to parse CSV: {str(e)}")
        
        # Required columns for prediction
        required_columns = [
            'gender', 'SeniorCitizen', 'Partner', 'Dependents', 'tenure',
            'PhoneService', 'MultipleLines',
            'InternetService', 'OnlineSecurity', 'OnlineBackup', 'DeviceProtection',
            'TechSupport', 'StreamingTV', 'StreamingMovies',
            'Contract', 'PaperlessBilling', 'PaymentMethod',
            'MonthlyCharges', 'TotalCharges'
        ]
        
        # Verify all required columns are present
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")
        
        # Initialize prediction service with Redis caching
        # This will reuse the loaded model for all predictions in the batch
        from backend.api.middleware import get_redis_client
        redis_client = get_redis_client()
        prediction_service = PredictionService(redis_client=redis_client)
        
        # Process predictions in batches for better performance
        predictions = []
        batch_size = 100  # Commit every 100 predictions
        failed_records = []
        
        for idx, row in df.iterrows():
            try:
                # Convert row to dictionary
                input_data = row[required_columns].to_dict()
                
                # Convert numeric types to Python native types
                # (pandas types can cause issues with Pydantic validation)
                for key, value in input_data.items():
                    if pd.isna(value):
                        # Skip records with missing values
                        failed_records.append({
                            "row": idx + 2,  # +2 because: +1 for header, +1 for 0-indexing
                            "error": f"Missing value in column: {key}"
                        })
                        continue
                    
                    # Convert pandas types to Python types
                    if isinstance(value, (pd.Int64Dtype, pd.Int32Dtype)):
                        input_data[key] = int(value)
                    elif isinstance(value, (pd.Float64Dtype, pd.Float32Dtype)):
                        input_data[key] = float(value)
                    elif hasattr(value, 'item'):  # numpy types
                        input_data[key] = value.item()
                
                # Generate prediction (without storing in DB yet)
                prediction = prediction_service.generate_prediction(
                    db=db,
                    user_id=user_uuid,
                    model_version_id=model_version_uuid,
                    input_data=input_data,
                    store_prediction=False  # We'll batch insert later
                )
                
                # Set batch metadata
                prediction.is_batch = True
                prediction.batch_id = batch_uuid
                
                predictions.append(prediction)
                
                # Batch commit every 100 predictions for performance
                if len(predictions) >= batch_size:
                    db.add_all(predictions)
                    db.commit()
                    logger.info(f"Committed {len(predictions)} predictions (total: {idx + 1}/{record_count})")
                    predictions = []  # Reset batch
                
            except Exception as e:
                logger.warning(f"Failed to process record {idx + 2}: {e}")
                failed_records.append({
                    "row": idx + 2,
                    "error": str(e)
                })
                continue
        
        # Commit remaining predictions
        if predictions:
            db.add_all(predictions)
            db.commit()
            logger.info(f"Committed final {len(predictions)} predictions")
        
        # Calculate processing time
        elapsed_time = time.time() - start_time
        successful_count = record_count - len(failed_records)
        
        # Check performance requirement (Requirement 13.4: 10 seconds for 1,000 records)
        expected_time = (record_count / 1000) * 10  # Scale linearly
        if elapsed_time > expected_time:
            logger.warning(
                f"Batch prediction exceeded performance target: "
                f"{elapsed_time:.2f}s for {record_count} records "
                f"(expected: {expected_time:.2f}s)"
            )
        
        logger.info(
            f"Completed batch prediction {batch_id}: "
            f"{successful_count}/{record_count} successful, "
            f"{len(failed_records)} failed, "
            f"time={elapsed_time:.2f}s"
        )
        
        return {
            "success": True,
            "batch_id": batch_id,
            "model_version_id": model_version_id,
            "total_records": record_count,
            "successful_predictions": successful_count,
            "failed_records": failed_records,
            "processing_time_seconds": elapsed_time,
            "retry_count": retry_count
        }
        
    except Exception as e:
        logger.error(
            f"Error in batch prediction {batch_id} "
            f"(attempt {self.request.retries + 1}/{self.max_retries + 1}): {e}",
            exc_info=True
        )
        
        # Store detailed error message
        error_message = f"Batch prediction failed: {str(e)}"
        if self.request.retries > 0:
            error_message = f"Batch prediction failed after {self.request.retries + 1} attempts: {str(e)}"
        
        # Retry the task
        try:
            raise self.retry(exc=e)
        except MaxRetriesExceededError:
            # Max retries exceeded
            logger.error(
                f"Batch prediction {batch_id} failed after {self.max_retries + 1} attempts. "
                "Max retries exceeded."
            )
            
            return {
                "success": False,
                "batch_id": batch_id,
                "error": error_message,
                "retry_count": self.request.retries,
                "max_retries_exceeded": True
            }
        
    finally:
        db.close()
