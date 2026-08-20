from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from .core.config import settings
from .models.base import Base

# SQLite doesn't support pool settings
connect_args = {}
if settings.DATABASE_URL.startswith('sqlite'):
    connect_args = {'check_same_thread': False}

engine = create_engine(
    settings.DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    echo=False,
    connect_args=connect_args,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=True, bind=engine)

get_db = lambda: SessionLocal()
