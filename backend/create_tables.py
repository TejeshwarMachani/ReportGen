from app.database import engine
from app.models.organization import Organization
from app.models.user import User
from app.models.dataset import Dataset
from app.models.report import Report
from app.models.chat_session import ChatSession
from app.models.chat_message import ChatMessage
from app.models.forecast_job import ForecastJob
from app.models.scheduled_report import ScheduledReport
from app.models.audit_log import AuditLog
from app.models.base import Base

Base.metadata.create_all(engine)
print('Tables created')

import sqlite3
conn = sqlite3.connect('test.db')
cursor = conn.cursor()
cursor.execute('SELECT name FROM sqlite_master WHERE type=\"table\";')
tables = cursor.fetchall()
print('Tables:', tables)
conn.close()
