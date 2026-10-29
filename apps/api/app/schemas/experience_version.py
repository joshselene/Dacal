"""Schemas for experience version management."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ExperienceVersionCreate(BaseModel):
    configuration_snapshot: dict = Field(default_factory=dict)


class ExperienceVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    experience_id: UUID
    version_number: int
    configuration_snapshot: dict
    created_at: datetime