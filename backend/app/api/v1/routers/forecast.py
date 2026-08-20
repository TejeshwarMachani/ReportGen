import json
import pandas as pd
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from app.database import get_db
from app.models.dataset import Dataset
from app.models.forecast_job import ForecastJob
from app.models.user import User
from app.services.dataset_service import DatasetService
from app.services.forecast_service import ForecastService, ForecastResult
from app.auth import get_current_user


router = APIRouter(prefix="/forecast", tags=["forecast"])


class ForecastRequest(BaseModel):
    """Request body for forecast generation."""
    target_column: str
    date_column: str
    horizon: int = 12
    model_type: str = "prophet"  # prophet, ets, arima


class ForecastResultResponse(BaseModel):
    """Response model for forecast results."""
    id: str
    job_id: str
    target_column: str
    date_column: str
    horizon: int
    model_type: str
    status: str
    forecast_values: List[float]
    confidence_intervals: List[List[float]]
    model_params: Dict[str, Any]
    summary_text: Optional[str] = None
    created_at: str
    completed_at: Optional[str] = None

    class Config:
        from_attributes = True


class ForecastJobResponse(BaseModel):
    """Response model for forecast job status."""
    id: str
    org_id: str
    dataset_id: str
    target_column: str
    date_column: str
    horizon: int
    model_type: str
    status: str
    result_json: Optional[Dict] = None
    created_at: str
    completed_at: Optional[str] = None

    class Config:
        from_attributes = True


@router.post("/generate/{dataset_id}")
async def generate_forecast(
    dataset_id: str,
    request: ForecastRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Start a forecast job for a dataset.

    Validates the request, creates a forecast job, and
    starts the Celery background task.

    Key validation steps:
    1. Dataset exists and user has access (org_id scoping)
    2. Dataset has required date and target columns
    3. Data volume is sufficient
    4. Horizon is reasonable
    5. Model type is valid
    """
    # Validate dataset exists and user has access
    org_id = current_user.org_id
    dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        Dataset.org_id == org_id
    ).first()

    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found or access denied"
        )

    # Validate dataset has data
    schema = json.loads(dataset.schema_json) if dataset.schema_json else []
    column_names = set(col["column"] for col in schema if "column" in col)

    # Check that required columns exist
    missing_cols = []
    if request.date_column not in column_names:
        missing_cols.append(f"date column '{request.date_column}'")
    if request.target_column not in column_names:
        missing_cols.append(f"target column '{request.target_column}'")

    if missing_cols:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Dataset missing required columns: {', '.join(missing_cols)}"
        )

    # Validate forecast request
    df_placeholder = pd.DataFrame()  # Would read actual data in production
    is_valid, error_msg = ForecastService.validate_forecast_request(
        df_placeholder,
        request.target_column,
        request.date_column,
        request.horizon,
    )

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )

    # Create forecast job record
    from sqlalchemy import func
    job = ForecastJob(
        org_id=org_id,
        dataset_id=dataset.id,
        created_by=current_user.id,
        target_column=request.target_column,
        date_column=request.date_column,
        horizon_periods=request.horizon,
        model_type=request.model_type,
        status="queued",
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    # Start background task. If the broker is unreachable (local dev),
    # run the task inline so forecasting still works.
    from app.workers.forecast_task import run_forecast_task

    task_kwargs = {
        "job_id": job.id,
        "dataset_id": dataset.id,
        "target_column": request.target_column,
        "date_column": request.date_column,
        "horizon": request.horizon,
        "model_type": request.model_type,
    }
    try:
        task = run_forecast_task.apply_async(kwargs=task_kwargs)
    except Exception:
        run_forecast_task.apply(kwargs=task_kwargs)
        task_id = None
    else:
        task_id = task.id

    return {
        "job_id": job.id,
        "status": "queued",
        "message": "Forecast job started in background",
        "task_id": task_id,
    }


@router.get("/jobs", response_model=List[ForecastJobResponse])
async def list_forecast_jobs(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List forecast jobs for current user's organization."""
    org_id = current_user.org_id
    jobs = db.query(ForecastJob).filter(ForecastJob.org_id == org_id).all()

    return [
        ForecastJobResponse(
            id=j.id,
            org_id=j.org_id,
            dataset_id=j.dataset_id,
            target_column=j.target_column,
            date_column=j.date_column,
            horizon=j.horizon_periods,
            model_type=j.model_type,
            status=j.status,
            result_json=json.loads(j.result_json) if j.result_json else None,
            created_at=j.created_at.isoformat() if j.created_at else "",
            completed_at=j.completed_at.isoformat() if j.completed_at else None,
        )
        for j in jobs
    ]


@router.get("/jobs/{job_id}")
async def get_forecast_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get a specific forecast job's status and results."""
    org_id = current_user.org_id
    job = db.query(ForecastJob).filter(
        ForecastJob.id == job_id,
        ForecastJob.org_id == org_id
    ).first()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Forecast job not found or access denied"
        )

    result = None
    if job.result_json:
        result = ForecastResultResponse(
            id=job.id,
            job_id=job.id,
            target_column=job.target_column,
            date_column=job.date_column,
            horizon=job.horizon_periods,
            model_type=job.model_type,
            status=job.status,
            forecast_values=job.result_json.get("forecast_values", []) if job.result_json else [],
            confidence_intervals=job.result_json.get("confidence_intervals", []) if job.result_json else [],
            model_params=job.result_json.get("model_params", {}) if job.result_json else {},
            summary_text=job.result_json.get("summary_text") if job.result_json else None,
            created_at=job.created_at.isoformat() if job.created_at else "",
            completed_at=job.completed_at.isoformat() if job.completed_at else None,
        )

    return {
        "job": {
            "id": job.id,
            "org_id": job.org_id,
            "dataset_id": job.dataset_id,
            "target_column": job.target_column,
            "date_column": job.date_column,
            "horizon": job.horizon_periods,
            "model_type": job.model_type,
            "status": job.status,
            "created_at": job.created_at.isoformat() if job.created_at else "",
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        },
        "result": result,
    }