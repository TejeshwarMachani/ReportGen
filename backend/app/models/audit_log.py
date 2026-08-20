"""SQLAlchemy model for audit log entries.

Maps to the audit_logs table in the database.
All entries are scoped by org_id for multi-tenant audit trails.
"""
from sqlalchemy import Column, String, DateTime, Integer, Boolean
from sqlalchemy.sql import func
from ..database import Base


class AuditLog(Base):
    """Audit log entry model.

    Stores a record of significant operations for compliance and debugging.
    Each entry is automatically scoped by org_id for multi-tenant isolation.

    Attributes:
        id: Primary key UUID
        timestamp: When the log entry was created (UTC)
        method: HTTP method of the request
        path: Request path
        org_id: Organization identifier (multi-tenant scoping)
        user_id: User identifier from JWT
        request_id: Unique request ID for correlation
        ip_address: Client IP address
        user_agent: Client user agent string
        status_code: HTTP response status code
        response_time_ms: How long the request took (ms)
        sensitive_data_detected: Whether PII/secrets were in the request
        description: Human-readable description of the operation
        success: Whether the operation was considered successful
    """

    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, default=lambda: __import__('uuid').uuid4().hex[:12])
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    method = Column(String, nullable=False, index=True)
    path = Column(String, nullable=False, index=True)
    org_id = Column(String, nullable=True, index=True)
    user_id = Column(String, nullable=True, index=True)
    request_id = Column(String, nullable=False, unique=True, index=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    status_code = Column(Integer, nullable=True)
    response_time_ms = Column(Integer, nullable=True)
    sensitive_data_detected = Column(Boolean, nullable=False, default=False)
    description = Column(String, nullable=False)
    success = Column(Boolean, nullable=False, default=True)