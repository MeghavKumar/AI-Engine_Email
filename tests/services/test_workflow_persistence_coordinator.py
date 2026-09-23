from pathlib import Path

from app.db.session import SessionLocal
from app.models import EmailAccount
from app.schemas.email_attachment import EmailAttachment
from app.schemas.reminder_workflow import (
    ReminderWorkflowState,
    ReminderWorkflowStatus,
)
from app.services.workflow_persistence_coordinator import (
    WorkflowPersistenceCoordinator,
)


def test_workflow_persistence_coordinator_lifecycle():
    workflow_id = "test-persistence-coordinator"

    initial_state = ReminderWorkflowState(
        workflow_id=workflow_id,
        status=ReminderWorkflowStatus.DRAFT_CREATED,
    )

    ready_state = ReminderWorkflowState(
        workflow_id=workflow_id,
        status=ReminderWorkflowStatus.READY_TO_SEND,
        attachments=[
            EmailAttachment(
                filename="document.pdf",
                content_type="application/pdf",
                file_path=Path("/tmp/document.pdf"),
            )
        ],
    )

    closed_state = ReminderWorkflowState(
        workflow_id=workflow_id,
        status=ReminderWorkflowStatus.BLOCKED,
        blocked_reason="Completed for test.",
    )

    with SessionLocal() as session:
        account = EmailAccount(
            user_id="test-user",
            provider="gmail",
            email_address="coordinator@example.com",
        )
        session.add(account)
        session.flush()

        coordinator = WorkflowPersistenceCoordinator(session)

        try:
            workflow = coordinator.create(
                state=initial_state,
                email_account_id=account.id,
                user_id="test-user",
                workflow_type="REMINDER",
                provider="gmail",
            )

            session.commit()

            assert workflow.workflow_id == workflow_id
            assert workflow.status == "DRAFT_CREATED"

            loaded = coordinator.load(
                workflow_id=workflow_id,
                state_type=ReminderWorkflowState,
            )

            assert loaded is not None

            persisted_workflow, restored_state = loaded

            assert persisted_workflow.workflow_id == workflow_id
            assert isinstance(restored_state, ReminderWorkflowState)
            assert restored_state == initial_state

            coordinator.update(
                workflow=persisted_workflow,
                state=ready_state,
                message_id="message-123",
                thread_id="thread-123",
            )

            session.commit()

            loaded_after_update = coordinator.load(
                workflow_id=workflow_id,
                state_type=ReminderWorkflowState,
            )

            assert loaded_after_update is not None

            updated_workflow, updated_state = loaded_after_update

            assert updated_workflow.status == "READY_TO_SEND"
            assert updated_workflow.message_id == "message-123"
            assert updated_workflow.thread_id == "thread-123"
            assert updated_state == ready_state
            assert updated_state.attachments[0].filename == "document.pdf"

            coordinator.close(
                workflow=updated_workflow,
                state=closed_state,
            )

            session.commit()

            loaded_after_close = coordinator.load(
                workflow_id=workflow_id,
                state_type=ReminderWorkflowState,
            )

            assert loaded_after_close is not None

            closed_workflow, restored_closed_state = loaded_after_close

            assert closed_workflow.status == "BLOCKED"
            assert closed_workflow.closed_at is not None
            assert restored_closed_state == closed_state

        finally:
            workflow = coordinator.repository.get_by_workflow_id(
                workflow_id
            )

            if workflow is not None:
                session.delete(workflow)
                session.flush()

            session.delete(account)
            session.commit()
