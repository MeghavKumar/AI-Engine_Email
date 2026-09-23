from pathlib import Path

from app.db.repositories.email_workflow import EmailWorkflowRepository
from app.db.session import SessionLocal
from app.models import EmailAccount
from app.schemas.email_attachment import EmailAttachment
from app.schemas.reminder_workflow import (
    ReminderWorkflowState,
    ReminderWorkflowStatus,
)
from app.services.workflow_persistence import WorkflowPersistenceService


def test_reminder_workflow_state_persists_and_restores_from_postgres():
    workflow_id = "test-reminder-persistence-integration"

    state = ReminderWorkflowState(
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

    persistence = WorkflowPersistenceService()

    with SessionLocal() as session:
        account = EmailAccount(
            user_id="test-user",
            provider="gmail",
            email_address="persistence@example.com",
        )
        session.add(account)
        session.flush()

        repository = EmailWorkflowRepository(session)

        try:
            serialized_state = persistence.serialize(state)

            workflow = repository.create(
                workflow_id=workflow_id,
                email_account_id=account.id,
                user_id="test-user",
                workflow_type="REMINDER",
                provider="gmail",
                status=state.status.value,
                state=serialized_state,
            )

            session.commit()

            loaded = repository.get_by_workflow_id(workflow_id)

            assert loaded is not None
            assert loaded.workflow_id == workflow_id
            assert loaded.workflow_type == "REMINDER"
            assert loaded.provider == "gmail"
            assert loaded.state["status"] == "READY_TO_SEND"

            restored = persistence.deserialize(
                loaded.state,
                ReminderWorkflowState,
            )

            assert restored == state
            assert restored.workflow_id == workflow_id
            assert restored.status == ReminderWorkflowStatus.READY_TO_SEND
            assert restored.attachments[0].filename == "document.pdf"
            assert restored.attachments[0].file_path == Path(
                "/tmp/document.pdf"
            )

        finally:
            workflow = repository.get_by_workflow_id(workflow_id)

            if workflow is not None:
                session.delete(workflow)
                session.flush()

            session.delete(account)
            session.commit()
