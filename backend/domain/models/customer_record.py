
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, LargeBinary, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.infrastructure.database import Base


class CustomerRecord(Base):
    __tablename__ = "customer_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    
                                                   
    customer_id_encrypted = Column(LargeBinary, nullable=False)
    payment_method_encrypted = Column(LargeBinary, nullable=True)
    
                          
    gender = Column(String(10), nullable=True)
    senior_citizen = Column(Integer, nullable=True)
    partner = Column(String(10), nullable=True)
    dependents = Column(String(10), nullable=True)
    
                      
    tenure = Column(Integer, nullable=True)
    phone_service = Column(String(10), nullable=True)
    multiple_lines = Column(String(50), nullable=True)
    internet_service = Column(String(50), nullable=True)
    online_security = Column(String(50), nullable=True)
    online_backup = Column(String(50), nullable=True)
    device_protection = Column(String(50), nullable=True)
    tech_support = Column(String(50), nullable=True)
    streaming_tv = Column(String(50), nullable=True)
    streaming_movies = Column(String(50), nullable=True)
    
                      
    contract = Column(String(50), nullable=True)
    paperless_billing = Column(String(10), nullable=True)
    monthly_charges = Column(Float, nullable=True)
    total_charges = Column(Float, nullable=True)
    
                     
    churn = Column(Boolean, nullable=True, index=True)
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

                   
    dataset = relationship("Dataset", back_populates="customer_records")

    def __repr__(self):
        return f"<CustomerRecord(id={self.id}, dataset_id={self.dataset_id}, churn={self.churn})>"
