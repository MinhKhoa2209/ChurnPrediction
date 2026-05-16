
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.infrastructure.database import Base


class TrainingJob(Base):
    __tablename__ = "training_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    model_version_id = Column(
        UUID(as_uuid=True), ForeignKey("model_versions.id", ondelete="SET NULL"), nullable=True
    )
    
    model_type = Column(String(50), nullable=False)
    status = Column(
        Enum("queued", "running", "completed", "failed", name="training_job_status"),
        nullable=False,
        index=True,
    )
    
                       
    progress_percent = Column(Integer, default=0, nullable=False)
    current_iteration = Column(Integer, nullable=True)
    total_iterations = Column(Integer, nullable=True)
    estimated_seconds_remaining = Column(Integer, nullable=True)
    
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

                   
    user = relationship("User", back_populates="training_jobs")
    dataset = relationship("Dataset", back_populates="training_jobs")
    model_version = relationship("ModelVersion", back_populates="training_jobs")
    training_progress = relationship("TrainingProgress", back_populates="training_job", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="training_job", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<TrainingJob(id={self.id}, type={self.model_type}, status={self.status})>"
