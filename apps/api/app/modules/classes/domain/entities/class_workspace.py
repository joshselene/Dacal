"""Domain entities for the Classes & Modules bounded context."""

from dataclasses import dataclass
from datetime import date, datetime, time
from typing import Any
from uuid import UUID


@dataclass
class ClassroomEntity:
    id: UUID
    organisation_id: UUID
    name: str
    description: str | None
    created_at: datetime


@dataclass
class ModuleEntity:
    id: UUID
    organisation_id: UUID
    class_id: UUID
    name: str
    description: str | None
    created_at: datetime


@dataclass
class StudentEntity:
    id: UUID
    class_id: UUID
    pseudonym_id: str
    name: str
    display_name_opt_in: bool
    comfort_overrides: dict[str, Any] | None
    created_at: datetime


@dataclass
class ScheduleEntity:
    id: UUID
    class_id: UUID
    title: str
    scheduled_date: date | None
    day_of_week: str | None
    start_time: time
    end_time: time
    notes: str | None
    created_at: datetime
