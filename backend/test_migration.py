import os
import sys

os.chdir("E:\\files\\backend")

from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool

from alembic import context

config = context.config

if config.config_file_name and os.path.isfile(config.config_file_name):
    fileConfig(config.config_file_name)

sys.path.insert(0, os.path.dirname(os.path.realpath(".")))

from sqlalchemy import MetaData
from app.models.organization import Organization
from app.models.user import User
from app.models.dataset import Dataset
from app.models.report import Report
from app.models.chat_session import ChatSession
from app.models.chat_message import ChatMessage
from app.models.forecast_job import ForecastJob
from app.models.scheduled_report import ScheduledReport

target_metadata = MetaData()
target_metadata.add_entity(Organization)
target_metadata.add_entity(User)
target_metadata.add_entity(Dataset)
target_metadata.add_entity(Report)
target_metadata.add_entity(ChatSession)
target_metadata.add_entity(ChatMessage)
target_metadata.add_entity(ForecastJob)
target_metadata.add_entity(ScheduledReport)

print("All models imported successfully!")

# Now try running alembic
from alembic import command
from alembic.config import Config

alembic_cfg = Config("alembic.ini")
command.upgrade(alembic_cfg, "head")
print("Migration completed successfully!")