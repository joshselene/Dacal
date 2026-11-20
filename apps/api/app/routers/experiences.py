
"""Tutor-facing immersive learning experience / scenario endpoints.

Implements the Plan–Validate–Build workflow (SRS Sections 3–6):
- FR-03 & FR-04: Prompt/voice/attachment intake and 20 skippable questions
- FR-05: Three concept previews and explicit Start generating gate
- FR-06 & FR-07: Background job record, configuration lock (409 before Ready),
  and in-app notification on completion (LC-6)
- FR-08: Plain-language localized patch editing (< 10% spec bytes)
- FR-10: Configuration round-tripping through validated scene spec
- FR-11 & FR-13: Version snapshots, approval for launch, duplication
- FR-14 & FR-15: R1–R7 constraint layer and k=3 bounded repair loop
"""

from copy import deepcopy
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import get_current_tutor, require_roles
from app.models.audit_event import AuditEvent
from app.models.experience import Experience
from app.models.experience_version import ExperienceVersion
from app.models.job import JobRecord
from app.models.notification import Notification
from app.models.tutor import Tutor
from app.schemas.experience import (
    ExperienceAnswersUpdate,
    ExperienceConceptUpdate,
    ExperienceConfigurationUpdate,
    ExperienceCreate,
    ExperienceResponse,
    ExperienceUpdate,
    PlainLanguageEditRequest,
)
from app.services.ai_provider import generate_with_repair_loop, get_ai_provider, with_preview_images
from app.services.validator import get_reference_scene_spec, validate_scene_spec

router = APIRouter()


def _log_audit(
    db: Session,
    tutor: Tutor,
    action: str,
    ref_id: UUID | None = None,
    version_number: int | None = None,
    details: dict | None = None,
) -> None:
    event = AuditEvent(
        organisation_id=tutor.organisation_id,
        user_id=tutor.id,
        action=action,
        ref_id=ref_id,
        version_number=version_number,
        details=details or {},
    )
    db.add(event)


def _notify_tutor(
    db: Session,
    tutor: Tutor,
    kind: str,
    title: str,
    message: str,
    ref_id: UUID | None = None,
) -> None:
    notif = Notification(
        organisation_id=tutor.organisation_id,
        user_id=tutor.id,
        kind=kind,
        title=title,
        message=message,
        ref_id=ref_id,
    )
    db.add(notif)


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
    state: str = "ready_to_configure",
    approved_by: UUID | None = None,
) -> ExperienceVersion:
    """Save the current configuration and spec as a version snapshot."""
    latest_version = (
        db.query(func.max(ExperienceVersion.version_number))
        .filter(ExperienceVersion.experience_id == experience.id)
        .scalar()
    )
    next_num = (latest_version or 0) + 1
    experience.current_version = next_num

    version = ExperienceVersion(
        experience_id=experience.id,
        version_number=next_num,
        state=state,
        configuration_snapshot=deepcopy(experience.configuration or {}),
        spec=deepcopy(experience.spec),
        validation_report=deepcopy(experience.validation_report),
        approved_by=approved_by,
        approved_at=datetime.utcnow() if approved_by else None,
    )

    db.add(version)
    db.flush()
    return version


@router.post("", response_model=ExperienceResponse, status_code=201)
def create_experience(
    payload: ExperienceCreate,
    db: Session = Depends(get_db),
    current_tutor: Tutor = Depends(require_roles("tutor", "admin")),
):
    provider = get_ai_provider()
    concepts = provider.generate_concepts(payload.prompt, {})
    experience = Experience(
        organisation_id=current_tutor.organisation_id,
        created_by_tutor_id=current_tutor.id,
        class_id=payload.class_id,
        module_id=payload.module_id,
        title=payload.title.strip(),
        category=payload.category,
        prompt=payload.prompt,
        voice_transcript=payload.voice_transcript,
        attachments=payload.attachments or [],
        answers={},
        concept_options=concepts,
        concept_preview=None,
        configuration={},
        spec=None,
        validation_report=None,
        current_version=1,
        status="draft",
        generation_mode=provider.name,
    )

    db.add(experience)
    db.flush()
    _log_audit(db, current_tutor, "create_draft", experience.id, 1, {"title": experience.title})
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
    return get_experience_or_404(db, experience_id, current_tutor)


@router.patch("/{experience_id}", response_model=ExperienceResponse)
def update_experience(
    experience_id: UUID,
    payload: ExperienceUpdate,
    db: Session = Depends(get_db),
    current_tutor: Tutor = Depends(require_roles("tutor", "admin")),
):
    experience = get_experience_or_404(db, experience_id, current_tutor)
    changes = payload.model_dump(exclude_unset=True)
    for k, v in changes.items():
        if k == "title" and v is not None:
            v = v.strip()
        setattr(experience, k, v)
    experience.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(experience)
    return experience


@router.delete("/{experience_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_experience(
    experience_id: UUID,
    db: Session = Depends(get_db),
    current_tutor: Tutor = Depends(require_roles("tutor", "admin")),
):
    experience = get_experience_or_404(db, experience_id, current_tutor)
    experience.deleted_at = datetime.utcnow()
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch(
    "/{experience_id}/answers",
    response_model=ExperienceResponse,
)
def update_answers(
    experience_id: UUID,
    payload: ExperienceAnswersUpdate,
    db: Session = Depends(get_db),
    current_tutor: Tutor = Depends(require_roles("tutor", "admin")),
):
    experience = get_experience_or_404(db, experience_id, current_tutor)

    if experience.status in {
        "approved",
        "preview_approved",
        "generating",
        "ready_to_configure",
        "configured",
        "live",
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


@router.post("/{experience_id}/concepts")
def generate_concept_previews(
    experience_id: UUID,
    db: Session = Depends(get_db),
    current_tutor: Tutor = Depends(require_roles("tutor", "admin")),
):
    """Return three concept previews for the scenario (FR-05)."""
    experience = get_experience_or_404(db, experience_id, current_tutor)
    provider = get_ai_provider()
    concepts = provider.generate_concepts(experience.prompt, experience.answers)
    concepts = with_preview_images(provider, concepts, experience.prompt)
    experience.concept_options = concepts
    experience.updated_at = datetime.utcnow()
    db.commit()
    return {"concepts": concepts}


@router.put(
    "/{experience_id}/concept",
    response_model=ExperienceResponse,
)
def update_concept(
    experience_id: UUID,
    payload: ExperienceConceptUpdate,
    db: Session = Depends(get_db),
    current_tutor: Tutor = Depends(require_roles("tutor", "admin")),
):
    experience = get_experience_or_404(db, experience_id, current_tutor)

    if experience.status in {
        "approved",
        "preview_approved",
        "generating",
        "ready_to_configure",
        "configured",
        "live",
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
    current_tutor: Tutor = Depends(require_roles("tutor", "admin")),
):
    experience = get_experience_or_404(db, experience_id, current_tutor)

    if not experience.concept_preview:
        raise HTTPException(
            status_code=409,
            detail="Save a concept preview before approving it.",
        )

    if experience.status not in {"concept_review", "approved", "preview_approved"}:
        raise HTTPException(
            status_code=409,
            detail="The concept cannot be approved at this workflow stage.",
        )

    experience.status = "approved"
    experience.concept_approved_at = datetime.utcnow()
    experience.updated_at = datetime.utcnow()
    _log_audit(db, current_tutor, "approve_preview", experience.id, experience.current_version)

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
    current_tutor: Tutor = Depends(require_roles("tutor", "admin")),
):
    """Explicit Start generating gate (FR-05, FR-06, FR-14, FR-15, LC-2, LC-3, LC-6)."""
    experience = get_experience_or_404(db, experience_id, current_tutor)

    if experience.status not in {"approved", "preview_approved"}:
        raise HTTPException(
            status_code=409,
            detail="Only approved experiences can start generation.",
        )

    # Idempotency key: (scenario_id, version, attempt_batch) per LC-2
    idem_key = f"{experience.id}:v{experience.current_version}:gen"
    existing_job = db.query(JobRecord).filter(JobRecord.idempotency_key == idem_key).first()
    if existing_job and existing_job.status == "completed" and experience.status == "ready_to_configure":
        return experience

    experience.status = "generating"
    experience.updated_at = datetime.utcnow()

    result = generate_with_repair_loop(
        prompt=experience.prompt,
        answers=experience.answers,
        concept=experience.concept_preview,
        max_retries=3,
    )

    if existing_job is None:
        job = JobRecord(
            organisation_id=current_tutor.organisation_id,
            experience_id=experience.id,
            version_number=experience.current_version,
            idempotency_key=idem_key,
            kind="scene_generation",
            status="completed" if result["success"] else "failed",
            attempt=result["attempts"],
            max_attempts=3,
            error_plain=result["error_plain"],
            validation_report=result["validation_report"],
        )
        db.add(job)
    else:
        existing_job.status = "completed" if result["success"] else "failed"
        existing_job.attempt = result["attempts"]
        existing_job.error_plain = result["error_plain"]
        existing_job.validation_report = result["validation_report"]

    if not result["success"]:
        # LC-3: Move back to Preview approved and store plain-language reason
        experience.status = "approved"
        experience.error_plain = result["error_plain"]
        experience.validation_report = result["validation_report"]
        experience.updated_at = datetime.utcnow()
        _notify_tutor(
            db,
            current_tutor,
            "generation_failed",
            f"Generation needs attention: {experience.title}",
            result["error_plain"] or "Scene generation could not satisfy safety constraints.",
            experience.id,
        )
        _log_audit(
            db,
            current_tutor,
            "generate_failed",
            experience.id,
            experience.current_version,
            {"attempts": result["attempts"], "error_plain": result["error_plain"]},
        )
        db.commit()
        db.refresh(experience)
        return experience

    experience.spec = result["spec"]
    experience.validation_report = result["validation_report"]
    experience.error_plain = None
    experience.status = "ready_to_configure"
    experience.updated_at = datetime.utcnow()

    # Sync default configuration from spec
    if not experience.configuration:
        experience.configuration = {
            "environment": "Classroom",
            "duration": "5–10 minutes",
            "guidance": "Step-by-step",
            "visualStyle": "Soft 3D",
            "accessibility": "Visual prompts",
            "comfort": "Low stimulation",
            "budget": result["spec"]["task"]["budget"],
            "required": result["spec"]["task"]["required"],
            "support": result["spec"]["support"],
        }

    create_version_snapshot(db, experience, state="ready_to_configure")
    _notify_tutor(
        db,
        current_tutor,
        "ready_to_configure",
        f"Ready to configure: {experience.title}",
        f"'{experience.title}' passed all R1–R7 checks and is ready to configure.",
        experience.id,
    )
    _log_audit(
        db,
        current_tutor,
        "generate",
        experience.id,
        experience.current_version,
        {"attempts": result["attempts"]},
    )

    db.commit()
    db.refresh(experience)
    return experience


@router.post("/{experience_id}/edit")
def plain_language_edit(
    experience_id: UUID,
    payload: PlainLanguageEditRequest,
    db: Session = Depends(get_db),
    current_tutor: Tutor = Depends(require_roles("tutor", "admin")),
):
    """Apply a localized plain-language patch to the scene spec (FR-08, FR-14, LC-4, AT-03)."""
    experience = get_experience_or_404(db, experience_id, current_tutor)

    if experience.status not in {"ready_to_configure", "configured", "approved", "live"}:
        raise HTTPException(
            status_code=409,
            detail="Plain-language editing is locked until the experience is Ready to configure.",
        )

    base_spec = experience.spec or get_reference_scene_spec()
    provider = get_ai_provider()
    patch_result = provider.apply_plain_language_edit(base_spec, payload.instruction)
    patched_spec = patch_result["patched_spec"]
    report = validate_scene_spec(patched_spec)

    if not report["valid"]:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Edit rejected by constraint validator R1–R7.",
                "validation_report": report,
                "patch_ratio": patch_result["patch_ratio"],
            },
        )

    experience.spec = patched_spec
    experience.validation_report = report
    # LC-4: Any edit to a Ready, Configured or Live version creates version n+1
    # which re-enters configuration/approval; old approved versions remain in version history.
    experience.status = "ready_to_configure"
    experience.updated_at = datetime.utcnow()

    new_version = create_version_snapshot(db, experience, state="ready_to_configure")
    _log_audit(
        db,
        current_tutor,
        "edit",
        experience.id,
        new_version.version_number,
        {
            "instruction": payload.instruction,
            "patch_ratio": patch_result["patch_ratio"],
            "patch_ops": patch_result["patch_ops"],
        },
    )
    db.commit()
    db.refresh(experience)

    return {
        "experience": ExperienceResponse.model_validate(experience).model_dump(),
        "version_number": new_version.version_number,
        "patch_ops": patch_result["patch_ops"],
        "patch_bytes": patch_result["patch_bytes"],
        "spec_bytes": patch_result["spec_bytes"],
        "patch_ratio": patch_result["patch_ratio"],
        "validation_report": report,
    }


@router.patch(
    "/{experience_id}/configuration",
    response_model=ExperienceResponse,
)
def update_configuration(
    experience_id: UUID,
    payload: ExperienceConfigurationUpdate,
    db: Session = Depends(get_db),
    current_tutor: Tutor = Depends(require_roles("tutor", "admin")),
):
    experience = get_experience_or_404(db, experience_id, current_tutor)

    if experience.status not in {
        "ready_to_configure",
        "configured",
        "approved",
        "live",
    }:
        raise HTTPException(
            status_code=409,
            detail="Generation must be complete before configuration.",
        )

    candidate_spec = deepcopy(payload.spec or experience.spec or get_reference_scene_spec())

    # Round-trip task and support settings from configuration into spec (FR-10)
    cfg = payload.configuration or {}
    if "budget" in cfg and cfg["budget"] is not None:
        candidate_spec.setdefault("task", {})["budget"] = int(cfg["budget"])
    if "required" in cfg and isinstance(cfg["required"], list) and cfg["required"]:
        candidate_spec.setdefault("task", {})["required"] = cfg["required"]
    if "time_limit_s" in cfg and cfg["time_limit_s"] is not None:
        candidate_spec.setdefault("task", {})["time_limit_s"] = int(cfg["time_limit_s"])
    if "difficulty" in cfg and cfg["difficulty"]:
        candidate_spec.setdefault("task", {})["difficulty"] = cfg["difficulty"]
    if "rules" in cfg and isinstance(cfg["rules"], list):
        candidate_spec.setdefault("task", {})["rules"] = cfg["rules"]
    if "what_ifs" in cfg and isinstance(cfg["what_ifs"], list):
        candidate_spec.setdefault("task", {})["what_ifs"] = cfg["what_ifs"]
    if "support" in cfg and isinstance(cfg["support"], dict):
        candidate_spec["support"] = cfg["support"]

    report = validate_scene_spec(candidate_spec)
    if not report["valid"]:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Configuration violates R1–R7 scene constraints.",
                "validation_report": report,
            },
        )

    experience.configuration = payload.configuration
    experience.spec = candidate_spec
    experience.validation_report = report
    experience.status = "configured"
    experience.updated_at = datetime.utcnow()

    # Save the new configuration and its version in one transaction.
    ver = create_version_snapshot(db, experience, state="configured")
    _log_audit(db, current_tutor, "configure", experience.id, ver.version_number)

    db.commit()
    db.refresh(experience)
    return experience


@router.post(
    "/{experience_id}/approve-version",
    response_model=ExperienceResponse,
)
def approve_for_launch(
    experience_id: UUID,
    db: Session = Depends(get_db),
    current_tutor: Tutor = Depends(require_roles("tutor", "admin")),
):
    """Gate 2: Approve a configured version so it can be launched on laptop or room (FR-11, LC-5)."""
    experience = get_experience_or_404(db, experience_id, current_tutor)

    if experience.status not in {"ready_to_configure", "configured", "approved", "live"}:
        raise HTTPException(
            status_code=409,
            detail="Experience must be configured and validated before approval for launch.",
        )

    spec_to_check = experience.spec or get_reference_scene_spec()
    report = validate_scene_spec(spec_to_check)
    if not report["valid"]:
        raise HTTPException(
            status_code=409,
            detail="Cannot approve a version that fails R1–R7 validation.",
        )

    experience.spec = spec_to_check
    experience.validation_report = report
    experience.status = "approved"
    experience.updated_at = datetime.utcnow()

    latest_ver = (
        db.query(ExperienceVersion)
        .filter(ExperienceVersion.experience_id == experience.id)
        .order_by(ExperienceVersion.version_number.desc())
        .first()
    )
    if latest_ver is None:
        latest_ver = create_version_snapshot(
            db,
            experience,
            state="approved",
            approved_by=current_tutor.id,
        )
    else:
        latest_ver.state = "approved"
        latest_ver.spec = deepcopy(experience.spec)
        latest_ver.validation_report = deepcopy(report)
        latest_ver.configuration_snapshot = deepcopy(experience.configuration or {})
        latest_ver.approved_by = current_tutor.id
        latest_ver.approved_at = datetime.utcnow()

    _log_audit(db, current_tutor, "approve_version", experience.id, latest_ver.version_number)
    db.commit()
    db.refresh(experience)
    return experience
    return experience
