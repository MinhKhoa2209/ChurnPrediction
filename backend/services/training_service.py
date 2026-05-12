import logging
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from backend.domain.models.training_job import TrainingJob

logger = logging.getLogger(__name__)


VALID_MODEL_TYPES = {"KNN", "NaiveBayes", "DecisionTree", "SVM"}


VALID_STATUSES = {"queued", "running", "completed", "failed"}
STALE_QUEUED_TIMEOUT = timedelta(minutes=15)
STALE_RUNNING_TIMEOUT = timedelta(hours=1)


class TrainingService:
    @staticmethod
    def _normalize_uuid(value: UUID | str | None) -> UUID | None:
        if value is None or isinstance(value, UUID):
            return value
        return UUID(value)

    @staticmethod
    def _utc_like(reference_time: Optional[datetime]) -> datetime:
        if reference_time and reference_time.tzinfo is not None:
            return datetime.now(reference_time.tzinfo)
        return datetime.utcnow()

    @staticmethod
    def reconcile_stale_jobs(
        db: Session,
        user_id: Optional[UUID] = None,
        dataset_id: Optional[UUID] = None,
        job_id: Optional[UUID] = None,
    ) -> int:
        from backend.domain.models.model_version import ModelVersion

        user_id = TrainingService._normalize_uuid(user_id)
        dataset_id = TrainingService._normalize_uuid(dataset_id)
        job_id = TrainingService._normalize_uuid(job_id)
        query = db.query(TrainingJob).filter(TrainingJob.status.in_(["queued", "running"]))

        if user_id is not None:
            query = query.filter(TrainingJob.user_id == user_id)

        if dataset_id is not None:
            query = query.filter(TrainingJob.dataset_id == dataset_id)

        if job_id is not None:
            query = query.filter(TrainingJob.id == job_id)

        stale_jobs = query.all()
        updated_count = 0

        for job in stale_jobs:
            reference_time = job.started_at or job.created_at
            now = TrainingService._utc_like(reference_time)
            timeout = STALE_RUNNING_TIMEOUT if job.status == "running" else STALE_QUEUED_TIMEOUT

            if not reference_time or now - reference_time < timeout:
                continue

            matching_model = (
                db.query(ModelVersion)
                .filter(
                    ModelVersion.user_id == job.user_id,
                    ModelVersion.dataset_id == job.dataset_id,
                    ModelVersion.model_type == job.model_type,
                    ModelVersion.trained_at >= job.created_at,
                )
                .order_by(ModelVersion.trained_at.desc())
                .first()
            )

            if matching_model:
                job.status = "completed"
                job.model_version_id = matching_model.id
                job.progress_percent = 100
                job.completed_at = matching_model.trained_at or now
                job.error_message = None
                logger.warning(
                    "Reconciled stale training job %s as completed using model version %s",
                    job.id,
                    matching_model.id,
                )
            else:
                job.status = "failed"
                job.completed_at = now
                job.error_message = (
                    "Training job was interrupted before completion. Please start it again."
                )
                job.progress_percent = job.progress_percent or 0
                logger.warning("Marked stale training job %s as failed", job.id)

            updated_count += 1

        if updated_count:
            db.commit()

        return updated_count

    @staticmethod
    def create_training_job(
        db: Session, user_id: UUID, dataset_id: UUID, model_type: str
    ) -> TrainingJob:
        user_id = TrainingService._normalize_uuid(user_id)
        dataset_id = TrainingService._normalize_uuid(dataset_id)

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
    def get_training_job(db: Session, job_id: UUID, user_id: Optional[UUID] = None) -> Optional[TrainingJob]:
        job_id = TrainingService._normalize_uuid(job_id)
        if user_id:
            user_id = TrainingService._normalize_uuid(user_id)
        TrainingService.reconcile_stale_jobs(db=db, user_id=user_id, job_id=job_id)
        query = db.query(TrainingJob).filter(TrainingJob.id == job_id)
        if user_id:
            query = query.filter(TrainingJob.user_id == user_id)
        return query.first()

    @staticmethod
    def get_job(db: Session, job_id: UUID) -> Optional[TrainingJob]:
        """Get training job by ID without user filter (for internal use)"""
        return db.query(TrainingJob).filter(TrainingJob.id == job_id).first()

    @staticmethod
    def list_training_jobs(
        db: Session, user_id: Optional[UUID] = None, status_filter: Optional[str] = None
    ) -> list[TrainingJob]:
        if user_id:
            user_id = TrainingService._normalize_uuid(user_id)

        if status_filter and status_filter not in VALID_STATUSES:
            raise ValueError(
                f"Invalid status_filter '{status_filter}'. Must be one of: {', '.join(VALID_STATUSES)}"
            )

        TrainingService.reconcile_stale_jobs(db=db, user_id=user_id)

        query = db.query(TrainingJob)
        if user_id:
            query = query.filter(TrainingJob.user_id == user_id)

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
        job_id = TrainingService._normalize_uuid(job_id)
        user_id = TrainingService._normalize_uuid(user_id)
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
