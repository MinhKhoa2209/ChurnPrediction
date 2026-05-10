import logging
from uuid import UUID

from celery.exceptions import MaxRetriesExceededError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.config import settings
from backend.services.notification_service import NotificationService
from backend.services.training_progress_service import TrainingProgressService
from backend.services.training_service import TrainingService
from backend.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


engine = create_engine(
    settings.database_url.replace("postgresql+asyncpg://", "postgresql://"),
    pool_size=5,
    max_overflow=10,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@celery_app.task(
    name="backend.workers.training_tasks.train_model_task",
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 2},
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
)
def train_model_task(
    self, job_id: str, dataset_id: str, model_type: str, hyperparameters: dict | None = None
) -> dict:
    db = SessionLocal()

    try:
        job_uuid = UUID(job_id)
        dataset_uuid = UUID(dataset_id)

        retry_count = self.request.retries
        max_retries = self.max_retries

        logger.info(
            f"Starting training job {job_id}: {model_type} on dataset {dataset_id} "
            f"(attempt {retry_count + 1}/{max_retries + 1})"
        )

        TrainingService.update_job_status(db, job_uuid, status="running", progress=0)

        from backend.services.ml_training_service import MLTrainingService

        optimize_hyperparameters = hyperparameters is None or hyperparameters.get("optimize", False)

        if hyperparameters and "optimize" in hyperparameters:
            hyperparameters = {k: v for k, v in hyperparameters.items() if k != "optimize"}
            if not hyperparameters:
                hyperparameters = None

        TrainingService.update_job_status(db, job_uuid, status="running", progress=10)

        training_job = TrainingService.get_job(db, job_uuid)

        model_version = MLTrainingService.train_model(
            db=db,
            user_id=training_job.user_id,
            dataset_id=dataset_uuid,
            model_type=model_type,
            hyperparameters=hyperparameters,
            optimize_hyperparameters=optimize_hyperparameters,
        )

        training_job.model_version_id = model_version.id

        TrainingService.update_job_status(db, job_uuid, status="completed", progress=100)

        TrainingProgressService.create_progress_entry(
            db,
            job_uuid,
            iteration=100,
            metric_name="accuracy",
            metric_value=model_version.metrics["accuracy"],
        )

        TrainingProgressService.create_progress_entry(
            db,
            job_uuid,
            iteration=100,
            metric_name="f1_score",
            metric_value=model_version.metrics["f1_score"],
        )

        # Create notification for successful training completion
        try:
            notification_service = NotificationService()
            notification_service.create_training_completion_notification(
                db=db,
                user_id=training_job.user_id,
                training_job_id=job_uuid,
                model_type=model_type,
                status="completed"
            )
            logger.info(f"Created completion notification for training job {job_id}")
        except Exception as notif_error:
            logger.error(f"Failed to create notification: {notif_error}", exc_info=True)

        logger.info(f"Successfully completed training job {job_id}")

        return {
            "success": True,
            "job_id": job_id,
            "model_type": model_type,
            "model_version_id": str(model_version.id),
            "version": model_version.version,
            "metrics": model_version.metrics,
            "training_time": model_version.training_time_seconds,
            "retry_count": retry_count,
        }

    except Exception as e:
        logger.error(
            f"Error in training job {job_id} (attempt {self.request.retries + 1}/{self.max_retries + 1}): {e}",
            exc_info=True,
        )

        error_message = f"Training failed: {str(e)}"
        if self.request.retries > 0:
            error_message = f"Training failed after {self.request.retries + 1} attempts: {str(e)}"

        try:
            TrainingService.update_job_status(
                db, UUID(job_id), status="failed", error=error_message
            )
            
            # Create notification for failed training
            try:
                training_job = TrainingService.get_job(db, UUID(job_id))
                if training_job:
                    notification_service = NotificationService()
                    notification_service.create_training_completion_notification(
                        db=db,
                        user_id=training_job.user_id,
                        training_job_id=UUID(job_id),
                        model_type=model_type,
                        status="failed",
                        failure_reason=str(e)
                    )
                    logger.info(f"Created failure notification for training job {job_id}")
            except Exception as notif_error:
                logger.error(f"Failed to create failure notification: {notif_error}", exc_info=True)
                
        except Exception as update_error:
            logger.error(f"Failed to update job status: {update_error}")

        try:
            raise self.retry(exc=e)
        except MaxRetriesExceededError:
            logger.error(
                f"Training job {job_id} failed after {self.max_retries + 1} attempts. "
                "Max retries exceeded."
            )

            return {
                "success": False,
                "job_id": job_id,
                "error": error_message,
                "retry_count": self.request.retries,
                "max_retries_exceeded": True,
            }

    finally:
        db.close()
