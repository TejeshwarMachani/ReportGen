"""Celery application for background jobs (reports, forecasts)."""
import os
from celery import Celery

celery_app = Celery(
    "reportgen",
    broker=os.getenv("CELERY_BROKER_URL", os.getenv("REDIS_URL", "redis://localhost:6379/0")),
    backend=os.getenv("CELERY_RESULT_BACKEND", os.getenv("REDIS_URL", "redis://localhost:6379/0")),
    include=["app.workers.report_task", "app.workers.forecast_task"],
)
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_always_eager=os.getenv("CELERY_TASK_ALWAYS_EAGER", "0") == "1",
)
