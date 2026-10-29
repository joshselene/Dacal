
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import get_current_tutor
from app.models.tutor import Tutor
from app.modules.classes.infrastructure.persistence.class_workspace_repository import (
    ClassWorkspaceRepository,
)
from app.schemas.class_workspace import (
    ClassWorkspaceCreate,
    ClassWorkspaceUpdate,
    ClassWorkspaceResponse,
    StudentCreate,
    StudentResponse,
    ScheduleCreate,
    ScheduleResponse,
)

router = APIRouter()


def get_owned_class(repo: ClassWorkspaceRepository, tutor: Tutor, class_id: UUID):
    classroom = repo.get_class(tutor, class_id)
    if classroom is None:
        raise HTTPException(status_code=404, detail="Class not found")
    return classroom


@router.post(
    "",
    response_model=ClassWorkspaceResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_class(
    payload: ClassWorkspaceCreate,
    db: Session = Depends(get_db),
    tutor: Tutor = Depends(get_current_tutor),
):
    repo = ClassWorkspaceRepository(db)
    return repo.create_class(tutor, payload.name, payload.description)


@router.get("", response_model=list[ClassWorkspaceResponse])
def list_classes(
    db: Session = Depends(get_db),
    tutor: Tutor = Depends(get_current_tutor),
):
    return ClassWorkspaceRepository(db).list_classes(tutor)


@router.get("/{class_id}", response_model=ClassWorkspaceResponse)
def get_class(
    class_id: UUID,
    db: Session = Depends(get_db),
    tutor: Tutor = Depends(get_current_tutor),
):
    repo = ClassWorkspaceRepository(db)
    return get_owned_class(repo, tutor, class_id)


@router.patch("/{class_id}", response_model=ClassWorkspaceResponse)
def update_class(
    class_id: UUID,
    payload: ClassWorkspaceUpdate,
    db: Session = Depends(get_db),
    tutor: Tutor = Depends(get_current_tutor),
):
    repo = ClassWorkspaceRepository(db)
    classroom = get_owned_class(repo, tutor, class_id)
    values = payload.model_dump(exclude_unset=True)
    if not values:
        return classroom
    if "name" in values and values["name"] is not None:
        values["name"] = values["name"].strip()
    return repo.update_class(classroom, values)


@router.delete("/{class_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_class(
    class_id: UUID,
    db: Session = Depends(get_db),
    tutor: Tutor = Depends(get_current_tutor),
):
    repo = ClassWorkspaceRepository(db)
    classroom = get_owned_class(repo, tutor, class_id)
    repo.delete_class(classroom)


@router.get("/{class_id}/students", response_model=list[StudentResponse])
def list_students(
    class_id: UUID,
    db: Session = Depends(get_db),
    tutor: Tutor = Depends(get_current_tutor),
):
    repo = ClassWorkspaceRepository(db)
    get_owned_class(repo, tutor, class_id)
    return repo.list_students(class_id)


@router.post(
    "/{class_id}/students",
    response_model=StudentResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_student(
    class_id: UUID,
    payload: StudentCreate,
    db: Session = Depends(get_db),
    tutor: Tutor = Depends(get_current_tutor),
):
    repo = ClassWorkspaceRepository(db)
    get_owned_class(repo, tutor, class_id)
    return repo.add_student(class_id, payload.name)


@router.patch("/{class_id}/students/{student_id}", response_model=StudentResponse)
def update_student(
    class_id: UUID,
    student_id: UUID,
    payload: StudentCreate,
    db: Session = Depends(get_db),
    tutor: Tutor = Depends(get_current_tutor),
):
    repo = ClassWorkspaceRepository(db)
    get_owned_class(repo, tutor, class_id)
    student = repo.get_student(class_id, student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    return repo.update_student(student, payload.name)


@router.delete(
    "/{class_id}/students/{student_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_student(
    class_id: UUID,
    student_id: UUID,
    db: Session = Depends(get_db),
    tutor: Tutor = Depends(get_current_tutor),
):
    repo = ClassWorkspaceRepository(db)
    get_owned_class(repo, tutor, class_id)
    student = repo.get_student(class_id, student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    repo.delete_student(student)


@router.get("/{class_id}/schedules", response_model=list[ScheduleResponse])
def list_schedules(
    class_id: UUID,
    db: Session = Depends(get_db),
    tutor: Tutor = Depends(get_current_tutor),
):
    repo = ClassWorkspaceRepository(db)
    get_owned_class(repo, tutor, class_id)
    return repo.list_schedules(class_id)


@router.post(
    "/{class_id}/schedules",
    response_model=ScheduleResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_schedule(
    class_id: UUID,
    payload: ScheduleCreate,
    db: Session = Depends(get_db),
    tutor: Tutor = Depends(get_current_tutor),
):
    repo = ClassWorkspaceRepository(db)
    get_owned_class(repo, tutor, class_id)
    return repo.add_schedule(class_id, payload.model_dump())


@router.patch("/{class_id}/schedules/{schedule_id}", response_model=ScheduleResponse)
def update_schedule(
    class_id: UUID,
    schedule_id: UUID,
    payload: ScheduleCreate,
    db: Session = Depends(get_db),
    tutor: Tutor = Depends(get_current_tutor),
):
    repo = ClassWorkspaceRepository(db)
    get_owned_class(repo, tutor, class_id)
    schedule = repo.get_schedule(class_id, schedule_id)
    if schedule is None:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return repo.update_schedule(schedule, payload.model_dump())


@router.delete(
    "/{class_id}/schedules/{schedule_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_schedule(
    class_id: UUID,
    schedule_id: UUID,
    db: Session = Depends(get_db),
    tutor: Tutor = Depends(get_current_tutor),
):
    repo = ClassWorkspaceRepository(db)
    get_owned_class(repo, tutor, class_id)
    schedule = repo.get_schedule(class_id, schedule_id)
    if schedule is None:
        raise HTTPException(status_code=404, detail="Schedule not found")
    repo.delete_schedule(schedule)
