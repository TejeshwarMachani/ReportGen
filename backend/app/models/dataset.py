import uuid
from sqlalchemy import Column, String, Integer, DateTime, func, Text
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base
from app.models.organization import Organization
from app.models.user import User

class Dataset(Base):
    __tablename__ = "datasets"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = Column(String(36), ForeignKey("organizations.id"), nullable=False)
    uploaded_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    source_type = Column(String(10), default="csv")  # csv, xlsx
    file_path = Column(String(512), nullable=False)  # S3 key
    schema_json = Column(Text, nullable=True)
    row_count = Column(Integer, default=0)
    status = Column(String(20), default="uploading")  # uploading, processing, ready, error
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    organization = relationship(Organization, foreign_keys=[org_id])
    uploaded_by_user = relationship(User, foreign_keys=[uploaded_by])
