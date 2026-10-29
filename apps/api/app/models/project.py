
"""Learning project model created by a tutor."""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID

from .base import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organisation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organisations.id"),
        nullable=False,
        index=True,
    )
    created_by_tutor_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tutors.id"),
        nullable=False,
    )
    class_id = Column(
        UUID(as_uuid=True),
        ForeignKey("classes.id"),
        nullable=True,
        index=True,
    )
    module_id = Column(
        UUID(as_uuid=True),
        ForeignKey("modules.id"),
        nullable=True,
        index=True,
    )

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), default="draft", nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
    deleted_at = Column(DateTime, nullable=True)
