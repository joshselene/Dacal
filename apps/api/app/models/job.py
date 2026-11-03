"""Background generation and validation job model (LC-2, FR-06, FR-15)."""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Text, JSON
from sqlalchemy.dialects.postgresql import UUID

from .base import Base


class JobRecord(Base):
    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organisation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organisations.id"),
        nullable=False,
        index=True,
    )
    experience_id = Column(
        UUID(as_uuid=True),
        ForeignKey("experiences.id"),
        nullable=False,
        index=True,
    )
    version_number = Column(Integer, nullable=False, default=1)
    idempotency_key = Column(String(255), nullable=False, unique=True, index=True)
    kind = Column(String(50), nullable=False, default="scene_generation")
    status = Column(String(50), nullable=False, default="queued")
    attempt = Column(Integer, nullable=False, default=1)
    max_attempts = Column(Integer, nullable=False, default=3)
    error_plain = Column(Text, nullable=True)
    validation_report = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
