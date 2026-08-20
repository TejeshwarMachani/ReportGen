from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, List
from pydantic import BaseModel

from app.database import get_db
from app.models.organization import Organization
from app.models.user import User
from app.models.dataset import Dataset
from app.models.report import Report as ReportModel
from app.models.forecast_job import ForecastJob
from app.auth import get_current_user


router = APIRouter(prefix="/dashboard", tags=["dashboard"])


class DashboardSummary(BaseModel):
    """Dashboard summary data for the home screen."""
    org_id: str
    organization_name: str
    total_datasets: int
    total_reports: int
    total_forecasts: int
    recent_activity: List[Dict[str, Any]]
    role: str


@router.get("", response_model=DashboardSummary)
async def dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get dashboard summary for the home screen.

    Shows key metrics and recent activity for the authenticated user's org.
    All queries are scoped by org_id from the authenticated JWT.
    """
    org_id = current_user.org_id

    # Count datasets for this org
    total_datasets = db.query(Dataset).filter(Dataset.org_id == org_id).count()

    # Count reports for this org
    total_reports = db.query(ReportModel).filter(ReportModel.org_id == org_id).count()

    # Count forecast jobs for this org
    total_forecasts = db.query(ForecastJob).filter(ForecastJob.org_id == org_id).count()

    # Recent activity: last 5 datasets, reports, and forecast jobs
    recent_datasets = db.query(Dataset)\
        .filter(Dataset.org_id == org_id)\
        .order_by(Dataset.created_at.desc())\
        .limit(5)\
        .all()

    recent_reports = db.query(ReportModel)\
        .filter(ReportModel.org_id == org_id)\
        .order_by(ReportModel.created_at.desc())\
        .limit(5)\
        .all()

    recent_forecasts = db.query(ForecastJob)\
        .filter(ForecastJob.org_id == org_id)\
        .order_by(ForecastJob.created_at.desc())\
        .limit(5)\
        .all()

    # Build recent activity list
    recent_activity = []

    for ds in recent_datasets:
        recent_activity.append({
            "id": ds.id,
            "type": "dataset",
            "title": ds.name,
            "created_at": ds.created_at.isoformat() if ds.created_at else "",
            "status": ds.status,
        })

    for rep in recent_reports:
        recent_activity.append({
            "id": rep.id,
            "type": "report",
            "title": rep.title,
            "created_at": rep.created_at.isoformat() if rep.created_at else "",
            "status": rep.status,
        })

    for fj in recent_forecasts:
        recent_activity.append({
            "id": fj.id,
            "type": "forecast",
            "title": f"Forecast: {fj.target_column}",
            "created_at": fj.created_at.isoformat() if fj.created_at else "",
            "status": fj.status,
        })

    # Sort by created_at descending
    recent_activity.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    recent_activity = recent_activity[:5]

    # Get organization name
    org = db.query(Organization).filter(Organization.id == org_id).first()
    org_name = org.name if org else "Organization"

    # Get user role
    user = db.query(User).filter(User.id == current_user.id).first()
    role = user.role if user else "member"

    return DashboardSummary(
        org_id=org_id,
        organization_name=org_name,
        total_datasets=total_datasets,
        total_reports=total_reports,
        total_forecasts=total_forecasts,
        recent_activity=recent_activity,
        role=role,
    )


@router.get("/stats")
async def dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get detailed dashboard statistics."""
    org_id = current_user.org_id

    # Dataset status breakdown
    dataset_status_counts = db.query(
        Dataset.status, func.count(Dataset.id)
    ).filter(Dataset.org_id == org_id)\
     .group_by(Dataset.status)\
     .all()

    report_status_counts = db.query(
        ReportModel.status, func.count(ReportModel.id)
    ).filter(ReportModel.org_id == org_id)\
     .group_by(ReportModel.status)\
     .all()

    forecast_status_counts = db.query(
        ForecastJob.status, func.count(ForecastJob.id)
    ).filter(ForecastJob.org_id == org_id)\
     .group_by(ForecastJob.status)\
     .all()

    return {
        "dataset_status_breakdown": {
            status: count for status, count in dataset_status_counts
        },
        "report_status_breakdown": {
            status: count for status, count in report_status_counts
        },
        "forecast_status_breakdown": {
            status: count for status, count in forecast_status_counts
        },
        "total_org_members": db.query(User).filter(User.org_id == org_id).count(),
    }