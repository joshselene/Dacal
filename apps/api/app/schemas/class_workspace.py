
from datetime import date, time, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StudentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    pseudonym_id: str | None = Field(default=None, max_length=64)
    display_name_opt_in: bool = False
    comfort_overrides: dict[str, Any] | None = None


class StudentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    display_name_opt_in: bool | None = None
    comfort_overrides: dict[str, Any] | None = None


class StudentResponse(BaseModel):
    id: UUID
    class_id: UUID
    pseudonym_id: str
    name: str
    display_name_opt_in: bool = False
    comfort_overrides: dict[str, Any] | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ModuleCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None


class ModuleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None


class ModuleResponse(BaseModel):
    id: UUID
    organisation_id: UUID
    class_id: UUID
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ScheduleCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    scheduled_date: date | None = None
    day_of_week: str | None = Field(default=None, max_length=20)
    start_time: time
    end_time: time
    notes: str | None = None

    @model_validator(mode="after")
    def validate_times(self):
        if self.end_time <= self.start_time:
            raise ValueError("End time must be later than start time")
        if self.scheduled_date is None and self.day_of_week is None:
            raise ValueError(
                "Provide a scheduled date or a day of the week"
            )
        return self


class ScheduleResponse(BaseModel):
    id: UUID
    class_id: UUID
    title: str
    scheduled_date: date | None
    day_of_week: str | None
    start_time: time
    end_time: time
    notes: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ClassWorkspaceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None


class ClassWorkspaceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None


class ClassWorkspaceResponse(BaseModel):
    id: UUID
    organisation_id: UUID
    name: str
    description: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
