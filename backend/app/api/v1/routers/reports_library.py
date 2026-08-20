import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from app.database import get_db
from app.models.organization import Organization
from app.models.dataset import Dataset
from app.models.report import Report as ReportModel
from app.auth import get_current_user


router = APIRouter(prefix="/library", tags=["reports-library"])


class ReportItem(BaseModel):
    """Item in the reports library."""
    id: str
    title: str
    dataset_id: str
    report_type: str
    status: str
    created_at: str
    generated_at: Optional[str] = None
    export_format: Optional[str] = None

    class Config:
        from_attributes = True


class ReportSearchFilters(BaseModel):
    """Filters for reports library search."""
    report_type: Optional[List[str]] = None
    status: Optional[List[str]] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    search_text: Optional[str] = None


@router.get("", response_model=List[ReportItem])
async def reports_library(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    filters: ReportSearchFilters = Depends(),
):
    """List reports in the library with search and filtering.

    Supports filtering by:
    - report_type (auto_summary, executive, comparison, etc.)
    - status (queued, generating, completed, failed)
    - date range
    - search text in title
    """
    org_id = current_user.org_id
    query = db.query(ReportModel).filter(ReportModel.org_id == org_id)

    # Apply filters
    if filters.report_type:
        query = query.filter(ReportModel.report_type.in_(filters.report_type))

    if filters.status:
        query = query.filter(ReportModel.status.in_(filters.status))

    if filters.search_text:
        search = f"%{filters.search_text}%"
        query = query.filter(ReportModel.title.ilike(search))

    if filters.date_from:
        try:
            from datetime import datetime
            date_from = datetime.fromisoformat(filters.date_from)
            query = query.filter(ReportModel.created_at >= date_from)
        except (ValueError, TypeError):
            pass

    if filters.date_to:
        try:
            from datetime import datetime
            date_to = datetime.fromisoformat(filters.date_to)
            # End of day
            from datetime import timedelta
            date_to_end = date_to + timedelta(days=1)
            query = query.filter(ReportModel.created_at < date_to_end)
        except (ValueError, TypeError):
            pass

    # Order by most recent first
    query = query.order_by(ReportModel.created_at.desc())

    reports = query.all()

    return [
        ReportItem(
            id=r.id,
            title=r.title,
            dataset_id=r.dataset_id,
            report_type=r.report_type,
            status=r.status,
            created_at=r.created_at.isoformat() if r.created_at else "",
            generated_at=r.generated_at.isoformat() if r.generated_at else None,
            export_format=r.export_format,
        )
        for r in reports
    ]


@router.get("/{report_id}/details")
async def report_library_details(
    report_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get detailed information about a specific report from the library."""
    org_id = current_user.org_id
    report = db.query(ReportModel).filter(
        ReportModel.id == report_id,
        ReportModel.org_id == org_id
    ).first()

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found or access denied"
        )

    # Get dataset info
    dataset = db.query(Dataset).filter(Dataset.id == report.dataset_id).first()

    return {
        "report": {
            "id": report.id,
            "title": report.title,
            "report_type": report.report_type,
            "status": report.status,
            "narrative_text": report.narrative_text,
            "created_at": report.created_at.isoformat() if report.created_at else "",
            "generated_at": report.generated_at.isoformat() if report.generated_at else None,
            "export_format": report.export_format,
        },
        "dataset": {
            "id": dataset.id if dataset else None,
            "name": dataset.name if dataset else None,
            "source_type": dataset.source_type if dataset else None,
        } if dataset else None,
        "computed_stats": json.loads(report.computed_stats_json) if report.computed_stats_json else None,
        "charts": json.loads(report.charts_json) if report.charts_json else None,
    }