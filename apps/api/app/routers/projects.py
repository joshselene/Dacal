
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from ..dependencies import get_db, get_current_tutor
from ..models.project import Project
from ..models.classroom import Classroom
from ..models.module import Module
from ..models.tutor import Tutor
from ..schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse

router = APIRouter()


def validate_class_and_module(
    db: Session,
    tutor: Tutor,
    class_id: UUID | None,
    module_id: UUID | None,
):
    if class_id is not None:
        classroom = db.query(Classroom).filter(
            Classroom.id == class_id,
            Classroom.organisation_id == tutor.organisation_id,
            Classroom.deleted_at.is_(None),
        ).first()

        if classroom is None:
            raise HTTPException(
                status_code=400,
                detail="Class not found in your organisation",
            )

    if module_id is not None:
        module = db.query(Module).filter(
            Module.id == module_id,
            Module.organisation_id == tutor.organisation_id,
            Module.deleted_at.is_(None),
        ).first()

        if module is None:
            raise HTTPException(
                status_code=400,
                detail="Module not found in your organisation",
            )

        if class_id is not None and module.class_id != class_id:
            raise HTTPException(
                status_code=400,
                detail="The module does not belong to the selected class",
            )


def get_project_or_404(
    db: Session,
    tutor: Tutor,
    project_id: UUID,
) -> Project:
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.organisation_id == tutor.organisation_id,
        Project.deleted_at.is_(None),
    ).first()

    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    return project


@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_project(
    request: ProjectCreate,
    db: Session = Depends(get_db),
    tutor: Tutor = Depends(get_current_tutor),
):
    validate_class_and_module(
        db, tutor, request.class_id, request.module_id
    )

    project = Project(
        organisation_id=tutor.organisation_id,
        created_by_tutor_id=tutor.id,
        name=request.name.strip(),
        description=request.description,
        class_id=request.class_id,
        module_id=request.module_id,
        status="draft",
    )

    if not project.name:
        raise HTTPException(status_code=422, detail="Project name is required")

    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("", response_model=list[ProjectResponse])
def list_projects(
    db: Session = Depends(get_db),
    tutor: Tutor = Depends(get_current_tutor),
):
    return db.query(Project).filter(
        Project.organisation_id == tutor.organisation_id,
        Project.deleted_at.is_(None),
    ).order_by(Project.created_at.desc()).all()


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: UUID,
    db: Session = Depends(get_db),
    tutor: Tutor = Depends(get_current_tutor),
):
    return get_project_or_404(db, tutor, project_id)


@router.patch("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: UUID,
    request: ProjectUpdate,
    db: Session = Depends(get_db),
    tutor: Tutor = Depends(get_current_tutor),
):
    project = get_project_or_404(db, tutor, project_id)
    changes = request.model_dump(exclude_unset=True)

    if "name" in changes:
        if changes["name"] is None or not changes["name"].strip():
            raise HTTPException(
                status_code=422, detail="Project name cannot be empty"
            )
        changes["name"] = changes["name"].strip()

    new_class_id = changes.get("class_id", project.class_id)
    new_module_id = changes.get("module_id", project.module_id)

    validate_class_and_module(
        db, tutor, new_class_id, new_module_id
    )

    for field, value in changes.items():
        setattr(project, field, value)

    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: UUID,
    db: Session = Depends(get_db),
    tutor: Tutor = Depends(get_current_tutor),
):
    project = get_project_or_404(db, tutor, project_id)
    project.deleted_at = datetime.utcnow()
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
