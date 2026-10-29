
"""Version management for immersive learning experiences."""

from copy import deepcopy
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import get_current_tutor
from app.models.experience import Experience
from app.models.experience_version import ExperienceVersion
from app.models.tutor import Tutor
from app.schemas.experience import ExperienceResponse
from app.schemas.experience_version import (
    ExperienceVersionCreate,
    ExperienceVersionResponse,
)

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
) -> ExperienceVersion:
    latest_version = (
        db.query(func.max(ExperienceVersion.version_number))
        .filter(
            ExperienceVersion.experience_id == experience.id
        )
        .scalar()
    )

    version = ExperienceVersion(
        experience_id=experience.id,
        version_number=(latest_version or 0) + 1,
        configuration_snapshot=deepcopy(
            experience.configuration or {}
        ),
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
    current_tutor: Tutor = Depends(get_current_tutor),
):
    experience = get_owned_experience(
        db, experience_id, current_tutor
    )

    experience.configuration = payload.configuration_snapshot
    version = save_version(db, experience)

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
        .filter(
            ExperienceVersion.experience_id == experience_id
        )
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
    current_tutor: Tutor = Depends(get_current_tutor),
):
    experience = get_owned_experience(
        db, experience_id, current_tutor
    )

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

    experience.configuration = deepcopy(
        version.configuration_snapshot
    )

    # Preserve history by recording the restored state as a new version.
    save_version(db, experience)

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
    current_tutor: Tutor = Depends(get_current_tutor),
):
    original = get_owned_experience(
        db, experience_id, current_tutor
    )

    duplicate = Experience(
        organisation_id=original.organisation_id,
        created_by_tutor_id=current_tutor.id,
        title=f"{original.title} (Copy)",
        prompt=original.prompt,
        answers=deepcopy(original.answers or {}),
        concept_preview=deepcopy(original.concept_preview),
        configuration=deepcopy(original.configuration or {}),
        status="draft",
        generation_mode="mock",
    )

    db.add(duplicate)
    db.flush()

    save_version(db, duplicate)

    db.commit()
    db.refresh(duplicate)
    return duplicate
