"""Version snapshots for immersive learning experiences."""

import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
)
from sqlalchemy.dialects.postgresql import UUID

from .base import Base


class ExperienceVersion(Base):
    __tablename__ = "experience_versions"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    experience_id = Column(
        UUID(as_uuid=True),
        ForeignKey("experiences.id"),
        nullable=False,
        index=True,
    )

    version_number = Column(Integer, nullable=False)
    state = Column(String(50), nullable=False, default="ready_to_configure")

    configuration_snapshot = Column(JSON, nullable=False, default=dict)
    spec = Column(JSON, nullable=True)
    validation_report = Column(JSON, nullable=True)

    approved_by = Column(UUID(as_uuid=True), ForeignKey("tutors.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )