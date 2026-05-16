
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from backend.infrastructure.database import Base


class PreprocessingConfig(Base):
    __tablename__ = "preprocessing_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    
                                             
    encoding_mappings = Column(JSONB, nullable=False)                                                
    scaler_params = Column(JSONB, nullable=False)                                    
    smote_config = Column(JSONB, nullable=False)                       
    feature_columns = Column(JSONB, nullable=False)                                
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

                   
    dataset = relationship("Dataset", back_populates="preprocessing_configs")
    model_versions = relationship(
        "ModelVersion",
        back_populates="preprocessing_config",
        passive_deletes=True,
    )

    def __repr__(self):
        return f"<PreprocessingConfig(id={self.id}, dataset_id={self.dataset_id})>"
