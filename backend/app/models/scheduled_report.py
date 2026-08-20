import uuid
from sqlalchemy import Column, String, DateTime, Boolean, Text, func
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base
from app.models.organization import Organization

class ScheduledReport(Base):
    __tablename__ = "scheduled_reports"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = Column(String(36), ForeignKey("organizations.id"), nullable=False)
    report_config_json = Column(Text, nullable=False)
    frequency = Column(String(20), default="weekly")
    recipients = Column(Text, nullable=True)
    next_run_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    organization = relationship("Organization", foreign_keys=[org_id])
