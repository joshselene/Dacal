
import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey, Time, Date, Text
from sqlalchemy.dialects.postgresql import UUID

from .base import Base


class ClassSchedule(Base):
    __tablename__ = "class_schedules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    class_id = Column(
        UUID(as_uuid=True),
        ForeignKey("classes.id"),
        nullable=False,
        index=True,
    )

    title = Column(String(255), nullable=False)
    scheduled_date = Column(Date, nullable=True)
    day_of_week = Column(String(20), nullable=True)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
