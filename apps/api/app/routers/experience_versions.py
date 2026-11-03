
"""Version management for immersive learning experiences."""

from copy import deepcopy
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import get_current_tutor, require_roles
from app.models.experience import Experience
from app.models.experience_version import ExperienceVersion
from app.models.tutor import Tutor
from app.schemas.experience import ExperienceResponse
from app.schemas.experience_version import (
    ExperienceVersionCreate,
    ExperienceVersionResponse,
)
from app.services.validator import get_reference_scene_spec, validate_scene_spec

router = APIRouter()


def get_owned_experience(
    db: Session,
    experience_id: UUID,
    current_tutor: Tutor,
) -> Experience:
    experience = (
        db.query(Experience)
        .filter(
            Experience.id == experience_id,
            Experience.organisation_id == current_tutor.organisation_id,
            Experience.deleted_at.is_(None),
        )
        .first()
    )

    if not experience:
        raise HTTPException(
            status_code=404,
            detail="Experience not found.",
        )

    return experience


def save_version(
    db: Session,
    experience: Experience,
    state: str = "approved",
    approved_by: UUID | None = None,
) -> ExperienceVersion:
    latest_version = (
        db.query(func.max(ExperienceVersion.version_number))
        .filter(ExperienceVersion.experience_id == experience.id)
        .scalar()
    )
    next_num = (latest_version or 0) + 1
    experience.current_version = next_num

    spec_snapshot = deepcopy(experience.spec or get_reference_scene_spec())
    report = deepcopy(experience.validation_report or validate_scene_spec(spec_snapshot))

    version = ExperienceVersion(
        experience_id=experience.id,
        version_number=next_num,
        state=state,
        configuration_snapshot=deepcopy(experience.configuration or {}),
        spec=spec_snapshot,
        validation_report=report,
        approved_by=approved_by,
        approved_at=datetime.utcnow() if approved_by else None,
    )

    db.add(version)
    db.flush()
    return version


@router.post(
    "/{experience_id}/versions",
    response_model=ExperienceVersionResponse,
)
def create_version(
    experience_id: UUID,
    payload: ExperienceVersionCreate,
    db: Session = Depends(get_db),
    current_tutor: Tutor = Depends(require_roles("tutor", "admin")),
):
    experience = get_owned_experience(db, experience_id, current_tutor)

    experience.configuration = payload.configuration_snapshot
    if payload.spec is not None:
        experience.spec = payload.spec
        experience.validation_report = validate_scene_spec(payload.spec)
    experience.status = "approved"
    experience.updated_at = datetime.utcnow()

    version = save_version(
        db,
        experience,
        state="approved",
        approved_by=current_tutor.id,
    )

    db.commit()
    db.refresh(version)
    return version


@router.get(
    "/{experience_id}/versions",
    response_model=list[ExperienceVersionResponse],
)
def list_versions(
    experience_id: UUID,
    db: Session = Depends(get_db),
    current_tutor: Tutor = Depends(get_current_tutor),
):
    get_owned_experience(db, experience_id, current_tutor)

    return (
        db.query(ExperienceVersion)
        .filter(ExperienceVersion.experience_id == experience_id)
        .order_by(ExperienceVersion.version_number.desc())
        .all()
    )


@router.post(
    "/{experience_id}/versions/{version_id}/restore",
    response_model=ExperienceResponse,
)
def restore_version(
    experience_id: UUID,
    version_id: UUID,
    db: Session = Depends(get_db),
    current_tutor: Tutor = Depends(require_roles("tutor", "admin")),
):
    experience = get_owned_experience(db, experience_id, current_tutor)

    version = (
        db.query(ExperienceVersion)
        .filter(
            ExperienceVersion.id == version_id,
            ExperienceVersion.experience_id == experience.id,
        )
        .first()
    )

    if not version:
        raise HTTPException(
            status_code=404,
            detail="Version not found for this experience.",
        )

    experience.configuration = deepcopy(version.configuration_snapshot)
    if version.spec is not None:
        experience.spec = deepcopy(version.spec)
        experience.validation_report = deepcopy(version.validation_report)

    # Preserve history by recording the restored state as a new version.
    save_version(db, experience, state="ready_to_configure")

    db.commit()
    db.refresh(experience)
    return experience


@router.post(
    "/{experience_id}/duplicate",
    response_model=ExperienceResponse,
    status_code=201,
)
def duplicate_experience(
    experience_id: UUID,
    db: Session = Depends(get_db),
    current_tutor: Tutor = Depends(require_roles("tutor", "admin")),
):
    original = get_owned_experience(db, experience_id, current_tutor)

    duplicate = Experience(
        organisation_id=original.organisation_id,
        created_by_tutor_id=current_tutor.id,
        class_id=original.class_id,
        module_id=original.module_id,
        title=f"{original.title} (Copy)",
        category=original.category,
        prompt=original.prompt,
        voice_transcript=original.voice_transcript,
        attachments=deepcopy(original.attachments or []),
        answers=deepcopy(original.answers or {}),
        concept_options=deepcopy(original.concept_options),
        concept_preview=deepcopy(original.concept_preview),
        configuration=deepcopy(original.configuration or {}),
        spec=deepcopy(original.spec),
        validation_report=deepcopy(original.validation_report),
        status="draft",
        generation_mode=original.generation_mode or "mock",
    )

    db.add(duplicate)
    db.flush()

    save_version(db, duplicate, state="draft")

    db.commit()
    db.refresh(duplicate)
    return duplicate
