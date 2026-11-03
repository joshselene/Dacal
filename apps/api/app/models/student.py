
import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey, Index, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID

from .base import Base


def _default_pseudonym() -> str:
    return f"LRN-{uuid.uuid4().hex[:6].upper()}"


class Student(Base):
    __tablename__ = "students"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    class_id = Column(
        UUID(as_uuid=True),
        ForeignKey("classes.id"),
        nullable=False,
        index=True,
    )

    pseudonym_id = Column(String(64), nullable=False, default=_default_pseudonym)
    name = Column(String(255), nullable=False)
    display_name_opt_in = Column(Boolean, default=False, nullable=False)
    comfort_overrides = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    __table_args__ = (
        Index("ix_students_class_name", "class_id", "name"),
    )
