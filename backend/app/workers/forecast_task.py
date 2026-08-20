"""Celery task for running forecast generation."""
from __future__ import annotations

import json
import math
from datetime import datetime
from typing import Any, Dict

from celery import shared_task

from app.database import SessionLocal
from app.models.forecast_job import ForecastJob


@shared_task(bind=True, max_retries=3)
def run_forecast_task(
    self,
    job_id: str,
    dataset_id: str,
    target_column: str,
    date_column: str,
    horizon: int = 12,
    model_type: str = "prophet",
) -> Dict[str, Any]:
    """Run a forecast job and persist the result.

    ponytail: demo mode produces a deterministic placeholder series; wire the
    real data file + Prophet/statsmodels when the storage layer is connected.
    """
    session = SessionLocal()
    try:
        job = session.query(ForecastJob).filter(ForecastJob.id == job_id).first()
        if not job:
            raise ValueError(f"Forecast job {job_id} not found")

        job.status = "running"
        session.commit()

        values = [round(100.0 + i * 1.35, 2) for i in range(horizon)]
        ci = [
            [round(v * 0.85, 2), round(v * 1.15, 2)]
            for v in values
        ]
        direction = "upward" if values[-1] > values[0] else "downward"
        result = {
            "forecast_values": values,
            "confidence_intervals": ci,
            "model_params": {"model_type": model_type, "mode": "demo"},
            "summary_text": (
                f"Forecast for {target_column} over the next {horizon} periods "
                f"trends {direction}, from {values[0]:.2f} toward {values[-1]:.2f}. "
                f"Confidence bands widen over time as uncertainty grows."
            ),
        }

        job.result_json = json.dumps(result)
        job.status = "completed"
        job.completed_at = datetime.utcnow()
        session.commit()

        return {"job_id": job.id, "status": job.status, "horizon": horizon}
    except Exception as exc:
        session.rollback()
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))
    finally:
        session.close()
