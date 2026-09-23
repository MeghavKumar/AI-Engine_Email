from sqlalchemy.orm import Session

from app.models.email_workflow import EmailWorkflow
from app.schemas.reminder import ReminderDraft
from app.schemas.reminder_workflow import ReminderWorkflowState
from app.services.reminder_workflow import ReminderWorkflowService
from app.services.workflow_persistence_coordinator import (
    WorkflowPersistenceCoordinator,
)


class ReminderWorkflowPersistenceService:
    """Coordinate reminder workflow logic with durable persistence."""

    def __init__(
        self,
        session: Session,
        workflow_service: ReminderWorkflowService | None = None,
    ):
        self.workflow_service = (
            workflow_service or ReminderWorkflowService()
        )
        self.persistence = WorkflowPersistenceCoordinator(session)

    def create_and_persist(
        self,
        workflow_id: str,
        reminder: ReminderDraft,
        email_account_id: int,
        user_id: str,
        provider: str,
        message_id: str | None = None,
        thread_id: str | None = None,
    ) -> tuple[EmailWorkflow, ReminderWorkflowState]:
        """Create a reminder workflow and persist its initial state."""

        state = self.workflow_service.create_state(
            workflow_id=workflow_id,
            reminder=reminder,
        )

        workflow = self.persistence.create(
            state=state,
            email_account_id=email_account_id,
            user_id=user_id,
            workflow_type="REMINDER",
            provider=provider,
            message_id=message_id,
            thread_id=thread_id,
        )

        return workflow, state

    def save(
        self,
        workflow: EmailWorkflow,
        state: ReminderWorkflowState,
        message_id: str | None = None,
        thread_id: str | None = None,
    ) -> EmailWorkflow:
        """Persist the current reminder workflow state."""

        return self.persistence.update(
            workflow=workflow,
            state=state,
            message_id=message_id,
            thread_id=thread_id,
        )

    def load(
        self,
        workflow_id: str,
    ) -> tuple[EmailWorkflow, ReminderWorkflowState] | None:
        """Restore a persisted reminder workflow."""

        return self.persistence.load(
            workflow_id=workflow_id,
            state_type=ReminderWorkflowState,
        )

    def close(
        self,
        workflow: EmailWorkflow,
        state: ReminderWorkflowState,
    ) -> EmailWorkflow:
        """Persist the final reminder state and close the workflow."""

        return self.persistence.close(
            workflow=workflow,
            state=state,
        )
