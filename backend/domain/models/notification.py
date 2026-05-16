
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.infrastructure.database import Base


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    training_job_id = Column(
        UUID(as_uuid=True), ForeignKey("training_jobs.id", ondelete="CASCADE"), nullable=True
    )
    
    notification_type = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    
    is_read = Column(Boolean, default=False, nullable=False, index=True)
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)
    read_at = Column(DateTime(timezone=True), nullable=True)

                   
    user = relationship("User", back_populates="notifications")
    training_job = relationship("TrainingJob", back_populates="notifications")

    def __repr__(self):
        return f"<Notification(id={self.id}, type={self.notification_type}, is_read={self.is_read})>"
