"""Schemas for experience version management."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ExperienceVersionCreate(BaseModel):
    configuration_snapshot: dict[str, Any] = Field(default_factory=dict)
    spec: dict[str, Any] | None = None


class ExperienceVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    experience_id: UUID
    version_number: int
    state: str = "ready_to_configure"
    configuration_snapshot: dict[str, Any]
    spec: dict[str, Any] | None = None
    validation_report: dict[str, Any] | None = None
    approved_by: UUID | None = None
    approved_at: datetime | None = None
    created_at: datetime