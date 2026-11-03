
from datetime import datetime
import uuid
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.classroom import Classroom
from app.models.module import Module
from app.models.student import Student
from app.models.class_schedule import ClassSchedule
from app.models.tutor import Tutor


class ClassWorkspaceRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_class(self, tutor: Tutor, name: str, description: str | None):
        classroom = Classroom(
            organisation_id=tutor.organisation_id,
            name=name.strip(),
            description=description,
        )
        self.db.add(classroom)
        self.db.commit()
        self.db.refresh(classroom)
        return classroom

    def list_classes(self, tutor: Tutor):
        return (
            self.db.query(Classroom)
            .filter(
                Classroom.organisation_id == tutor.organisation_id,
                Classroom.deleted_at.is_(None),
            )
            .order_by(Classroom.created_at.desc())
            .all()
        )

    def get_class(self, tutor: Tutor, class_id: UUID):
        return (
            self.db.query(Classroom)
            .filter(
                Classroom.id == class_id,
                Classroom.organisation_id == tutor.organisation_id,
                Classroom.deleted_at.is_(None),
            )
            .first()
        )

    def update_class(self, classroom: Classroom, values: dict):
        for key, value in values.items():
            setattr(classroom, key, value.strip() if key == "name" and value else value)
        self.db.commit()
        self.db.refresh(classroom)
        return classroom

    def delete_class(self, classroom: Classroom):
        classroom.deleted_at = datetime.utcnow()
        self.db.commit()

    def list_modules(self, tutor: Tutor, class_id: UUID):
        return (
            self.db.query(Module)
            .filter(
                Module.class_id == class_id,
                Module.organisation_id == tutor.organisation_id,
                Module.deleted_at.is_(None),
            )
            .order_by(Module.created_at.asc())
            .all()
        )

    def get_module(self, tutor: Tutor, class_id: UUID, module_id: UUID):
        return (
            self.db.query(Module)
            .filter(
                Module.id == module_id,
                Module.class_id == class_id,
                Module.organisation_id == tutor.organisation_id,
                Module.deleted_at.is_(None),
            )
            .first()
        )

    def add_module(self, tutor: Tutor, class_id: UUID, name: str, description: str | None):
        module = Module(
            organisation_id=tutor.organisation_id,
            class_id=class_id,
            name=name.strip(),
            description=description,
        )
        self.db.add(module)
        self.db.commit()
        self.db.refresh(module)
        return module

    def update_module(self, module: Module, values: dict):
        for key, value in values.items():
            setattr(module, key, value.strip() if key == "name" and value else value)
        module.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(module)
        return module

    def delete_module(self, module: Module):
        module.deleted_at = datetime.utcnow()
        self.db.commit()

    def list_students(self, class_id: UUID):
        return (
            self.db.query(Student)
            .filter(Student.class_id == class_id)
            .order_by(Student.created_at.asc())
            .all()
        )

    def get_student(self, class_id: UUID, student_id: UUID):
        return (
            self.db.query(Student)
            .filter(Student.id == student_id, Student.class_id == class_id)
            .first()
        )

    def add_student(
        self,
        class_id: UUID,
        name: str,
        pseudonym_id: str | None = None,
        display_name_opt_in: bool = False,
        comfort_overrides: dict | None = None,
    ):
        pseudo = (pseudonym_id or f"LRN-{uuid.uuid4().hex[:6].upper()}").strip()
        student = Student(
            class_id=class_id,
            name=name.strip(),
            pseudonym_id=pseudo,
            display_name_opt_in=display_name_opt_in,
            comfort_overrides=comfort_overrides,
        )
        self.db.add(student)
        self.db.commit()
        self.db.refresh(student)
        return student

    def update_student(self, student: Student, name: str, values: dict | None = None):
        if name is not None:
            student.name = name.strip()
        if values:
            for k, v in values.items():
                if k != "name" and v is not None:
                    setattr(student, k, v)
        self.db.commit()
        self.db.refresh(student)
        return student

    def delete_student(self, student: Student):
        self.db.delete(student)
        self.db.commit()

    def list_schedules(self, class_id: UUID):
        return (
            self.db.query(ClassSchedule)
            .filter(ClassSchedule.class_id == class_id)
            .order_by(ClassSchedule.created_at.asc())
            .all()
        )

    def get_schedule(self, class_id: UUID, schedule_id: UUID):
        return (
            self.db.query(ClassSchedule)
            .filter(
                ClassSchedule.id == schedule_id,
                ClassSchedule.class_id == class_id,
            )
            .first()
        )

    def add_schedule(self, class_id: UUID, values: dict):
        schedule = ClassSchedule(class_id=class_id, **values)
        self.db.add(schedule)
        self.db.commit()
        self.db.refresh(schedule)
        return schedule

    def update_schedule(self, schedule: ClassSchedule, values: dict):
        for key, value in values.items():
            setattr(schedule, key, value)
        self.db.commit()
        self.db.refresh(schedule)
        return schedule

    def delete_schedule(self, schedule: ClassSchedule):
        self.db.delete(schedule)
        self.db.commit()
