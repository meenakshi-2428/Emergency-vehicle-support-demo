from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import settings

engine = create_engine(settings.database_url, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_postgis(db_conn):
    """Enable the PostGIS extension. Safe to call every startup."""
    db_conn.exec_driver_sql("CREATE EXTENSION IF NOT EXISTS postgis;")
