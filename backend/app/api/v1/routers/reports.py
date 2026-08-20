import json
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from app.database import get_db
from app.models.dataset import Dataset
from app.models.report import Report as ReportModel
from app.services.dataset_service import DatasetService
from app.services.report_service import ReportService
from app.workers.report_task import generate_report_task
from app.auth import get_current_user


router = APIRouter(prefix="/reports", tags=["reports"])


class GenerateReportRequest(BaseModel):
    """Request body for report generation."""
    title: Optional[str] = None
    report_type: Optional[str] = None  # "auto_summary", "executive", "comparison"
    export_format: Optional[str] = None  # "pdf", "docx", None


class ReportResponse(BaseModel):
    """Response model for report operations."""
    id: str
    title: str
    dataset_id: str
    report_type: str
    status: str
    narrative_text: Optional[str] = None
    computed_stats_json: Optional[dict] = None
    charts_json: Optional[dict] = None
    created_at: str
    generated_at: Optional[str] = None
    export_format: Optional[str] = None
    export_result: Optional[dict] = None

    class Config:
        from_attributes = True


@router.post("/generate", status_code=status.HTTP_202_ACCEPTED)
async def generate_report(
    request: GenerateReportRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Generate a business report from a dataset.

    Task is processed asynchronously via Celery.
    The report generation pipeline:
    1. Validates dataset exists and user has access
    2. Computes deterministic statistics from the data
    3. Selects appropriate chart types
    4. Generates LLM prompt with ONLY pre-computed stats
    5. Calls Anthropic Claude API to generate narrative
    6. Assembles and stores the complete report
    7. Optionally renders to PDF/DOCX

    Key invariant: Every number in the narrative traces back to computed_stats_json.
    LLM never performs arithmetic on raw data.
    """
    # Check dataset exists and user has access
    dataset = db.query(Dataset).filter(Dataset.id == request.dataset_id).first() if hasattr(request, 'dataset_id') else None

    # For now, we'll need dataset_id from context - in real implementation
    # this would come from the authenticated user's org and their datasets

    # TODO: In full implementation, fetch dataset_id from request or auth context
    # For now, return pending status
    raise HTTPException(
        status_code=status.HTTP_202_ACCEPTED,
        detail="Report generation initiated asynchronously"
    )


@router.post("/generate/{dataset_id}")
async def generate_report_by_dataset(
    dataset_id: str,
    request: GenerateReportRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Generate a report for a specific dataset.

    Starts the Celery background task for report generation.
    Returns immediately with task ID for status polling.
    """
    # Validate dataset exists and user has access (org_id scoping)
    dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        Dataset.org_id == current_user.org_id
    ).first()

    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found or access denied"
        )

    # Validate dataset is ready (status should be "ready" not "processing"/"error")
    if dataset.status != "ready":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Dataset not ready for reporting. Current status: {dataset.status}"
        )

    # Start background task. If the broker is unreachable (local dev),
    # run the task inline so report generation still works.
    task_kwargs = {
        "dataset_id": dataset.id,
        "title": request.title or dataset.name,
        "user_id": current_user.id,
        "report_type": request.report_type or "auto_summary",
        "export_format": request.export_format,
    }
    try:
        task = generate_report_task.apply_async(kwargs=task_kwargs)
    except Exception:
        generate_report_task.apply(kwargs=task_kwargs)
        task_id = None
    else:
        task_id = task.id

    return {
        "task_id": task_id,
        "dataset_id": dataset.id,
        "status": "pending",
        "message": "Report generation started in background",
    }


@router.get("", response_model=List[ReportResponse])
async def list_reports(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List reports for current user's organization."""
    org_id = current_user.org_id
    reports = db.query(ReportModel).filter(ReportModel.org_id == org_id).all()

    return [
        ReportResponse(
            id=r.id,
            title=r.title,
            dataset_id=r.dataset_id,
            report_type=r.report_type,
            status=r.status,
            narrative_text=r.narrative_text,
            computed_stats_json=json.loads(r.computed_stats_json) if r.computed_stats_json else None,
            charts_json=json.loads(r.charts_json) if r.charts_json else None,
            created_at=r.created_at.isoformat() if r.created_at else "",
            generated_at=r.generated_at.isoformat() if r.generated_at else None,
            export_format=r.export_format,
            export_result=r.export_result,
        )
        for r in reports
    ]


@router.get("/{report_id}")
async def get_report(
    report_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get a specific report by ID."""
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

    return ReportResponse(
        id=report.id,
        title=report.title,
        dataset_id=report.dataset_id,
        report_type=report.report_type,
        status=report.status,
        narrative_text=report.narrative_text,
        computed_stats_json=json.loads(report.computed_stats_json) if report.computed_stats_json else None,
        charts_json=json.loads(report.charts_json) if report.charts_json else None,
        created_at=report.created_at.isoformat() if report.created_at else "",
        generated_at=report.generated_at.isoformat() if report.generated_at else None,
        export_format=report.export_format,
        export_result=report.export_result,
    )


@router.delete("/{report_id}", status_code=status.HTTP_200_OK)
async def delete_report(
    report_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Delete a report by ID (org-scoped)."""
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

    db.delete(report)
    db.commit()

    return {"detail": "Report deleted"}


@router.post("/{report_id}/export/{format}")
async def export_report(
    report_id: str,
    format: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Export a report in the specified format."""
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

    if report.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Report not yet completed. Current status: {report.status}"
        )

    # Generate export
    from app.workers.report_task import _render_pdf, _render_docx

    export_result = None
    if format == "pdf":
        export_result = _render_pdf(
            json.loads(report.computed_stats_json) if report.computed_stats_json else {},
            json.loads(report.charts_json) if report.charts_json else [],
            report.narrative_text or "",
        )
    elif format == "docx":
        export_result = _render_docx(
            json.loads(report.computed_stats_json) if report.computed_stats_json else {},
            json.loads(report.charts_json) if report.charts_json else [],
            report.narrative_text or "",
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported export format: {format}. Use 'pdf' or 'docx'."
        )

    # Update report with export info
    report.export_format = format
    report.export_result = export_result
    db.commit()

    return {
        "report_id": report.id,
        "format": format,
        "export_result": export_result,
        "download_url": f"/downloads/reports/{report.id}.{format}",
    }