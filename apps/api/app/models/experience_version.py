"""Version snapshots for immersive learning experiences."""

import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
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

    configuration_snapshot = Column(JSON, nullable=False)

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )