
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from backend.infrastructure.database import Base


class Report(Base):
    __tablename__ = "reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    model_version_id = Column(
        UUID(as_uuid=True), ForeignKey("model_versions.id", ondelete="SET NULL"), nullable=True
    )
    
    report_type = Column(String(50), nullable=False)
    file_path = Column(String(500), nullable=False)                      
    report_metadata = Column(JSONB, nullable=True)                                                      
    
    generated_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)

                   
    user = relationship("User", back_populates="reports")
    model_version = relationship("ModelVersion", back_populates="reports")

    def __repr__(self):
        return f"<Report(id={self.id}, type={self.report_type}, generated_at={self.generated_at})>"
