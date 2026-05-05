"""
Training Celery Tasks
"""

import logging
import time
from uuid import UUID

from celery.exceptions import MaxRetriesExceededError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.config import settings
from backend.services.training_service import TrainingService
from backend.services.training_progress_service import TrainingProgressService
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
    name="backend.workers.training_tasks.train_model_task",
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 2},
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True
)
def train_model_task(
    self,
    job_id: str,
    dataset_id: str,
    model_type: str,
    hyperparameters: dict | None = None
) -> dict:
    """
    Background task for training a machine learning model with retry logic
    
    - 8.7: Display Training_Job status in real-time
    - 8.8: Store Model_Version in Database when complete
    - 8.9: Complete all Training_Jobs within 60 seconds for 4 models on 5,634 records
    - 17.1: Emit progress updates every 5 seconds
    - 17.2: Report current iteration, total iterations, estimated time remaining
    - 17.3: Store training progress in database
    - 17.6: Emit error messages with failure reason
    - 30.3: Retry failed training jobs up to 2 times with exponential backoff
    
    Args:
        self: Celery task instance (for progress updates and retries)
        job_id: Training job UUID as string
        dataset_id: Dataset UUID as string
        model_type: Model type (KNN, NaiveBayes, DecisionTree, SVM)
        hyperparameters: Optional hyperparameters for training
        
    Returns:
        Dictionary with training results
    """
    db = SessionLocal()
    
    try:
        job_uuid = UUID(job_id)
        dataset_uuid = UUID(dataset_id)
        
        # Get retry information
        retry_count = self.request.retries
        max_retries = self.max_retries
        
        logger.info(
            f"Starting training job {job_id}: {model_type} on dataset {dataset_id} "
            f"(attempt {retry_count + 1}/{max_retries + 1})"
        )
        
        # Update job status to running
        TrainingService.update_job_status(
            db,
            job_uuid,
            status="running",
            progress=0
        )
        
        # Import ML training service
        from backend.services.ml_training_service import MLTrainingService
        
        # Determine if hyperparameter optimization should be used
        optimize_hyperparameters = hyperparameters is None or hyperparameters.get("optimize", False)
        
        # Remove 'optimize' flag from hyperparameters if present
        if hyperparameters and "optimize" in hyperparameters:
            hyperparameters = {k: v for k, v in hyperparameters.items() if k != "optimize"}
            if not hyperparameters:
                hyperparameters = None
        
        # Update progress to 10% (starting training)
        TrainingService.update_job_status(
            db,
            job_uuid,
            status="running",
            progress=10
        )
        
        # Train the model using ML training service
        # This handles:
        # 1. Load and preprocess the dataset
        # 2. Train the model with hyperparameters or optimization
        # 3. Evaluate the model on test set
        # 4. Save model artifact to R2 storage
        # 5. Create ModelVersion record
        # 6. Log to MLflow
        
        # Get training job to access user_id
        training_job = TrainingService.get_job(db, job_uuid)
        
        model_version = MLTrainingService.train_model(
            db=db,
            user_id=training_job.user_id,
            dataset_id=dataset_uuid,
            model_type=model_type,
            hyperparameters=hyperparameters,
            optimize_hyperparameters=optimize_hyperparameters
        )
        
        # Update job with model version ID and mark as completed
        training_job.model_version_id = model_version.id
        
        TrainingService.update_job_status(
            db,
            job_uuid,
            status="completed",
            progress=100
        )
        
        # Store final training metrics as progress entries
        TrainingProgressService.create_progress_entry(
            db,
            job_uuid,
            iteration=100,
            metric_name="accuracy",
            metric_value=model_version.metrics["accuracy"]
        )
        
        TrainingProgressService.create_progress_entry(
            db,
            job_uuid,
            iteration=100,
            metric_name="f1_score",
            metric_value=model_version.metrics["f1_score"]
        )
        
        logger.info(f"Successfully completed training job {job_id}")
        
        return {
            "success": True,
            "job_id": job_id,
            "model_type": model_type,
            "model_version_id": str(model_version.id),
            "version": model_version.version,
            "metrics": model_version.metrics,
            "training_time": model_version.training_time_seconds,
            "retry_count": retry_count
        }
        
    except Exception as e:
        logger.error(
            f"Error in training job {job_id} (attempt {self.request.retries + 1}/{self.max_retries + 1}): {e}",
            exc_info=True
        )
        
        # Store detailed error message (Requirement 17.6)
        error_message = f"Training failed: {str(e)}"
        if self.request.retries > 0:
            error_message = f"Training failed after {self.request.retries + 1} attempts: {str(e)}"
        
        # Update job status to failed
        try:
            TrainingService.update_job_status(
                db,
                UUID(job_id),
                status="failed",
                error=error_message
            )
        except Exception as update_error:
            logger.error(f"Failed to update job status: {update_error}")
        
        # Retry the task (Requirement 30.3)
        try:
            # Exponential backoff: 2^retry_count * base_delay (with jitter)
            # Base delay is handled by retry_backoff=True
            raise self.retry(exc=e)
        except MaxRetriesExceededError:
            # Max retries exceeded, job stays failed
            logger.error(
                f"Training job {job_id} failed after {self.max_retries + 1} attempts. "
                "Max retries exceeded."
            )
            
            return {
                "success": False,
                "job_id": job_id,
                "error": error_message,
                "retry_count": self.request.retries,
                "max_retries_exceeded": True
            }
        
    finally:
        db.close()
