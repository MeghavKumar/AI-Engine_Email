from typing import TypeVar

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.repositories.email_workflow import EmailWorkflowRepository
from app.models.email_workflow import EmailWorkflow
from app.services.workflow_persistence import WorkflowPersistenceService

WorkflowStateT = TypeVar("WorkflowStateT", bound=BaseModel)


class WorkflowPersistenceCoordinator:
    """Coordinate typed workflow state with database persistence."""

    def __init__(
        self,
        session: Session,
        persistence_service: WorkflowPersistenceService | None = None,
    ):
        self.repository = EmailWorkflowRepository(session)
        self.persistence = (
            persistence_service or WorkflowPersistenceService()
        )

    def create(
        self,
        state: BaseModel,
        email_account_id: int,
        user_id: str,
        workflow_type: str,
        provider: str,
        message_id: str | None = None,
        thread_id: str | None = None,
    ) -> EmailWorkflow:
        """Persist a new workflow state."""

        workflow_id = self._get_workflow_id(state)

        return self.repository.create(
            workflow_id=workflow_id,
            email_account_id=email_account_id,
            user_id=user_id,
            workflow_type=workflow_type,
            provider=provider,
            status=self._get_status(state),
            state=self.persistence.serialize(state),
            message_id=message_id,
            thread_id=thread_id,
        )

    def update(
        self,
        workflow: EmailWorkflow,
        state: BaseModel,
        message_id: str | None = None,
        thread_id: str | None = None,
    ) -> EmailWorkflow:
        """Persist a new state for an existing workflow."""

        return self.repository.update(
            workflow=workflow,
            status=self._get_status(state),
            state=self.persistence.serialize(state),
            message_id=message_id,
            thread_id=thread_id,
        )

    def load(
        self,
        workflow_id: str,
        state_type: type[WorkflowStateT],
    ) -> tuple[EmailWorkflow, WorkflowStateT] | None:
        """Load a database workflow and restore its typed state."""

        workflow = self.repository.get_by_workflow_id(workflow_id)

        if workflow is None:
            return None

        state = self.persistence.deserialize(
            workflow.state,
            state_type,
        )

        return workflow, state

    def close(
        self,
        workflow: EmailWorkflow,
        state: BaseModel,
    ) -> EmailWorkflow:
        """Persist the final state and mark the workflow closed."""

        return self.repository.close(
            workflow=workflow,
            status=self._get_status(state),
            state=self.persistence.serialize(state),
        )

    @staticmethod
    def _get_workflow_id(state: BaseModel) -> str:
        workflow_id = getattr(state, "workflow_id", None)

        if not workflow_id:
            raise ValueError(
                "Workflow state must contain a workflow_id."
            )

        return workflow_id

    @staticmethod
    def _get_status(state: BaseModel) -> str:
        status = getattr(state, "status", None)

        if status is None:
            raise ValueError(
                "Workflow state must contain a status."
            )

        return status.value if hasattr(status, "value") else str(status)
