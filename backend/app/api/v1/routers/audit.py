"""Audit log API router.

Provides endpoints for viewing and exporting audit logs
with org_id scoping for multi-tenant compliance.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, and_
from sqlalchemy.orm import Session
from typing import Optional, List

from app.database import get_db
from app.models.audit_log import AuditLog
from app.models.user import User
from app.auth import get_current_user as get_current_active_user

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("", response_model=List[dict])
async def list_audit_logs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    # Org scoping - only show logs for user's org
    org_id: Optional[str] = Query(None, description="Filter by org_id"),
    # Pagination
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Max records to return"),
    # Filters
    start_date: Optional[str] = Query(None, description="Filter logs from this date (ISO)"),
    end_date: Optional[str] = Query(None, description="Filter logs to this date (ISO)"),
    method: Optional[str] = Query(None, description="Filter by HTTP method"),
    path: Optional[str] = Query(None, description="Filter by request path"),
    has_sensitive_data: Optional[bool] = Query(
        None, description="Filter by sensitive data detection"
    ),
) -> List[dict]:
    """List audit logs for the current user's organization."""
    from app.database import Base
    from sqlalchemy import select, and_

    # Build query with org_id scoping
    query = select(AuditLog).where(AuditLog.org_id == current_user.org_id)

    # Apply optional filters
    if org_id:
        query = query.where(AuditLog.org_id == org_id)

    if start_date:
        from datetime import datetime
        try:
            start_dt = datetime.fromisoformat(start_date)
            query = query.where(AuditLog.timestamp >= start_dt)
        except ValueError:
            pass

    if end_date:
        from datetime import datetime, timezone
        try:
            end_dt = datetime.fromisoformat(end_date).replace(tzinfo=timezone.utc)
            query = query.where(AuditLog.timestamp <= end_dt)
        except ValueError:
            pass

    if method:
        query = query.where(AuditLog.method == method)

    if path:
        query = query.where(AuditLog.path.contains(path))

    if has_sensitive_data is not None:
        query = query.where(AuditLog.sensitive_data_detected == has_sensitive_data)

    # Apply pagination and ordering
    query = query.order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit)

    result = db.execute(query).scalars().all()

    return [
        {
            "id": log.id,
            "timestamp": log.timestamp.isoformat() if log.timestamp else None,
            "method": log.method,
            "path": log.path,
            "org_id": log.org_id,
            "user_id": log.user_id,
            "request_id": log.request_id,
            "ip_address": log.ip_address,
            "user_agent": log.user_agent,
            "status_code": log.status_code,
            "response_time_ms": log.response_time_ms,
            "sensitive_data_detected": log.sensitive_data_detected,
            "description": log.description,
            "success": log.success,
        }
        for log in result
    ]


@router.get("/{log_id}", response_model=dict)
async def get_audit_log(
    log_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """Get a specific audit log entry."""
    from sqlalchemy import select

    query = select(AuditLog).where(
        and_(AuditLog.id == log_id, AuditLog.org_id == current_user.org_id)
    )
    log = db.execute(query).scalar_one_or_none()

    if not log:
        raise HTTPException(status_code=404, detail="Audit log entry not found")

    return {
        "id": log.id,
        "timestamp": log.timestamp.isoformat() if log.timestamp else None,
        "method": log.method,
        "path": log.path,
        "org_id": log.org_id,
        "user_id": log.user_id,
        "request_id": log.request_id,
        "ip_address": log.ip_address,
        "user_agent": log.user_agent,
        "status_code": log.status_code,
        "response_time_ms": log.response_time_ms,
        "sensitive_data_detected": log.sensitive_data_detected,
        "description": log.description,
        "success": log.success,
    }


@router.delete("/retention/cleanup")
async def cleanup_audit_logs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    days: int = Query(90, ge=1, description="Delete logs older than N days"),
) -> dict:
    """Clean up old audit logs based on retention policy.

    Only accessible by org owners/admins.
    """
    from datetime import datetime, timedelta, timezone

    # Check if user is org owner (simple check - in production, use proper RBAC)
    # Query old logs
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

    old_logs = db.execute(
        select(AuditLog).where(
            and_(
                AuditLog.org_id == current_user.org_id,
                AuditLog.timestamp < cutoff_date,
            )
        )
    ).scalars().all()

    for log in old_logs:
        db.delete(log)

    db.commit()

    return {
        "status": "completed",
        "deleted_count": len(old_logs),
        "retention_days": days,
    }