"""
Training Job Service
"""

import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from backend.domain.models.training_job import TrainingJob

logger = logging.getLogger(__name__)

# Valid model types
VALID_MODEL_TYPES = {"KNN", "NaiveBayes", "DecisionTree", "SVM"}

# Valid job statuses
VALID_STATUSES = {"queued", "running", "completed", "failed"}


class TrainingService:
    """Service for training job operations"""
    
    @staticmethod
    def create_training_job(
        db: Session,
        user_id: UUID,
        dataset_id: UUID,
        model_type: str
    ) -> TrainingJob:
        """
        Create a new training job
        Requirement 8.5: Create Training_Job for each selected model type
        Requirement 8.7: Display Training_Job status in real-time
        
        Args:
            db: Database session
            user_id: User ID who created the job
            dataset_id: Dataset ID to train on
            model_type: Model type (KNN, NaiveBayes, DecisionTree, SVM)
            
        Returns:
            Created TrainingJob instance
            
        Raises:
            ValueError: If model_type is invalid
        """
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
            created_at=datetime.utcnow()
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
    def get_training_job(
        db: Session,
        job_id: UUID,
        user_id: UUID
    ) -> Optional[TrainingJob]:
        """
        Get training job by ID with user authorization
        Requirement 8.7: Users can only access their own training jobs
        
        Args:
            db: Database session
            job_id: Training job UUID
            user_id: User UUID (for ownership check)
            
        Returns:
            TrainingJob instance or None if not found or not owned by user
        """
        return db.query(TrainingJob).filter(
            TrainingJob.id == job_id,
            TrainingJob.user_id == user_id
        ).first()
    
    @staticmethod
    def list_training_jobs(
        db: Session,
        user_id: UUID,
        status_filter: Optional[str] = None
    ) -> list[TrainingJob]:
        """
        List user's training jobs with optional status filter
        Requirement 8.7: Display Training_Job status
        
        Args:
            db: Database session
            user_id: User UUID
            status_filter: Optional status filter (queued, running, completed, failed)
            
        Returns:
            List of TrainingJob instances
            
        Raises:
            ValueError: If status_filter is invalid
        """
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
        model_version_id: Optional[UUID] = None
    ) -> Optional[TrainingJob]:
        """
        Update training job status and progress
        Requirement 8.6: Execute Training_Jobs asynchronously in background processes
        Requirement 8.7: Display Training_Job status in real-time
        
        Args:
            db: Database session
            job_id: Training job UUID
            status: New status (queued, running, completed, failed)
            progress: Progress percentage (0-100)
            current_iteration: Current training iteration
            total_iterations: Total training iterations
            estimated_seconds_remaining: Estimated seconds remaining
            error: Error message if failed
            model_version_id: Model version ID if completed
            
        Returns:
            Updated TrainingJob instance or None if not found
            
        Raises:
            ValueError: If status is invalid
        """
        if status not in VALID_STATUSES:
            raise ValueError(
                f"Invalid status '{status}'. Must be one of: {', '.join(VALID_STATUSES)}"
            )
        
        training_job = db.query(TrainingJob).filter(TrainingJob.id == job_id).first()
        
        if not training_job:
            return None
        
        # Update status
        training_job.status = status
        
        # Update progress if provided
        if progress is not None:
            training_job.progress_percent = max(0, min(100, progress))
        
        # Update iteration tracking
        if current_iteration is not None:
            training_job.current_iteration = current_iteration
        
        if total_iterations is not None:
            training_job.total_iterations = total_iterations
        
        if estimated_seconds_remaining is not None:
            training_job.estimated_seconds_remaining = estimated_seconds_remaining
        
        # Update error message if provided
        if error is not None:
            training_job.error_message = error
        
        # Update model version ID if provided
        if model_version_id is not None:
            training_job.model_version_id = model_version_id
        
        # Update timestamps based on status
        if status == "running" and not training_job.started_at:
            training_job.started_at = datetime.utcnow()
        
        if status in ["completed", "failed"] and not training_job.completed_at:
            training_job.completed_at = datetime.utcnow()
            training_job.progress_percent = 100 if status == "completed" else training_job.progress_percent
        
        db.commit()
        db.refresh(training_job)
        
        logger.info(f"Updated training job {job_id} status to {status}")
        
        return training_job
    
    @staticmethod
    def delete_training_job(
        db: Session,
        job_id: UUID,
        user_id: UUID
    ) -> bool:
        """
        Delete/cancel a training job
        Users can only delete their own training jobs
        
        Args:
            db: Database session
            job_id: Training job UUID
            user_id: User UUID (for ownership check)
            
        Returns:
            True if deleted, False if not found or not owned by user
        """
        training_job = db.query(TrainingJob).filter(
            TrainingJob.id == job_id,
            TrainingJob.user_id == user_id
        ).first()
        
        if not training_job:
            return False
        
        # Only allow deletion of queued or failed jobs
        # Running jobs should be cancelled first (future enhancement)
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
