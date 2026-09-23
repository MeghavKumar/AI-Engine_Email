from app.db.session import SessionLocal
from app.models import EmailAccount
from app.schemas.reminder import (
    ReminderApprovalDecision,
    ReminderApprovalStatus,
    ReminderDraft,
)
from app.schemas.reminder_workflow import ReminderWorkflowStatus
from app.services.reminder_workflow_persistence import (
    ReminderWorkflowPersistenceService,
)


def make_reminder() -> ReminderDraft:
    return ReminderDraft(
        to=["recipient@example.com"],
        subject="Follow-up",
        body="Following up on my previous email.",
    )


def test_reminder_workflow_persistence_integration():
    workflow_id = "test-reminder-workflow-persistence"

    with SessionLocal() as session:
        account = EmailAccount(
            user_id="test-user",
            provider="gmail",
            email_address="integration@example.com",
        )
        session.add(account)
        session.flush()

        service = ReminderWorkflowPersistenceService(session)

        try:
            workflow, state = service.create_and_persist(
                workflow_id=workflow_id,
                reminder=make_reminder(),
                email_account_id=account.id,
                user_id="test-user",
                provider="gmail",
            )

            session.commit()

            assert workflow.workflow_id == workflow_id
            assert state.status == ReminderWorkflowStatus.DRAFT_CREATED

            state = service.workflow_service.inspect_security(state)
            state = service.workflow_service.verify_attachments(state)
            state = service.workflow_service.request_approval(
                state,
                requested_by="test-user",
                reason="Reminder requires human approval.",
            )

            service.save(
                workflow=workflow,
                state=state,
            )

            session.commit()

            loaded = service.load(workflow_id)

            assert loaded is not None

            persisted_workflow, restored_state = loaded

            assert persisted_workflow.status == "APPROVAL"
            assert restored_state.status == ReminderWorkflowStatus.APPROVAL
            assert restored_state.approval_request is not None

            decision = ReminderApprovalDecision(
                request_id=restored_state.approval_request.request_id,
                status=ReminderApprovalStatus.APPROVED,
                decided_by="test-user",
            )

            restored_state = service.workflow_service.apply_approval_decision(
                restored_state,
                decision,
            )

            service.save(
                workflow=persisted_workflow,
                state=restored_state,
            )

            session.commit()

            final_loaded = service.load(workflow_id)

            assert final_loaded is not None

            final_workflow, final_state = final_loaded

            assert final_workflow.status == "READY_TO_SEND"
            assert final_state.status == ReminderWorkflowStatus.READY_TO_SEND
            assert final_state.reminder is not None
            assert final_state.reminder.status.value == "APPROVED"

        finally:
            workflow = service.persistence.repository.get_by_workflow_id(
                workflow_id
            )

            if workflow is not None:
                session.delete(workflow)
                session.flush()

            session.delete(account)
            session.commit()
