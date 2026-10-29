
"""Request and response schemas for immersive experiences."""

from datetime import datetime
from uuid import UUID
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ExperienceCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    prompt: str = Field(..., min_length=1)


class ExperienceAnswersUpdate(BaseModel):
    answers: dict[str, Any] = Field(default_factory=dict)


class ExperienceConceptUpdate(BaseModel):
    concept_preview: dict[str, Any]


class ExperienceConfigurationUpdate(BaseModel):
    configuration: dict[str, Any]


class ExperienceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organisation_id: UUID
    created_by_tutor_id: UUID
    title: str
    prompt: str
    answers: dict[str, Any]
    concept_preview: dict[str, Any] | None
    configuration: dict[str, Any]
    status: str
    generation_mode: str
    concept_approved_at: datetime | None
    created_at: datetime
    updated_at: datetime
