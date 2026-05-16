
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from backend.infrastructure.database import Base


class ModelVersion(Base):
    __tablename__ = "model_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    preprocessing_config_id = Column(
        UUID(as_uuid=True), ForeignKey("preprocessing_configs.id"), nullable=False
    )
    
    model_type = Column(
        Enum("KNN", "NaiveBayes", "DecisionTree", "SVM", name="model_type"),
        nullable=False,
        index=True,
    )
    version = Column(String(50), nullable=False, unique=True, index=True)
    
                    
    hyperparameters = Column(JSONB, nullable=False)
    metrics = Column(JSONB, nullable=False)                                                  
    confusion_matrix = Column(JSONB, nullable=False)
    training_time_seconds = Column(Float, nullable=False)
    
                          
    artifact_path = Column(String(500), nullable=False)                      
    mlflow_run_id = Column(String(255), nullable=True)
    
                          
    status = Column(
        Enum("active", "archived", name="model_status"),
        nullable=False,
        default="active",
        index=True,
    )
    classification_threshold = Column(Float, nullable=False, default=0.5)
    
    trained_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)
    archived_at = Column(DateTime(timezone=True), nullable=True)

                   
    user = relationship("User", back_populates="model_versions")
    dataset = relationship("Dataset", back_populates="model_versions")
    preprocessing_config = relationship("PreprocessingConfig", back_populates="model_versions")
    training_jobs = relationship("TrainingJob", back_populates="model_version")
    predictions = relationship("Prediction", back_populates="model_version")
    reports = relationship("Report", back_populates="model_version")

    def __repr__(self):
        return f"<ModelVersion(id={self.id}, type={self.model_type}, version={self.version})>"
