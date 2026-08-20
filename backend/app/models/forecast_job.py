import uuid
from sqlalchemy import Column, String, Integer, DateTime, func, Text
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base

class ForecastJob(Base):
    __tablename__ = "forecast_jobs"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = Column(String(36), ForeignKey("organizations.id"), nullable=False)
    dataset_id = Column(String(36), ForeignKey("datasets.id"), nullable=False)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    target_column = Column(String(255), nullable=False)
    date_column = Column(String(255), nullable=False)
    horizon_periods = Column(Integer, default=12)
    model_type = Column(String(20), default="prophet")
    result_json = Column(Text, nullable=True)
    status = Column(String(20), default="queued")
    created_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)
    organization = relationship("Organization", foreign_keys=[org_id])
    dataset = relationship("Dataset", foreign_keys=[dataset_id])
    created_by_user = relationship("User", foreign_keys=[created_by])
