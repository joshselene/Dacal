
"""Tutor-facing immersive learning experience endpoints.

Generation is simulated in this prototype; no real AI or 3D
scene generation is performed.
"""

from copy import deepcopy
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import get_current_tutor
from app.models.experience import Experience
from app.models.experience_version import ExperienceVersion
from app.models.tutor import Tutor
from app.schemas.experience import (
    ExperienceAnswersUpdate,
    ExperienceConceptUpdate,
    ExperienceConfigurationUpdate,
    ExperienceCreate,
    ExperienceResponse,
)

router = APIRouter()


def get_experience_or_404(
    db: Session,
    experience_id: UUID,
    current_tutor: Tutor,
) -> Experience:
    """Get an active experience belonging to the tutor's organisation."""
    experience = (
        db.query(Experience)
        .filter(
            Experience.id == experience_id,
            Experience.organisation_id == current_tutor.organisation_id,
            Experience.deleted_at.is_(None),
        )
        .first()
    )

    if experience is None:
        raise HTTPException(
            status_code=404,
            detail="Experience not found.",
        )

    return experience


def create_version_snapshot(
    db: Session,
    experience: Experience,
) -> ExperienceVersion:
    """Save the current configuration as an immutable version snapshot."""
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


@router.post("", response_model=ExperienceResponse, status_code=201)
def create_experience(
    payload: ExperienceCreate,
    db: Session = Depends(get_db),
    current_tutor: Tutor = Depends(get_current_tutor),
):
    experience = Experience(
        organisation_id=current_tutor.organisation_id,
        created_by_tutor_id=current_tutor.id,
        title=payload.title,
        prompt=payload.prompt,
        answers={},
        concept_preview=None,
        configuration={},
        status="draft",
        generation_mode="mock",
    )

    db.add(experience)
    db.commit()
    db.refresh(experience)
    return experience


@router.get("", response_model=list[ExperienceResponse])
def list_experiences(
    db: Session = Depends(get_db),
    current_tutor: Tutor = Depends(get_current_tutor),
):
    return (
        db.query(Experience)
        .filter(
            Experience.organisation_id == current_tutor.organisation_id,
            Experience.deleted_at.is_(None),
        )
        .order_by(Experience.created_at.desc())
        .all()
    )


@router.get("/{experience_id}", response_model=ExperienceResponse)
def get_experience(
    experience_id: UUID,
    db: Session = Depends(get_db),
    current_tutor: Tutor = Depends(get_current_tutor),
):
    return get_experience_or_404(
        db, experience_id, current_tutor
    )


@router.patch(
    "/{experience_id}/answers",
    response_model=ExperienceResponse,
)
def update_answers(
    experience_id: UUID,
    payload: ExperienceAnswersUpdate,
    db: Session = Depends(get_db),
    current_tutor: Tutor = Depends(get_current_tutor),
):
    experience = get_experience_or_404(
        db, experience_id, current_tutor
    )

    if experience.status in {
        "approved",
        "generating",
        "ready_to_configure",
        "configured",
    }:
        raise HTTPException(
            status_code=409,
            detail="Answers cannot be changed at this workflow stage.",
        )

    experience.answers = payload.answers
    experience.status = "questions"
    experience.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(experience)
    return experience


@router.put(
    "/{experience_id}/concept",
    response_model=ExperienceResponse,
)
def update_concept(
    experience_id: UUID,
    payload: ExperienceConceptUpdate,
    db: Session = Depends(get_db),
    current_tutor: Tutor = Depends(get_current_tutor),
):
    experience = get_experience_or_404(
        db, experience_id, current_tutor
    )

    if experience.status in {
        "approved",
        "generating",
        "ready_to_configure",
        "configured",
    }:
        raise HTTPException(
            status_code=409,
            detail="The concept cannot be changed at this workflow stage.",
        )

    experience.concept_preview = payload.concept_preview
    experience.status = "concept_review"
    experience.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(experience)
    return experience


@router.post(
    "/{experience_id}/approve",
    response_model=ExperienceResponse,
)
def approve_concept(
    experience_id: UUID,
    db: Session = Depends(get_db),
    current_tutor: Tutor = Depends(get_current_tutor),
):
    experience = get_experience_or_404(
        db, experience_id, current_tutor
    )

    if not experience.concept_preview:
        raise HTTPException(
            status_code=409,
            detail="Save a concept preview before approving it.",
        )

    if experience.status not in {"concept_review", "approved"}:
        raise HTTPException(
            status_code=409,
            detail="The concept cannot be approved at this workflow stage.",
        )

    experience.status = "approved"
    experience.concept_approved_at = datetime.utcnow()
    experience.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(experience)
    return experience


@router.post(
    "/{experience_id}/generate",
    response_model=ExperienceResponse,
)
def generate_experience(
    experience_id: UUID,
    db: Session = Depends(get_db),
    current_tutor: Tutor = Depends(get_current_tutor),
):
    """Simulate generation so the prototype workflow can be tested."""
    experience = get_experience_or_404(
        db, experience_id, current_tutor
    )

    if experience.status != "approved":
        raise HTTPException(
            status_code=409,
            detail="Only approved experiences can start generation.",
        )

    experience.status = "generating"
    experience.generation_mode = "mock"
    experience.updated_at = datetime.utcnow()

    # Prototype only: this does not call an AI provider or 3D engine.
    experience.status = "ready_to_configure"
    experience.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(experience)
    return experience


@router.patch(
    "/{experience_id}/configuration",
    response_model=ExperienceResponse,
)
def update_configuration(
    experience_id: UUID,
    payload: ExperienceConfigurationUpdate,
    db: Session = Depends(get_db),
    current_tutor: Tutor = Depends(get_current_tutor),
):
    experience = get_experience_or_404(
        db, experience_id, current_tutor
    )

    if experience.status not in {
        "ready_to_configure",
        "configured",
    }:
        raise HTTPException(
            status_code=409,
            detail="Generation must be complete before configuration.",
        )

    experience.configuration = payload.configuration
    experience.status = "configured"
    experience.updated_at = datetime.utcnow()

    # Save the new configuration and its version in one transaction.
    create_version_snapshot(db, experience)

    db.commit()
    db.refresh(experience)
    return experience
