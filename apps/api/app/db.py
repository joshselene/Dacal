"""Database connection utilities for FastAPI backend.

Provides a SQLAlchemy engine and a session factory, plus a FastAPI dependency
`get_db` that yields a session and ensures it is closed after the request.
"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DEFAULT_PG_URL = "postgresql+psycopg2://postgres:1112@localhost:1112/cheranyx"
DEFAULT_SQLITE_URL = "sqlite:///./chernyx.db"


def _resolve_database_url() -> str:
    env_url = os.getenv("DATABASE_URL")
    if env_url:
        return env_url
    try:
        test_engine = create_engine(
            DEFAULT_PG_URL,
            connect_args={"connect_timeout": 1},
        )
        with test_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        test_engine.dispose()
        return DEFAULT_PG_URL
    except Exception:
        return DEFAULT_SQLITE_URL


DATABASE_URL = _resolve_database_url()

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
