
"""Immersive learning experience created by a tutor."""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey, Text, JSON, Integer
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

    title = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False, default="Social Skills")
    prompt = Column(Text, nullable=False)
    voice_transcript = Column(Text, nullable=True)
    attachments = Column(JSON, nullable=False, default=list)

    # Saved workflow data
    answers = Column(JSON, nullable=False, default=dict)
    concept_options = Column(JSON, nullable=True)
    concept_preview = Column(JSON, nullable=True)
    configuration = Column(JSON, nullable=False, default=dict)
    spec = Column(JSON, nullable=True)
    validation_report = Column(JSON, nullable=True)
    current_version = Column(Integer, nullable=False, default=1)
    error_plain = Column(Text, nullable=True)

    # Workflow status: draft, questions, concept_review,
    # preview_approved, generating, ready_to_configure, configured, approved
    status = Column(String(50), nullable=False, default="draft")

    concept_approved_at = Column(DateTime, nullable=True)

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
