import uuid
from sqlalchemy import Column, String, Text, DateTime, func
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base
from app.models.organization import Organization
from app.models.dataset import Dataset
from app.models.user import User

class Report(Base):
    __tablename__ = "reports"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = Column(String(36), ForeignKey("organizations.id"), nullable=False)
    dataset_id = Column(String(36), ForeignKey("datasets.id"), nullable=False)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    report_type = Column(String(50), default="auto_summary")
    narrative_text = Column(Text, nullable=True)
    computed_stats_json = Column(Text, nullable=True)
    charts_json = Column(Text, nullable=True)
    status = Column(String(20), default="queued")  # queued, generating, completed, failed
    export_format = Column(String(10), nullable=True)
    export_result = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    generated_at = Column(DateTime, nullable=True)
    organization = relationship(Organization, foreign_keys=[org_id])
    dataset = relationship(Dataset, foreign_keys=[dataset_id])
    created_by_user = relationship(User, foreign_keys=[created_by])
