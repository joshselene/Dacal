
import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID

from .base import Base


class Student(Base):
    __tablename__ = "students"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    class_id = Column(
        UUID(as_uuid=True),
        ForeignKey("classes.id"),
        nullable=False,
        index=True,
    )

    name = Column(String(255), nullable=False)
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
