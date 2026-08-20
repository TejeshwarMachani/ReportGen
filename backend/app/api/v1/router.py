"""API v1 router aggregator. All endpoints live under /api/v1."""
from fastapi import APIRouter

from .routers import (
    auth,
    orgs,
    datasets,
    reports,
    reports_library,
    forecast,
    chat,
    team,
    dashboard,
    audit,
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(orgs.router)
api_router.include_router(datasets.router)
api_router.include_router(reports.router)
api_router.include_router(reports_library.router)
api_router.include_router(forecast.router)
api_router.include_router(chat.router)
api_router.include_router(team.router)
api_router.include_router(dashboard.router)
api_router.include_router(audit.router)
