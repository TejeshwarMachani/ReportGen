import os
import sys

from sqlalchemy import engine_from_config, pool

from alembic import context

config = context.config

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__ + "/../..")))

from app.models.base import Base
from app.models.organization import Organization
from app.models.user import User
from app.models.dataset import Dataset
from app.models.report import Report
from app.models.chat_session import ChatSession
from app.models.chat_message import ChatMessage
from app.models.forecast_job import ForecastJob
from app.models.scheduled_report import ScheduledReport
from app.models.audit_log import AuditLog

target_metadata = Base.metadata
