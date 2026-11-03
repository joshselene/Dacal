"""Application use cases for managing classes, modules, learners, and schedules."""

from uuid import UUID
from app.models.tutor import Tutor
from app.modules.classes.infrastructure.persistence.class_workspace_repository import (
    ClassWorkspaceRepository,
)


class ManageClassWorkspaceUseCase:
    def __init__(self, repo: ClassWorkspaceRepository):
        self.repo = repo

    def list_classes(self, tutor: Tutor):
        return self.repo.list_classes(tutor)

    def create_class(self, tutor: Tutor, name: str, description: str | None):
        return self.repo.create_class(tutor, name, description)

    def list_modules(self, tutor: Tutor, class_id: UUID):
        return self.repo.list_modules(tutor, class_id)
