"""SRS Section 4–10 endpoints: Scenarios, Jobs, Runtime & Console, Session Notebook,
Notifications, Audit Log, Validator, and School Admin Data Export/Delete.
"""

from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime
from typing import Any
from uuid import UUID
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Response, WebSocket, WebSocketDisconnect, status
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db import SessionLocal, get_db
from app.dependencies import get_current_tutor, require_roles
from app.models.audit_event import AuditEvent
from app.models.classroom import Classroom
from app.models.experience import Experience
from app.models.experience_version import ExperienceVersion
from app.models.job import JobRecord
from app.models.module import Module
from app.models.notebook_event import NotebookEvent
from app.models.notification import Notification
from app.models.run import ScenarioRun
from app.models.student import Student
from app.models.tutor import Tutor
from app.routers.experiences import (
    _log_audit,
    _notify_tutor,
    create_version_snapshot,
    get_experience_or_404,
)
from app.schemas.class_workspace import ModuleResponse
from app.services.ai_provider import generate_with_repair_loop, get_ai_provider, with_preview_images
from app.services.previews import read_stored
from app.services.validator import (
    compile_pathway_config,
    get_reference_scene_spec,
    simulate_learner_completion,
    validate_scene_spec,
)

router = APIRouter()

# Active WebSocket connections per run_id (RT-08)
_RUN_SOCKETS: dict[str, list[WebSocket]] = {}


# ---------------------------------------------------------------------------
# Request / Response Schemas
# ---------------------------------------------------------------------------


class ModuleTopLevelCreate(BaseModel):
    class_id: UUID
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None


class ScenarioCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    prompt: str = Field(..., min_length=1)
    category: str = Field(default="Life Skills", max_length=100)
    class_id: UUID | None = None
    module_id: UUID | None = None
    answers: dict[str, Any] = Field(default_factory=dict)
    voice_transcript: str | None = None
    attachments: list[dict[str, Any]] = Field(default_factory=list)


class ScenarioEditRequest(BaseModel):
    instruction: str = Field(..., min_length=1)


class ScenarioConfigRequest(BaseModel):
    configuration: dict[str, Any] = Field(default_factory=dict)
    spec: dict[str, Any] | None = None


class RunCreateRequest(BaseModel):
    scenario_id: UUID | None = None
    experience_id: UUID | None = None
    version_number: int | None = None
    learner_id: UUID | None = None
    pathway: str = Field(default="B", pattern="^[ABC]$")
    mode: str = Field(default="laptop", pattern="^(laptop|room)$")


class RunCommandRequest(BaseModel):
    command: str = Field(
        ...,
        description="Command: pause, resume, simplify, set_pathway, prompt, what_if, move, select, step_complete, end",
    )
    payload: dict[str, Any] = Field(default_factory=dict)


class ValidateSpecRequest(BaseModel):
    spec: dict[str, Any]
    comfort_caps: dict[str, dict[str, int]] | None = None
    schema_only: bool = False


# ---------------------------------------------------------------------------
# Top-level /modules endpoints (FR-02, Section 10)
# ---------------------------------------------------------------------------


@router.get("/modules", response_model=list[ModuleResponse], tags=["Modules"])
def list_all_modules(
    class_id: UUID | None = None,
    db: Session = Depends(get_db),
    tutor: Tutor = Depends(get_current_tutor),
):
    query = db.query(Module).filter(
        Module.organisation_id == tutor.organisation_id,
        Module.deleted_at.is_(None),
    )
    if class_id is not None:
        query = query.filter(Module.class_id == class_id)
    return query.order_by(Module.created_at.asc()).all()


@router.post(
    "/modules",
    response_model=ModuleResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Modules"],
)
def create_top_level_module(
    payload: ModuleTopLevelCreate,
    db: Session = Depends(get_db),
    tutor: Tutor = Depends(require_roles("tutor", "admin")),
):
    classroom = (
        db.query(Classroom)
        .filter(
            Classroom.id == payload.class_id,
            Classroom.organisation_id == tutor.organisation_id,
            Classroom.deleted_at.is_(None),
        )
        .first()
    )
    if classroom is None:
        raise HTTPException(status_code=404, detail="Class not found in your school")

    module = Module(
        organisation_id=tutor.organisation_id,
        class_id=payload.class_id,
        name=payload.name.strip(),
        description=payload.description,
    )
    db.add(module)
    db.commit()
    db.refresh(module)
    return module


# ---------------------------------------------------------------------------
# Validator & Reachability Oracle Endpoints (Section 5, FR-14, AT-01, AT-08)
# ---------------------------------------------------------------------------


@router.post("/validate", tags=["Validation"])
def validate_spec_endpoint(
    payload: ValidateSpecRequest,
    tutor: Tutor = Depends(get_current_tutor),
):
    report = validate_scene_spec(
        payload.spec,
        comfort_caps=payload.comfort_caps,
        schema_only=payload.schema_only,
    )
    oracle = simulate_learner_completion(payload.spec) if report["valid"] else {"completed": False}
    return {
        "validation_report": report,
        "oracle": oracle,
    }


@router.post("/safety-check", tags=["Validation"])
def run_safety_check_endpoint():
    """Demonstrate the Plan-Validate-Build repair loop: validates the faulty kirana seed

    (demonstrating real R3, R4, R5, R6 errors on Attempt 1), then repairs it so all R1-R7 pass on Attempt 2.
    """
    demo_dir = Path(__file__).resolve().parent.parent / "demo_seeds"
    faulty_path = demo_dir / "kirana_shop.faulty.json"
    valid_path = demo_dir / "kirana_shop.valid.json"

    faulty_spec = json.loads(faulty_path.read_text())
    valid_spec = json.loads(valid_path.read_text())

    attempt1_report = validate_scene_spec(faulty_spec)
    attempt2_report = validate_scene_spec(valid_spec)

    attempts = [
        {
            "attempt": 1,
            "valid": attempt1_report["valid"],
            "rules_summary": attempt1_report.get("rules_summary", {}),
            "errors": attempt1_report.get("errors", []),
            "warnings": attempt1_report.get("warnings", []),
            "spec": faulty_spec,
        },
        {
            "attempt": 2,
            "valid": attempt2_report["valid"],
            "rules_summary": attempt2_report.get("rules_summary", {}),
            "errors": attempt2_report.get("errors", []),
            "warnings": attempt2_report.get("warnings", []),
            "spec": valid_spec,
        },
    ]

    return {
        "status": "repaired",
        "attempts": attempts,
        "initial_report": attempt1_report,
        "final_report": attempt2_report,
        "repaired_spec": valid_spec,
    }


# ---------------------------------------------------------------------------
# /scenarios & /jobs endpoints (SRS Section 10)
# ---------------------------------------------------------------------------


@router.post("/scenarios", status_code=status.HTTP_201_CREATED, tags=["Scenarios"])
def create_scenario(
    payload: ScenarioCreateRequest,
    db: Session = Depends(get_db),
    tutor: Tutor = Depends(require_roles("tutor", "admin")),
):
    provider = get_ai_provider()
    concepts = provider.generate_concepts(payload.prompt, payload.answers)
    scenario = Experience(
        organisation_id=tutor.organisation_id,
        created_by_tutor_id=tutor.id,
        class_id=payload.class_id,
        module_id=payload.module_id,
        title=payload.title.strip(),
        category=payload.category,
        prompt=payload.prompt,
        voice_transcript=payload.voice_transcript,
        attachments=payload.attachments or [],
        answers=payload.answers or {},
        concept_options=concepts,
        concept_preview=concepts[0] if concepts else None,
        configuration={},
        current_version=1,
        status="draft",
        generation_mode=provider.name,
    )
    db.add(scenario)
    db.flush()
    _log_audit(db, tutor, "create_scenario", scenario.id, 1, {"title": scenario.title})
    db.commit()
    db.refresh(scenario)
    return scenario


@router.get("/scenarios", tags=["Scenarios"])
def list_scenarios(
    db: Session = Depends(get_db),
    tutor: Tutor = Depends(get_current_tutor),
):
    return (
        db.query(Experience)
        .filter(
            Experience.organisation_id == tutor.organisation_id,
            Experience.deleted_at.is_(None),
        )
        .order_by(Experience.created_at.desc())
        .all()
    )


@router.get("/scenarios/{scenario_id}", tags=["Scenarios"])
def get_scenario(
    scenario_id: UUID,
    db: Session = Depends(get_db),
    tutor: Tutor = Depends(get_current_tutor),
):
    return get_experience_or_404(db, scenario_id, tutor)


@router.post("/scenarios/{scenario_id}/concepts", tags=["Scenarios"])
def get_scenario_concepts(
    scenario_id: UUID,
    db: Session = Depends(get_db),
    tutor: Tutor = Depends(require_roles("tutor", "admin")),
):
    scenario = get_experience_or_404(db, scenario_id, tutor)
    provider = get_ai_provider()
    concepts = provider.generate_concepts(scenario.prompt, scenario.answers)
    concepts = with_preview_images(provider, concepts, scenario.prompt)
    scenario.concept_options = concepts
    if not scenario.concept_preview and concepts:
        scenario.concept_preview = concepts[0]
    scenario.status = "preview_approved"
    scenario.concept_approved_at = datetime.utcnow()
    scenario.updated_at = datetime.utcnow()
    db.commit()
    return {"scenario_id": str(scenario.id), "concepts": concepts, "status": scenario.status}


@router.get("/previews/{key}.png", tags=["Scenarios"], include_in_schema=False)
def get_preview_image(key: str) -> Response:
    """Nano Banana concept preview (gcs mode). Unauthenticated so <img> tags work: keys are 128-bit hashes and
    the images are generic shop illustrations built from concept text, never learner data."""
    data = read_stored(key)
    if data is None:
        raise HTTPException(status_code=404, detail="Preview not found")
    return Response(content=data, media_type="image/png", headers={"Cache-Control": "public, max-age=86400"})


@router.post("/scenarios/{scenario_id}/generate", tags=["Scenarios"])
def generate_scenario(
    scenario_id: UUID,
    db: Session = Depends(get_db),
    tutor: Tutor = Depends(require_roles("tutor", "admin")),
):
    scenario = get_experience_or_404(db, scenario_id, tutor)
    if scenario.status not in {"approved", "preview_approved", "concept_review"}:
        raise HTTPException(
            status_code=409,
            detail="Concept preview must be approved before starting generation.",
        )

    idem_key = f"{scenario.id}:v{scenario.current_version}:gen"
    existing_job = db.query(JobRecord).filter(JobRecord.idempotency_key == idem_key).first()
    if existing_job and existing_job.status == "completed" and scenario.status == "ready_to_configure":
        return {"job_id": str(existing_job.id), "status": existing_job.status, "scenario": scenario}

    result = generate_with_repair_loop(
        prompt=scenario.prompt,
        answers=scenario.answers,
        concept=scenario.concept_preview,
        max_retries=3,
    )

    if existing_job is None:
        job = JobRecord(
            organisation_id=tutor.organisation_id,
            experience_id=scenario.id,
            version_number=scenario.current_version,
            idempotency_key=idem_key,
            kind="scene_generation",
            status="completed" if result["success"] else "failed",
            attempt=result["attempts"],
            max_attempts=3,
            error_plain=result["error_plain"],
            validation_report=result["validation_report"],
        )
        db.add(job)
        db.flush()
    else:
        job = existing_job
        job.status = "completed" if result["success"] else "failed"
        job.attempt = result["attempts"]
        job.error_plain = result["error_plain"]
        job.validation_report = result["validation_report"]

    if not result["success"]:
        scenario.status = "preview_approved"
        scenario.error_plain = result["error_plain"]
        scenario.validation_report = result["validation_report"]
        _notify_tutor(
            db,
            tutor,
            "generation_failed",
            f"Generation failed: {scenario.title}",
            result["error_plain"] or "Generation failed validation.",
            scenario.id,
        )
        db.commit()
        return {
            "job_id": str(job.id),
            "status": "failed",
            "attempt": result["attempts"],
            "error_plain": result["error_plain"],
            "validation_report": result["validation_report"],
        }

    scenario.spec = result["spec"]
    scenario.validation_report = result["validation_report"]
    scenario.error_plain = None
    scenario.status = "ready_to_configure"
    scenario.updated_at = datetime.utcnow()
    ver = create_version_snapshot(db, scenario, state="ready_to_configure")
    _notify_tutor(
        db,
        tutor,
        "ready_to_configure",
        f"Ready to configure: {scenario.title}",
        f"Version {ver.version_number} passed R1–R7 validation.",
        scenario.id,
    )
    _log_audit(db, tutor, "generate", scenario.id, ver.version_number, {"job_id": str(job.id)})
    db.commit()
    db.refresh(scenario)
    return {
        "job_id": str(job.id),
        "status": job.status,
        "version_number": ver.version_number,
        "validation_report": result["validation_report"],
        "scenario": scenario,
    }


@router.get("/jobs", tags=["Jobs"])
def list_jobs(
    db: Session = Depends(get_db),
    tutor: Tutor = Depends(get_current_tutor),
):
    return (
        db.query(JobRecord)
        .filter(JobRecord.organisation_id == tutor.organisation_id)
        .order_by(JobRecord.created_at.desc())
        .all()
    )


@router.get("/jobs/{job_id}", tags=["Jobs"])
def get_job_status(
    job_id: UUID,
    db: Session = Depends(get_db),
    tutor: Tutor = Depends(get_current_tutor),
):
    job = (
        db.query(JobRecord)
        .filter(
            JobRecord.id == job_id,
            JobRecord.organisation_id == tutor.organisation_id,
        )
        .first()
    )
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/scenarios/{scenario_id}/versions/{version_n}", tags=["Scenarios"])
def get_scenario_version(
    scenario_id: UUID,
    version_n: int,
    db: Session = Depends(get_db),
    tutor: Tutor = Depends(get_current_tutor),
):
    scenario = get_experience_or_404(db, scenario_id, tutor)
    ver = (
        db.query(ExperienceVersion)
        .filter(
            ExperienceVersion.experience_id == scenario.id,
            ExperienceVersion.version_number == version_n,
        )
        .first()
    )
    if ver is None:
        raise HTTPException(status_code=404, detail="Scenario version not found")
    return ver


@router.post("/scenarios/{scenario_id}/versions/{version_n}/edit", tags=["Scenarios"])
def edit_scenario_version(
    scenario_id: UUID,
    version_n: int,
    payload: ScenarioEditRequest,
    db: Session = Depends(get_db),
    tutor: Tutor = Depends(require_roles("tutor", "admin")),
):
    scenario = get_experience_or_404(db, scenario_id, tutor)
    if scenario.status not in {"ready_to_configure", "configured", "approved", "live"}:
        raise HTTPException(
            status_code=409,
            detail="Cannot edit scenario before it reaches Ready to configure.",
        )

    ver = (
        db.query(ExperienceVersion)
        .filter(
            ExperienceVersion.experience_id == scenario.id,
            ExperienceVersion.version_number == version_n,
        )
        .first()
    )
    base_spec = (ver.spec if ver and ver.spec else scenario.spec) or get_reference_scene_spec()

    provider = get_ai_provider()
    patch_res = provider.apply_plain_language_edit(base_spec, payload.instruction)
    report = validate_scene_spec(patch_res["patched_spec"])

    if not report["valid"]:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Plain-language edit rejected by R1–R7 validator.",
                "validation_report": report,
                "patch_ratio": patch_res["patch_ratio"],
            },
        )

    scenario.spec = patch_res["patched_spec"]
    scenario.validation_report = report
    scenario.status = "ready_to_configure"
    scenario.updated_at = datetime.utcnow()
    new_ver = create_version_snapshot(db, scenario, state="ready_to_configure")
    _log_audit(
        db,
        tutor,
        "edit",
        scenario.id,
        new_ver.version_number,
        {"instruction": payload.instruction, "patch_ratio": patch_res["patch_ratio"]},
    )
    db.commit()
    return {
        "scenario_id": str(scenario.id),
        "version_number": new_ver.version_number,
        "state": new_ver.state,
        "spec": new_ver.spec,
        "validation_report": report,
        "patch_ops": patch_res["patch_ops"],
        "patch_bytes": patch_res["patch_bytes"],
        "spec_bytes": patch_res["spec_bytes"],
        "patch_ratio": patch_res["patch_ratio"],
    }


@router.put("/scenarios/{scenario_id}/versions/{version_n}/config", tags=["Scenarios"])
def configure_scenario_version(
    scenario_id: UUID,
    version_n: int,
    payload: ScenarioConfigRequest,
    db: Session = Depends(get_db),
    tutor: Tutor = Depends(require_roles("tutor", "admin")),
):
    scenario = get_experience_or_404(db, scenario_id, tutor)
    if scenario.status not in {"ready_to_configure", "configured", "approved", "live"}:
        raise HTTPException(
            status_code=409,
            detail="Configuration is locked until generation completes (Ready to configure).",
        )

    candidate_spec = deepcopy(payload.spec or scenario.spec or get_reference_scene_spec())
    cfg = payload.configuration or {}
    if "budget" in cfg and cfg["budget"] is not None:
        candidate_spec.setdefault("task", {})["budget"] = int(cfg["budget"])
    if "required" in cfg and isinstance(cfg["required"], list) and cfg["required"]:
        candidate_spec.setdefault("task", {})["required"] = cfg["required"]
    if "support" in cfg and isinstance(cfg["support"], dict):
        candidate_spec["support"] = cfg["support"]

    report = validate_scene_spec(candidate_spec)
    if not report["valid"]:
        raise HTTPException(
            status_code=422,
            detail={"message": "Configuration failed R1–R7 validation.", "validation_report": report},
        )

    scenario.configuration = cfg
    scenario.spec = candidate_spec
    scenario.validation_report = report
    scenario.status = "configured"
    scenario.updated_at = datetime.utcnow()

    ver = (
        db.query(ExperienceVersion)
        .filter(
            ExperienceVersion.experience_id == scenario.id,
            ExperienceVersion.version_number == version_n,
        )
        .first()
    )
    if ver is None or ver.state == "approved":
        ver = create_version_snapshot(db, scenario, state="configured")
    else:
        ver.configuration_snapshot = deepcopy(cfg)
        ver.spec = deepcopy(candidate_spec)
        ver.validation_report = deepcopy(report)
        ver.state = "configured"

    _log_audit(db, tutor, "configure", scenario.id, ver.version_number)
    db.commit()
    db.refresh(ver)
    return ver


@router.post("/scenarios/{scenario_id}/versions/{version_n}/approve", tags=["Scenarios"])
def approve_scenario_version(
    scenario_id: UUID,
    version_n: int,
    db: Session = Depends(get_db),
    tutor: Tutor = Depends(require_roles("tutor", "admin")),
):
    scenario = get_experience_or_404(db, scenario_id, tutor)
    ver = (
        db.query(ExperienceVersion)
        .filter(
            ExperienceVersion.experience_id == scenario.id,
            ExperienceVersion.version_number == version_n,
        )
        .first()
    )
    if ver is None:
        raise HTTPException(status_code=404, detail="Version not found")

    if ver.state not in {"ready_to_configure", "configured", "approved"}:
        raise HTTPException(
            status_code=409,
            detail="Only validated and configured versions can be approved.",
        )

    spec_to_validate = ver.spec or scenario.spec or get_reference_scene_spec()
    report = validate_scene_spec(spec_to_validate)
    if not report["valid"]:
        raise HTTPException(status_code=409, detail="Version spec is not valid.")

    ver.state = "approved"
    ver.spec = deepcopy(spec_to_validate)
    ver.validation_report = deepcopy(report)
    ver.approved_by = tutor.id
    ver.approved_at = datetime.utcnow()

    scenario.status = "approved"
    scenario.updated_at = datetime.utcnow()
    _log_audit(db, tutor, "approve", scenario.id, ver.version_number)
    db.commit()
    db.refresh(ver)
    return ver


# ---------------------------------------------------------------------------
# Runtime & Tutor Console (/runs and WebSocket /runs/{id}/console)
# (SRS Section 7: FR-11, FR-12, FR-16, RT-01..RT-09)
# ---------------------------------------------------------------------------


@router.post("/runs", status_code=status.HTTP_201_CREATED, tags=["Runtime"])
def launch_run(
    payload: RunCreateRequest,
    db: Session = Depends(get_db),
    tutor: Tutor = Depends(require_roles("tutor", "admin", "learner")),
):
    target_id = payload.scenario_id or payload.experience_id
    if target_id is None:
        raise HTTPException(status_code=422, detail="Provide scenario_id or experience_id")

    scenario = get_experience_or_404(db, target_id, tutor)

    # Locate the requested version or latest version
    ver_query = db.query(ExperienceVersion).filter(ExperienceVersion.experience_id == scenario.id)
    if payload.version_number is not None:
        ver = ver_query.filter(ExperienceVersion.version_number == payload.version_number).first()
    else:
        # Prefer the latest approved version (LC-4: old version stays runnable while n+1 is edited)
        ver = (
            ver_query.filter(ExperienceVersion.state == "approved")
            .order_by(ExperienceVersion.version_number.desc())
            .first()
        )
        if ver is None:
            ver = ver_query.order_by(ExperienceVersion.version_number.desc()).first()

    # FR-11 & AT-04: Unapproved or stale version returns 409 on launch
    if ver is None or ver.state != "approved":
        raise HTTPException(
            status_code=409,
            detail="Only approved versions can be launched. Approve the version first.",
        )

    spec = ver.spec or scenario.spec or get_reference_scene_spec()
    report = validate_scene_spec(spec)
    if not report["valid"]:
        raise HTTPException(status_code=409, detail="Scene specification did not pass validation.")

    compiled = compile_pathway_config(spec, payload.pathway)
    entrance_cells = spec["room"]["entrance"]["cells"]
    start_x, start_y = int(entrance_cells[0][0]), int(entrance_cells[0][1])

    run = ScenarioRun(
        organisation_id=tutor.organisation_id,
        experience_id=scenario.id,
        version_id=ver.id,
        version_number=ver.version_number,
        learner_id=payload.learner_id,
        created_by_tutor_id=tutor.id,
        pathway=payload.pathway,
        mode=payload.mode,
        status="running",
        learner_position={"x": start_x, "y": start_y, "dir": "N"},
        basket=[],
        steps_completed=["entered_room"],
        prompts_given=0,
        tutor_decisions=0,
        errors_count=0,
        active_what_if=None,
        compiled_config=compiled,
    )
    db.add(run)
    db.flush()

    nb_event = NotebookEvent(
        organisation_id=tutor.organisation_id,
        run_id=run.id,
        learner_id=payload.learner_id,
        kind="session_start",
        step_id="entered_room",
        pathway=payload.pathway,
        t_ms=0,
        event_data={"mode": payload.mode, "version_number": ver.version_number},
    )
    db.add(nb_event)
    _log_audit(
        db,
        tutor,
        "launch_run",
        run.id,
        ver.version_number,
        {"scenario_id": str(scenario.id), "mode": payload.mode, "pathway": payload.pathway},
    )
    db.commit()
    db.refresh(run)
    return _serialize_run(run, scenario.title)


@router.get("/runs", tags=["Runtime"])
def list_runs(
    db: Session = Depends(get_db),
    tutor: Tutor = Depends(get_current_tutor),
):
    runs = (
        db.query(ScenarioRun)
        .filter(ScenarioRun.organisation_id == tutor.organisation_id)
        .order_by(ScenarioRun.started_at.desc())
        .limit(50)
        .all()
    )
    exp_ids = {r.experience_id for r in runs}
    titles = {}
    if exp_ids:
        for exp in db.query(Experience).filter(Experience.id.in_(exp_ids)).all():
            titles[exp.id] = exp.title
    return [_serialize_run(r, titles.get(r.experience_id, "Scenario")) for r in runs]


@router.get("/runs/{run_id}", tags=["Runtime"])
def get_run(
    run_id: UUID,
    db: Session = Depends(get_db),
    tutor: Tutor = Depends(get_current_tutor),
):
    run = (
        db.query(ScenarioRun)
        .filter(
            ScenarioRun.id == run_id,
            ScenarioRun.organisation_id == tutor.organisation_id,
        )
        .first()
    )
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    exp = db.query(Experience).filter(Experience.id == run.experience_id).first()
    return _serialize_run(run, exp.title if exp else "Scenario")


@router.post("/runs/{run_id}/command", tags=["Runtime"])
async def execute_run_command(
    run_id: UUID,
    payload: RunCommandRequest,
    db: Session = Depends(get_db),
    tutor: Tutor = Depends(get_current_tutor),
):
    """Execute a Tutor Console or Learner Runtime command in < 500 ms (FR-16, RT-01, RT-07)."""
    run = (
        db.query(ScenarioRun)
        .filter(
            ScenarioRun.id == run_id,
            ScenarioRun.organisation_id == tutor.organisation_id,
        )
        .first()
    )
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")

    result = _apply_command_to_run(db, run, payload.command, payload.payload)
    db.commit()
    db.refresh(run)

    exp = db.query(Experience).filter(Experience.id == run.experience_id).first()
    serialized = _serialize_run(run, exp.title if exp else "Scenario")
    serialized["last_action"] = result

    # Broadcast over WebSocket to connected console/runtime views (RT-08)
    sockets = _RUN_SOCKETS.get(str(run.id), [])
    stale: list[WebSocket] = []
    for ws in sockets:
        try:
            await ws.send_json(serialized)
        except Exception:
            stale.append(ws)
    for ws in stale:
        if ws in sockets:
            sockets.remove(ws)

    return serialized


@router.websocket("/runs/{run_id}/console")
async def run_console_websocket(websocket: WebSocket, run_id: str):
    """Real-time WebSocket channel between Tutor Console and Learner Runtime (RT-08).
    Runtime continues uninterrupted if the console disconnects.
    """
    await websocket.accept()
    key = str(run_id)
    _RUN_SOCKETS.setdefault(key, []).append(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            cmd = data.get("command")
            cmd_payload = data.get("payload") or {}
            if cmd:
                with SessionLocal() as db:
                    try:
                        run_uuid = UUID(str(run_id))
                    except ValueError:
                        continue
                    run = db.query(ScenarioRun).filter(ScenarioRun.id == run_uuid).first()
                    if run:
                        _apply_command_to_run(db, run, cmd, cmd_payload)
                        db.commit()
                        db.refresh(run)
                        exp = db.query(Experience).filter(Experience.id == run.experience_id).first()
                        serialized = _serialize_run(run, exp.title if exp else "Scenario")
                        for peer in list(_RUN_SOCKETS.get(key, [])):
                            try:
                                await peer.send_json(serialized)
                            except Exception:
                                pass
    except WebSocketDisconnect:
        pass
    finally:
        if websocket in _RUN_SOCKETS.get(key, []):
            _RUN_SOCKETS[key].remove(websocket)


def _apply_command_to_run(
    db: Session,
    run: ScenarioRun,
    command: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    now = datetime.utcnow()
    elapsed_ms = int((now - run.started_at).total_seconds() * 1000)
    run.elapsed_ms = max(run.elapsed_ms, elapsed_ms)

    spec = run.compiled_config or get_reference_scene_spec()
    room = spec.get("room", {"w": 12, "h": 8})
    w, h = int(room.get("w", 12)), int(room.get("h", 8))
    layout = spec.get("layout", [])

    occupied: dict[tuple[int, int], dict[str, Any]] = {}
    for obj in layout:
        ox, oy = int(obj["cell"][0]), int(obj["cell"][1])
        ow, oh = int(obj["size"][0]), int(obj["size"][1])
        for cx in range(ox, ox + ow):
            for cy in range(oy, oy + oh):
                occupied[(cx, cy)] = obj

    pos = deepcopy(run.learner_position or {"x": 5, "y": 7, "dir": "N"})
    basket = deepcopy(run.basket or [])
    steps = deepcopy(run.steps_completed or [])
    action_note = command

    if command == "pause":
        run.status = "paused"
        run.tutor_decisions += 1
        action_note = "Session paused"

    elif command == "resume":
        run.status = "running"
        run.tutor_decisions += 1
        action_note = "Session resumed"

    elif command in ("simplify", "set_pathway"):
        # simplify steps toward more support (C -> B -> A); set_pathway jumps to A, B or C (FR-16, RT-06).
        # Either way the config is recompiled from the run's approved, validated version spec.
        if command == "simplify":
            next_pathway = "B" if run.pathway == "C" else "A"
        else:
            next_pathway = str(payload.get("pathway", "")).upper()
            if next_pathway not in ("A", "B", "C"):
                raise HTTPException(status_code=422, detail="pathway must be A, B or C")
        run.pathway = next_pathway
        full_spec = get_reference_scene_spec()
        ver = db.query(ExperienceVersion).filter(ExperienceVersion.id == run.version_id).first()
        if ver and ver.spec:
            full_spec = ver.spec
        run.compiled_config = compile_pathway_config(full_spec, next_pathway)
        run.tutor_decisions += 1
        action_note = f"Switched to Support Pathway {next_pathway}"

    elif command == "prompt":
        run.prompts_given += 1
        run.tutor_decisions += 1
        hint_text = payload.get("message") or "Check the next item on your shopping list."
        action_note = f"Prompt given: {hint_text}"

    elif command == "what_if":
        event_text = payload.get("event") or "Preferred item is out of stock"
        run.active_what_if = event_text
        run.tutor_decisions += 1
        action_note = f"Triggered what-if: {event_text}"

    elif command == "move":
        if run.status == "paused":
            return {"status": "paused", "note": "Session is paused"}
        direction = payload.get("dir", pos.get("dir", "N")).upper()
        dx, dy = {"N": (0, -1), "S": (0, 1), "E": (1, 0), "W": (-1, 0)}.get(direction, (0, 0))
        nx, ny = int(pos["x"]) + dx, int(pos["y"]) + dy
        pos["dir"] = direction
        if 0 <= nx < w and 0 <= ny < h and (nx, ny) not in occupied:
            pos["x"] = nx
            pos["y"] = ny
            action_note = f"Moved to [{nx}, {ny}] facing {direction}"
        else:
            run.errors_count += 1
            action_note = f"Blocked at [{nx}, {ny}]"
        run.learner_position = pos

    elif command == "select":
        # Space bar interaction with adjacent shelf or counter (RT-01)
        lx, ly = int(pos["x"]), int(pos["y"])
        adj_objs: list[dict[str, Any]] = []
        for dx, dy in ((0, -1), (0, 1), (1, 0), (-1, 0), (0, 0)):
            cell_obj = occupied.get((lx + dx, ly + dy))
            if cell_obj and cell_obj not in adj_objs:
                adj_objs.append(cell_obj)

        requested_sku = payload.get("sku")
        picked = None
        checked_out = False
        required_skus = set((spec.get("task") or {}).get("required") or [])

        for obj in adj_objs:
            if obj.get("asset") == "counter" or obj.get("id") == "counter":
                checked_out = True
                break
            # Without an explicit SKU, a hand press picks a still-needed required item before anything else.
            shelf_items = sorted(obj.get("items") or [], key=lambda it: it.get("sku") not in required_skus)
            for item in shelf_items:
                if requested_sku and item.get("sku") == requested_sku:
                    picked = item
                    break
                if not requested_sku and item.get("sku") not in [b.get("sku") for b in basket]:
                    picked = item
                    break
            if picked:
                break

        # Also allow direct SKU selection from UI controls
        if not picked and requested_sku:
            for obj in layout:
                for item in obj.get("items") or []:
                    if item.get("sku") == requested_sku:
                        picked = item
                        break

        if checked_out or payload.get("checkout"):
            step_name = "completed_checkout"
            if step_name not in steps:
                steps.append(step_name)
            run.steps_completed = steps
            run.status = "completed"
            run.ended_at = now
            action_note = "Checked out at counter"
        elif picked:
            basket.append({"sku": picked["sku"], "price": picked["price"]})
            step_name = f"picked_{picked['sku']}"
            if step_name not in steps:
                steps.append(step_name)
            run.basket = basket
            run.steps_completed = steps
            action_note = f"Picked up {picked['sku']} ({picked['price']})"
        else:
            run.errors_count += 1
            action_note = "No interactive item within reach"

    elif command == "end":
        run.status = "completed"
        run.ended_at = now
        action_note = "Session ended"

    nb = NotebookEvent(
        organisation_id=run.organisation_id,
        run_id=run.id,
        learner_id=run.learner_id,
        kind=command,
        step_id=steps[-1] if steps else None,
        pathway=run.pathway,
        t_ms=run.elapsed_ms,
        event_data={"note": action_note, "position": run.learner_position},
    )
    db.add(nb)
    run.updated_at = now
    return {"command": command, "note": action_note}


def _serialize_run(run: ScenarioRun, scenario_title: str = "Scenario") -> dict[str, Any]:
    basket = run.basket or []
    basket_total = sum(float(item.get("price", 0)) for item in basket)
    cfg = run.compiled_config or {}
    budget = cfg.get("task", {}).get("budget", 500)
    required = cfg.get("task", {}).get("required", [])
    return {
        "id": str(run.id),
        "organisation_id": str(run.organisation_id),
        "experience_id": str(run.experience_id),
        "scenario_title": scenario_title,
        "version_id": str(run.version_id),
        "version_number": run.version_number,
        "learner_id": str(run.learner_id) if run.learner_id else None,
        "pathway": run.pathway,
        "mode": run.mode,
        "status": run.status,
        "learner_position": run.learner_position,
        "basket": basket,
        "basket_total": basket_total,
        "budget": budget,
        "required_items": required,
        "steps_completed": run.steps_completed or [],
        "prompts_given": run.prompts_given,
        "tutor_decisions": run.tutor_decisions,
        "errors_count": run.errors_count,
        "active_what_if": run.active_what_if,
        "compiled_config": cfg,
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "ended_at": run.ended_at.isoformat() if run.ended_at else None,
        "elapsed_ms": run.elapsed_ms,
    }


# ---------------------------------------------------------------------------
# Non-Diagnostic Session Notebook (SRS Section 8: FR-17, NB-01..NB-05, AT-06)
# Hard rule NB-02: NO score, grade, rating, level, diagnosis, risk, percentile,
# or label field name anywhere in the schema, API response, or exports.
# ---------------------------------------------------------------------------


@router.get("/learners/{learner_id}/notebook", tags=["Notebook"])
def get_learner_notebook(
    learner_id: UUID,
    db: Session = Depends(get_db),
    tutor: Tutor = Depends(require_roles("tutor", "admin", "support")),
):
    student = (
        db.query(Student)
        .join(Classroom, Classroom.id == Student.class_id)
        .filter(
            Student.id == learner_id,
            Classroom.organisation_id == tutor.organisation_id,
            Classroom.deleted_at.is_(None),
        )
        .first()
    )
    if student is None:
        raise HTTPException(status_code=404, detail="Learner not found in your school")

    runs = (
        db.query(ScenarioRun)
        .filter(
            ScenarioRun.organisation_id == tutor.organisation_id,
            ScenarioRun.learner_id == learner_id,
        )
        .order_by(ScenarioRun.started_at.asc())
        .all()
    )

    return _build_notebook_response(db, student, runs)


@router.get("/notebook", tags=["Notebook"])
def list_school_notebook_sessions(
    learner_id: UUID | None = None,
    db: Session = Depends(get_db),
    tutor: Tutor = Depends(require_roles("tutor", "admin", "support")),
):
    query = db.query(ScenarioRun).filter(ScenarioRun.organisation_id == tutor.organisation_id)
    if learner_id is not None:
        query = query.filter(ScenarioRun.learner_id == learner_id)
    runs = query.order_by(ScenarioRun.started_at.desc()).limit(100).all()

    exp_ids = {r.experience_id for r in runs}
    titles = {}
    if exp_ids:
        for exp in db.query(Experience).filter(Experience.id.in_(exp_ids)).all():
            titles[exp.id] = exp.title

    learner_ids = {r.learner_id for r in runs if r.learner_id}
    learners_map = {}
    if learner_ids:
        for st in db.query(Student).filter(Student.id.in_(learner_ids)).all():
            learners_map[st.id] = st

    sessions = []
    for r in runs:
        st = learners_map.get(r.learner_id) if r.learner_id else None
        sessions.append(
            {
                "session_id": str(r.id),
                "scenario_id": str(r.experience_id),
                "scenario_title": titles.get(r.experience_id, "Scenario"),
                "scenario_version": r.version_number,
                "learner_id": str(r.learner_id) if r.learner_id else None,
                "learner_pseudonym": st.pseudonym_id if st else "LRN-ANON",
                "learner_display_name": (
                    st.name if (st and st.display_name_opt_in) else (st.pseudonym_id if st else "LRN-ANON")
                ),
                "pathway": r.pathway,
                "mode": r.mode,
                "steps_completed": r.steps_completed or [],
                "steps_completed_count": len(r.steps_completed or []),
                "prompts_given": r.prompts_given,
                "tutor_decisions": r.tutor_decisions,
                "errors_count": r.errors_count,
                "elapsed_ms": r.elapsed_ms,
                "started_at": r.started_at.isoformat() if r.started_at else None,
                "ended_at": r.ended_at.isoformat() if r.ended_at else None,
            }
        )

    return {"sessions": sessions}


def _build_notebook_response(
    db: Session,
    student: Student,
    runs: list[ScenarioRun],
) -> dict[str, Any]:
    exp_ids = {r.experience_id for r in runs}
    titles = {}
    if exp_ids:
        for exp in db.query(Experience).filter(Experience.id.in_(exp_ids)).all():
            titles[exp.id] = exp.title

    sessions = []
    for r in runs:
        events = (
            db.query(NotebookEvent)
            .filter(NotebookEvent.run_id == r.id)
            .order_by(NotebookEvent.t_ms.asc())
            .all()
        )
        sessions.append(
            {
                "session_id": str(r.id),
                "scenario_id": str(r.experience_id),
                "scenario_title": titles.get(r.experience_id, "Scenario"),
                "scenario_version": r.version_number,
                "pathway": r.pathway,
                "mode": r.mode,
                "steps_completed": r.steps_completed or [],
                "steps_completed_count": len(r.steps_completed or []),
                "prompts_given": r.prompts_given,
                "tutor_decisions": r.tutor_decisions,
                "errors_count": r.errors_count,
                "elapsed_ms": r.elapsed_ms,
                "started_at": r.started_at.isoformat() if r.started_at else None,
                "ended_at": r.ended_at.isoformat() if r.ended_at else None,
                "events": [
                    {
                        "id": str(ev.id),
                        "kind": ev.kind,
                        "step_id": ev.step_id,
                        "pathway": ev.pathway,
                        "t_ms": ev.t_ms,
                        "event_data": ev.event_data,
                    }
                    for ev in events
                ],
            }
        )

    return {
        "learner_id": str(student.id),
        "pseudonym_id": student.pseudonym_id,
        "display_name": student.name if student.display_name_opt_in else student.pseudonym_id,
        "display_name_opt_in": student.display_name_opt_in,
        "session_count": len(sessions),
        "sessions": sessions,
    }


# ---------------------------------------------------------------------------
# In-App Notifications (LC-6, FR-07)
# ---------------------------------------------------------------------------


@router.get("/notifications", tags=["Notifications"])
def list_notifications(
    db: Session = Depends(get_db),
    tutor: Tutor = Depends(get_current_tutor),
):
    items = (
        db.query(Notification)
        .filter(
            Notification.organisation_id == tutor.organisation_id,
            Notification.user_id == tutor.id,
        )
        .order_by(Notification.created_at.desc())
        .limit(50)
        .all()
    )
    unread_count = sum(1 for n in items if n.read_at is None)
    return {
        "unread_count": unread_count,
        "items": [
            {
                "id": str(n.id),
                "kind": n.kind,
                "title": n.title,
                "message": n.message,
                "ref_id": str(n.ref_id) if n.ref_id else None,
                "read_at": n.read_at.isoformat() if n.read_at else None,
                "created_at": n.created_at.isoformat() if n.created_at else None,
            }
            for n in items
        ],
    }


@router.post("/notifications/{notification_id}/read", tags=["Notifications"])
def mark_notification_read(
    notification_id: UUID,
    db: Session = Depends(get_db),
    tutor: Tutor = Depends(get_current_tutor),
):
    notif = (
        db.query(Notification)
        .filter(
            Notification.id == notification_id,
            Notification.organisation_id == tutor.organisation_id,
            Notification.user_id == tutor.id,
        )
        .first()
    )
    if notif is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    notif.read_at = datetime.utcnow()
    db.commit()
    return {"id": str(notif.id), "read_at": notif.read_at.isoformat()}


@router.post("/notifications/read-all", tags=["Notifications"])
def mark_all_notifications_read(
    db: Session = Depends(get_db),
    tutor: Tutor = Depends(get_current_tutor),
):
    now = datetime.utcnow()
    (
        db.query(Notification)
        .filter(
            Notification.organisation_id == tutor.organisation_id,
            Notification.user_id == tutor.id,
            Notification.read_at.is_(None),
        )
        .update({"read_at": now})
    )
    db.commit()
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Audit Log & School-Admin Export / Deletion (FR-19, FR-20)
# ---------------------------------------------------------------------------


@router.get("/audit-events", tags=["Audit"])
def list_audit_events(
    db: Session = Depends(get_db),
    tutor: Tutor = Depends(require_roles("tutor", "admin")),
):
    events = (
        db.query(AuditEvent)
        .filter(AuditEvent.organisation_id == tutor.organisation_id)
        .order_by(AuditEvent.created_at.desc())
        .limit(100)
        .all()
    )
    return [
        {
            "id": str(e.id),
            "user_id": str(e.user_id),
            "action": e.action,
            "ref_id": str(e.ref_id) if e.ref_id else None,
            "version_number": e.version_number,
            "details": e.details,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in events
    ]


@router.get("/school/export", tags=["School Admin"])
def export_school_data(
    db: Session = Depends(get_db),
    tutor: Tutor = Depends(require_roles("admin", "tutor")),
):
    """Export all school classes, modules, learners, scenarios, runs, and audit logs (FR-20)."""
    org_id = tutor.organisation_id
    classes = db.query(Classroom).filter(Classroom.organisation_id == org_id, Classroom.deleted_at.is_(None)).all()
    modules = db.query(Module).filter(Module.organisation_id == org_id, Module.deleted_at.is_(None)).all()
    class_ids = [c.id for c in classes]
    students = db.query(Student).filter(Student.class_id.in_(class_ids)).all() if class_ids else []
    scenarios = db.query(Experience).filter(Experience.organisation_id == org_id, Experience.deleted_at.is_(None)).all()
    runs = db.query(ScenarioRun).filter(ScenarioRun.organisation_id == org_id).all()
    audits = db.query(AuditEvent).filter(AuditEvent.organisation_id == org_id).all()

    return {
        "organisation_id": str(org_id),
        "exported_at": datetime.utcnow().isoformat(),
        "classes": [{"id": str(c.id), "name": c.name, "description": c.description} for c in classes],
        "modules": [{"id": str(m.id), "class_id": str(m.class_id), "name": m.name} for m in modules],
        "learners": [
            {
                "id": str(s.id),
                "class_id": str(s.class_id),
                "pseudonym_id": s.pseudonym_id,
                "display_name": s.name if s.display_name_opt_in else s.pseudonym_id,
            }
            for s in students
        ],
        "scenarios": [
            {"id": str(sc.id), "title": sc.title, "status": sc.status, "current_version": sc.current_version}
            for sc in scenarios
        ],
        "runs_count": len(runs),
        "audit_events_count": len(audits),
    }


@router.delete("/school/data", status_code=status.HTTP_200_OK, tags=["School Admin"])
def delete_school_data(
    db: Session = Depends(get_db),
    tutor: Tutor = Depends(require_roles("admin")),
):
    """Delete all school scenario, run, notebook, and class data (FR-20)."""
    org_id = tutor.organisation_id
    now = datetime.utcnow()
    db.query(NotebookEvent).filter(NotebookEvent.organisation_id == org_id).delete()
    db.query(ScenarioRun).filter(ScenarioRun.organisation_id == org_id).delete()
    db.query(JobRecord).filter(JobRecord.organisation_id == org_id).delete()
    db.query(Notification).filter(Notification.organisation_id == org_id).delete()
    db.query(Experience).filter(Experience.organisation_id == org_id).update({"deleted_at": now})
    db.query(Module).filter(Module.organisation_id == org_id).update({"deleted_at": now})
    db.query(Classroom).filter(Classroom.organisation_id == org_id).update({"deleted_at": now})
    _log_audit(db, tutor, "delete_school_data", org_id)
    db.commit()
    return {"status": "deleted", "organisation_id": str(org_id), "deleted_at": now.isoformat()}
