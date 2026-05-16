
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.infrastructure.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50), nullable=False, index=True)
    resource_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
                                                                  
    ip_address = Column(String(45), nullable=True)                               
    user_agent = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self):
        return f"<AuditLog(id={self.id}, action={self.action}, resource={self.resource_type})>"
