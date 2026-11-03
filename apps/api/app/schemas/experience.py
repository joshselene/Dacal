
"""Request and response schemas for immersive experiences."""

from datetime import datetime
from uuid import UUID
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ExperienceCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    prompt: str = Field(..., min_length=1)
    category: str = Field(default="Social Skills", max_length=100)
    class_id: UUID | None = None
    module_id: UUID | None = None
    voice_transcript: str | None = None
    attachments: list[dict[str, Any]] = Field(default_factory=list)


class ExperienceUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    prompt: str | None = Field(default=None, min_length=1)
    category: str | None = Field(default=None, max_length=100)
    class_id: UUID | None = None
    module_id: UUID | None = None
    voice_transcript: str | None = None
    attachments: list[dict[str, Any]] | None = None


class ExperienceAnswersUpdate(BaseModel):
    answers: dict[str, Any] = Field(default_factory=dict)


class ExperienceConceptUpdate(BaseModel):
    concept_preview: dict[str, Any]


class ExperienceConfigurationUpdate(BaseModel):
    configuration: dict[str, Any]
    spec: dict[str, Any] | None = None


class PlainLanguageEditRequest(BaseModel):
    instruction: str = Field(..., min_length=1)


class ExperienceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organisation_id: UUID
    created_by_tutor_id: UUID
    class_id: UUID | None = None
    module_id: UUID | None = None
    title: str
    category: str = "Social Skills"
    prompt: str
    voice_transcript: str | None = None
    attachments: list[dict[str, Any]] = Field(default_factory=list)
    answers: dict[str, Any]
    concept_options: list[dict[str, Any]] | None = None
    concept_preview: dict[str, Any] | None
    configuration: dict[str, Any]
    spec: dict[str, Any] | None = None
    validation_report: dict[str, Any] | None = None
    current_version: int = 1
    error_plain: str | None = None
    status: str
    generation_mode: str
    concept_approved_at: datetime | None
    created_at: datetime
    updated_at: datetime
