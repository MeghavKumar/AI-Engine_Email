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


def test_workflow_survives_process_restart():
    workflow_id = "test-workflow-restart-recovery"

    original_state = ReminderWorkflowState(
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

    account_id = None

    # Simulate the first process: create and persist the workflow.
    with SessionLocal() as session:
        account = EmailAccount(
            user_id="test-user",
            provider="gmail",
            email_address="recovery@example.com",
        )
        session.add(account)
        session.flush()

        account_id = account.id

        coordinator = WorkflowPersistenceCoordinator(session)

        coordinator.create(
            state=original_state,
            email_account_id=account.id,
            user_id="test-user",
            workflow_type="REMINDER",
            provider="gmail",
            message_id="message-before-restart",
            thread_id="thread-before-restart",
        )

        session.commit()

    # Simulate the process ending and a new process starting.
    with SessionLocal() as session:
        coordinator = WorkflowPersistenceCoordinator(session)

        loaded = coordinator.load(
            workflow_id=workflow_id,
            state_type=ReminderWorkflowState,
        )

        assert loaded is not None

        workflow, restored_state = loaded

        assert workflow.email_account_id == account_id
        assert workflow.message_id == "message-before-restart"
        assert workflow.thread_id == "thread-before-restart"
        assert workflow.status == "READY_TO_SEND"

        assert restored_state == original_state
        assert restored_state.workflow_id == workflow_id
        assert restored_state.status == ReminderWorkflowStatus.READY_TO_SEND
        assert restored_state.attachments[0].filename == "document.pdf"

    # Clean up using a separate fresh database session.
    with SessionLocal() as session:
        coordinator = WorkflowPersistenceCoordinator(session)

        workflow = coordinator.repository.get_by_workflow_id(workflow_id)

        if workflow is not None:
            session.delete(workflow)
            session.flush()

        account = session.get(EmailAccount, account_id)

        if account is not None:
            session.delete(account)

        session.commit()
