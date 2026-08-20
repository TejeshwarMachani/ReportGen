import uuid
from sqlalchemy import Column, String, Boolean, DateTime, func
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base
from app.models.organization import Organization

class User(Base):
    __tablename__ = "users"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = Column(String(36), ForeignKey("organizations.id"), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    role = Column(String(20), default="member")  # owner, admin, member, viewer
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    organization = relationship(Organization, foreign_keys=[org_id])
