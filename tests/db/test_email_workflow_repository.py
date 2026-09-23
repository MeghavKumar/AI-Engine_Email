from app.db.session import SessionLocal
from app.db.repositories.email_workflow import EmailWorkflowRepository
from app.models import EmailAccount


def test_email_workflow_repository_lifecycle():
    workflow_id = "test-repository-lifecycle"
    
    with SessionLocal() as session:
        account = EmailAccount(
            user_id="test-user",
            provider="gmail",
            email_address="test@example.com",
        )
        session.add(account)
        session.flush()

        repository = EmailWorkflowRepository(session)

        try:
            workflow = repository.create(
                workflow_id=workflow_id,
                email_account_id=account.id,
                user_id="test-user",
                workflow_type="REMINDER",
                provider="gmail",
                status="DRAFT_CREATED",
                state={
                    "workflow_id": workflow_id,
                    "status": "DRAFT_CREATED",
                },
                message_id="message-123",
                thread_id="thread-123",
            )

            assert workflow.id is not None
            assert workflow.workflow_id == workflow_id
            assert workflow.email_account_id == account.id

            session.commit()

            loaded = repository.get_by_workflow_id(workflow_id)

            assert loaded is not None
            assert loaded.workflow_type == "REMINDER"
            assert loaded.provider == "gmail"
            assert loaded.message_id == "message-123"
            assert loaded.thread_id == "thread-123"
            assert loaded.state["status"] == "DRAFT_CREATED"

            repository.update(
                workflow=loaded,
                status="READY_TO_SEND",
                state={
                    "workflow_id": workflow_id,
                    "status": "READY_TO_SEND",
                },
                message_id="message-456",
                thread_id="thread-456",
            )

            session.commit()

            updated = repository.get_by_workflow_id(workflow_id)

            assert updated is not None
            assert updated.status == "READY_TO_SEND"
            assert updated.state["status"] == "READY_TO_SEND"
            assert updated.message_id == "message-456"
            assert updated.thread_id == "thread-456"

            repository.close(
                workflow=updated,
                status="COMPLETED",
                state={
                    "workflow_id": workflow_id,
                    "status": "COMPLETED",
                },
            )

            session.commit()

            closed = repository.get_by_workflow_id(workflow_id)

            assert closed is not None
            assert closed.status == "COMPLETED"
            assert closed.closed_at is not None
        finally:
            workflow = repository.get_by_workflow_id(workflow_id)
            if workflow is not None:
                session.delete(workflow)
                session.flush()

            session.delete(account)
            session.commit()


def test_email_workflow_repository_supports_initial_email_workflow():
    workflow_id = "test-initial-email-workflow"

    with SessionLocal() as session:
        account = EmailAccount(
            user_id="test-user",
            provider="gmail",
            email_address="initial@example.com",
        )
        session.add(account)
        session.flush()

        repository = EmailWorkflowRepository(session)

        try:
            workflow = repository.create(
                workflow_id=workflow_id,
                email_account_id=account.id,
                user_id="test-user",
                workflow_type="INITIAL_EMAIL",
                provider="gmail",
                status="DRAFT_CREATED",
                state={
                    "workflow_id": workflow_id,
                    "status": "DRAFT_CREATED",
                },
            )

            session.commit()

            loaded = repository.get_by_workflow_id(workflow_id)

            assert loaded is not None
            assert loaded.workflow_type == "INITIAL_EMAIL"
            assert loaded.email_account_id == account.id
        finally:
            workflow = repository.get_by_workflow_id(workflow_id)
            if workflow is not None:
                session.delete(workflow)
                session.flush()

            session.delete(account)
            session.commit()
