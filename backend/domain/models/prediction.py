
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from backend.infrastructure.database import Base


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    model_version_id = Column(
        UUID(as_uuid=True), ForeignKey("model_versions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    
                      
    input_features = Column(JSONB, nullable=False)
    probability = Column(Float, nullable=False)
    threshold = Column(Float, nullable=False)
    prediction = Column(Boolean, nullable=False)                                  
    
                    
    shap_values = Column(JSONB, nullable=False)
    
                              
    is_batch = Column(Boolean, default=False, nullable=False)
    batch_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)

                   
    user = relationship("User", back_populates="predictions")
    model_version = relationship("ModelVersion", back_populates="predictions")

    def __repr__(self):
        return f"<Prediction(id={self.id}, probability={self.probability:.2f}, prediction={self.prediction})>"
