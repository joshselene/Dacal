"""Database connection utilities for FastAPI backend.

Provides a SQLAlchemy engine and a session factory, plus a FastAPI dependency
`get_db` that yields a session and ensures it is closed after the request.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, Session
from contextlib import contextmanager

# Default database URL – can be overridden via the DATABASE_URL env var.

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql+psycopg2://postgres:1112@localhost:1112/cheranyx"

engine = create_engine(DATABASE_URL)

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
