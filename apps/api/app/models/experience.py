
"""Immersive learning experience created by a tutor."""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.dialects.postgresql import UUID

from .base import Base


class Experience(Base):
    __tablename__ = "experiences"

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

    title = Column(String(255), nullable=False)
    prompt = Column(Text, nullable=False)

    # Saved workflow data
    answers = Column(JSON, nullable=False, default=dict)
    concept_preview = Column(JSON, nullable=True)
    configuration = Column(JSON, nullable=False, default=dict)

    # Workflow status: draft, questions, concept_review,
    # approved, generating, ready_to_configure
    status = Column(String(50), nullable=False, default="draft")

    concept_approved_at = Column(DateTime, nullable=True)

    # This prototype does not connect to an actual AI/3D generator.
    generation_mode = Column(
        String(50),
        nullable=False,
        default="mock",
    )

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
    deleted_at = Column(DateTime, nullable=True)
