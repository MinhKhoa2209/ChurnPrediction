import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Enum, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.infrastructure.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)
    name = Column(String(255), nullable=True)
    avatar = Column(Text, nullable=True)
    provider = Column(String(50), nullable=False, default="credentials")
    role = Column(
        Enum("Admin", "Analyst", name="user_role"),
        nullable=False,
        default="Analyst",
        index=True,
    )
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    email_verified = Column(Boolean, default=False, nullable=False)
    email_notifications_enabled = Column(Boolean, default=False, nullable=False)
    reset_token = Column(String(255), nullable=True)
    reset_token_expires = Column(DateTime(timezone=True), nullable=True)

    datasets = relationship("Dataset", back_populates="user", cascade="all, delete-orphan")
    model_versions = relationship("ModelVersion", back_populates="user", cascade="all, delete-orphan")
    training_jobs = relationship("TrainingJob", back_populates="user", cascade="all, delete-orphan")
    predictions = relationship("Prediction", back_populates="user", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"
