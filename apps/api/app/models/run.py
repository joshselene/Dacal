"""Scenario runtime session model for laptop and four-wall room execution (FR-11, FR-12, FR-16)."""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID

from .base import Base


class ScenarioRun(Base):
    __tablename__ = "runs"

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
    version_id = Column(
        UUID(as_uuid=True),
        ForeignKey("experience_versions.id"),
        nullable=False,
    )
    version_number = Column(Integer, nullable=False)
    learner_id = Column(
        UUID(as_uuid=True),
        ForeignKey("students.id"),
        nullable=True,
        index=True,
    )
    created_by_tutor_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tutors.id"),
        nullable=False,
    )

    pathway = Column(String(10), nullable=False, default="B")
    mode = Column(String(20), nullable=False, default="laptop")
    status = Column(String(30), nullable=False, default="running")

    learner_position = Column(
        JSON,
        nullable=False,
        default=lambda: {"x": 5, "y": 7, "dir": "N"},
    )
    basket = Column(JSON, nullable=False, default=list)
    steps_completed = Column(JSON, nullable=False, default=list)
    prompts_given = Column(Integer, nullable=False, default=0)
    tutor_decisions = Column(Integer, nullable=False, default=0)
    errors_count = Column(Integer, nullable=False, default=0)
    active_what_if = Column(String(255), nullable=True)
    compiled_config = Column(JSON, nullable=False, default=dict)

    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    ended_at = Column(DateTime, nullable=True)
    elapsed_ms = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
