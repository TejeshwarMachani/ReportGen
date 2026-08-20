import uuid
from sqlalchemy import Column, String, Text, DateTime, func
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("chat_sessions.id"), nullable=False)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    chart_data_json = Column(Text, nullable=True)
    query_executed = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    session = relationship("ChatSession", foreign_keys=[session_id], back_populates="messages")
