import uuid
from sqlalchemy import Column, String, DateTime, func
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base
from app.models.organization import Organization

class ChatSession(Base):
    __tablename__ = "chat_sessions"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = Column(String(36), ForeignKey("organizations.id"), nullable=False)
    dataset_id = Column(String(36), ForeignKey("datasets.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    organization = relationship("Organization", foreign_keys=[org_id])
    dataset = relationship("Dataset", foreign_keys=[dataset_id])
    user = relationship("User", foreign_keys=[user_id])
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")
