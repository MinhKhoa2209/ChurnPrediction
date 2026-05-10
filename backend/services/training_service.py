import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from backend.domain.models.training_job import TrainingJob

logger = logging.getLogger(__name__)


VALID_MODEL_TYPES = {"KNN", "NaiveBayes", "DecisionTree", "SVM"}


VALID_STATUSES = {"queued", "running", "completed", "failed"}


class TrainingService:
    @staticmethod
    def create_training_job(
        db: Session, user_id: UUID, dataset_id: UUID, model_type: str
    ) -> TrainingJob:
        if model_type not in VALID_MODEL_TYPES:
            raise ValueError(
                f"Invalid model_type '{model_type}'. Must be one of: {', '.join(VALID_MODEL_TYPES)}"
            )

        training_job = TrainingJob(
            user_id=user_id,
            dataset_id=dataset_id,
            model_type=model_type,
            status="queued",
            progress_percent=0,
            created_at=datetime.utcnow(),
        )

        db.add(training_job)
        db.commit()
        db.refresh(training_job)

        logger.info(
            f"Created training job {training_job.id} for user {user_id}: "
            f"{model_type} on dataset {dataset_id}"
        )

        return training_job

    @staticmethod
    def get_training_job(db: Session, job_id: UUID, user_id: UUID) -> Optional[TrainingJob]:
        return (
            db.query(TrainingJob)
            .filter(TrainingJob.id == job_id, TrainingJob.user_id == user_id)
            .first()
        )

    @staticmethod
    def get_job(db: Session, job_id: UUID) -> Optional[TrainingJob]:
        """Get training job by ID without user filter (for internal use)"""
        return db.query(TrainingJob).filter(TrainingJob.id == job_id).first()

    @staticmethod
    def list_training_jobs(
        db: Session, user_id: UUID, status_filter: Optional[str] = None
    ) -> list[TrainingJob]:
        if status_filter and status_filter not in VALID_STATUSES:
            raise ValueError(
                f"Invalid status_filter '{status_filter}'. Must be one of: {', '.join(VALID_STATUSES)}"
            )

        query = db.query(TrainingJob).filter(TrainingJob.user_id == user_id)

        if status_filter:
            query = query.filter(TrainingJob.status == status_filter)

        return query.order_by(TrainingJob.created_at.desc()).all()

    @staticmethod
    def update_job_status(
        db: Session,
        job_id: UUID,
        status: str,
        progress: Optional[int] = None,
        current_iteration: Optional[int] = None,
        total_iterations: Optional[int] = None,
        estimated_seconds_remaining: Optional[int] = None,
        error: Optional[str] = None,
        model_version_id: Optional[UUID] = None,
    ) -> Optional[TrainingJob]:
        if status not in VALID_STATUSES:
            raise ValueError(
                f"Invalid status '{status}'. Must be one of: {', '.join(VALID_STATUSES)}"
            )

        training_job = db.query(TrainingJob).filter(TrainingJob.id == job_id).first()

        if not training_job:
            return None

        training_job.status = status

        if progress is not None:
            training_job.progress_percent = max(0, min(100, progress))

        if current_iteration is not None:
            training_job.current_iteration = current_iteration

        if total_iterations is not None:
            training_job.total_iterations = total_iterations

        if estimated_seconds_remaining is not None:
            training_job.estimated_seconds_remaining = estimated_seconds_remaining

        if error is not None:
            training_job.error_message = error

        if model_version_id is not None:
            training_job.model_version_id = model_version_id

        if status == "running" and not training_job.started_at:
            training_job.started_at = datetime.utcnow()

        if status in ["completed", "failed"] and not training_job.completed_at:
            training_job.completed_at = datetime.utcnow()
            training_job.progress_percent = (
                100 if status == "completed" else training_job.progress_percent
            )

        db.commit()
        db.refresh(training_job)

        logger.info(f"Updated training job {job_id} status to {status}")

        return training_job

    @staticmethod
    def delete_training_job(db: Session, job_id: UUID, user_id: UUID) -> bool:
        training_job = (
            db.query(TrainingJob)
            .filter(TrainingJob.id == job_id, TrainingJob.user_id == user_id)
            .first()
        )

        if not training_job:
            return False

        if training_job.status == "running":
            logger.warning(
                f"Cannot delete running training job {job_id}. "
                "Cancel the job first (not yet implemented)."
            )
            return False

        db.delete(training_job)
        db.commit()

        logger.info(f"Deleted training job {job_id} for user {user_id}")

        return True
