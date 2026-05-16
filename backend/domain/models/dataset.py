
import uuid
from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship
from sqlalchemy.types import TypeDecorator

from backend.infrastructure.database import Base


class JSONType(TypeDecorator):
    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(JSONB())
        else:
            return dialect.type_descriptor(JSON())


                                                             
class UUIDType(TypeDecorator):
    impl = String(36)
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PGUUID(as_uuid=True))
        else:
            return dialect.type_descriptor(String(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return value
        else:
            return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return value
        else:
            return uuid.UUID(value) if isinstance(value, str) else value


class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(UUIDType, primary_key=True, default=uuid.uuid4)
    user_id = Column(UUIDType, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    file_hash = Column(String(64), nullable=True, index=True)
    record_count = Column(Integer, nullable=False)
    status = Column(
        Enum("uploading", "processing", "ready", "failed", name="dataset_status"),
        nullable=False,
        index=True,
    )
    validation_errors = Column(JSONType, nullable=True)
    data_quality_score = Column(Float, nullable=True)
    uploaded_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)
    processed_at = Column(DateTime(timezone=True), nullable=True)

                   
    user = relationship("User", back_populates="datasets")
    customer_records = relationship(
        "CustomerRecord",
        back_populates="dataset",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    preprocessing_configs = relationship(
        "PreprocessingConfig",
        back_populates="dataset",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    model_versions = relationship("ModelVersion", back_populates="dataset", passive_deletes=True)
    training_jobs = relationship("TrainingJob", back_populates="dataset", passive_deletes=True)

    def __repr__(self):
        return f"<Dataset(id={self.id}, filename={self.filename}, status={self.status})>"
