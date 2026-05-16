
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.infrastructure.database import Base


class TrainingProgress(Base):
    __tablename__ = "training_progress"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    training_job_id = Column(
        UUID(as_uuid=True), ForeignKey("training_jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    
    iteration = Column(Integer, nullable=False)
    metric_value = Column(Float, nullable=False)
    metric_name = Column(String(50), nullable=False)
    
    recorded_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)

                   
    training_job = relationship("TrainingJob", back_populates="training_progress")

    def __repr__(self):
        return f"<TrainingProgress(job_id={self.training_job_id}, iteration={self.iteration}, metric={self.metric_name}={self.metric_value})>"
