"""Non-diagnostic session notebook event model (Section 8: NB-01 to NB-05).

Hard product rule NB-02: No column or property in this model may use any
diagnostic or evaluative naming (no score, grade, rating, level, diagnosis,
risk, percentile, or label). Counts and times only.
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID

from .base import Base


class NotebookEvent(Base):
    __tablename__ = "notebook_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organisation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organisations.id"),
        nullable=False,
        index=True,
    )
    run_id = Column(
        UUID(as_uuid=True),
        ForeignKey("runs.id"),
        nullable=False,
        index=True,
    )
    learner_id = Column(
        UUID(as_uuid=True),
        ForeignKey("students.id"),
        nullable=True,
        index=True,
    )

    kind = Column(String(64), nullable=False)
    step_id = Column(String(128), nullable=True)
    pathway = Column(String(10), nullable=False, default="B")
    t_ms = Column(Integer, nullable=False, default=0)
    event_data = Column(JSON, nullable=False, default=dict)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
