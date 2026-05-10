import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from backend.domain.models.training_progress import TrainingProgress

logger = logging.getLogger(__name__)


class TrainingProgressService:
    @staticmethod
    def create_progress_entry(
        db: Session, job_id: UUID, iteration: int, metric_name: str, metric_value: float
    ) -> TrainingProgress:
        progress_entry = TrainingProgress(
            training_job_id=job_id,
            iteration=iteration,
            metric_name=metric_name,
            metric_value=metric_value,
            recorded_at=datetime.utcnow(),
        )

        db.add(progress_entry)
        db.commit()
        db.refresh(progress_entry)

        logger.debug(
            f"Created progress entry for job {job_id}: "
            f"iteration={iteration}, {metric_name}={metric_value}"
        )

        return progress_entry

    @staticmethod
    def get_progress_history(
        db: Session, job_id: UUID, metric_name: Optional[str] = None
    ) -> list[TrainingProgress]:
        query = db.query(TrainingProgress).filter(TrainingProgress.training_job_id == job_id)

        if metric_name:
            query = query.filter(TrainingProgress.metric_name == metric_name)

        return query.order_by(TrainingProgress.iteration.asc()).all()

    @staticmethod
    def get_latest_metrics(db: Session, job_id: UUID) -> dict[str, float]:
        progress_entries = (
            db.query(TrainingProgress)
            .filter(TrainingProgress.training_job_id == job_id)
            .order_by(TrainingProgress.recorded_at.desc())
            .all()
        )

        latest_metrics = {}
        seen_metrics = set()

        for entry in progress_entries:
            if entry.metric_name not in seen_metrics:
                latest_metrics[entry.metric_name] = entry.metric_value
                seen_metrics.add(entry.metric_name)

        return latest_metrics

    @staticmethod
    def delete_progress_history(db: Session, job_id: UUID) -> int:
        deleted_count = (
            db.query(TrainingProgress).filter(TrainingProgress.training_job_id == job_id).delete()
        )

        db.commit()

        logger.info(f"Deleted {deleted_count} progress entries for job {job_id}")

        return deleted_count
