from app.schemas.reminder import (
    ReminderApprovalDecision,
    ReminderApprovalStatus,
    ReminderDraft,
)
from app.schemas.reminder_workflow import ReminderWorkflowStatus
from app.services.reminder_send import ReminderSendService
from app.services.reminder_workflow import ReminderWorkflowService


class FakeEmailProvider:
    def __init__(self):
        self.sent_messages = []

    def send_message(
        self,
        account_id: str,
        message: dict,
    ) -> str:
        self.sent_messages.append(
            {
                "account_id": account_id,
                "message": message,
            }
        )
        return "provider-message-456"


def make_reminder() -> ReminderDraft:
    return ReminderDraft(
        to=["recipient@example.com"],
        subject="Follow-up",
        body="Just following up on my previous email.",
    )


def test_approved_workflow_can_be_sent():
    provider = FakeEmailProvider()
    workflow_service = ReminderWorkflowService()
    send_service = ReminderSendService(provider)

    state = workflow_service.create_state(
        workflow_id="workflow-send-001",
        reminder=make_reminder(),
    )

    state = workflow_service.inspect_security(state)
    state = workflow_service.verify_attachments(state)

    state = workflow_service.request_approval(
        state,
        requested_by="user-001",
        reason="Reminder requires human approval before sending.",
    )

    decision = ReminderApprovalDecision(
        request_id=state.approval_request.request_id,
        status=ReminderApprovalStatus.APPROVED,
        decided_by="user-001",
    )

    state = workflow_service.apply_approval_decision(
        state,
        decision=decision,
    )

    assert state.status == ReminderWorkflowStatus.READY_TO_SEND
    assert state.reminder is not None

    message_id = send_service.send(
        reminder=state.reminder,
        account_id="account-123",
    )

    assert message_id == "provider-message-456"
    assert len(provider.sent_messages) == 1

    sent = provider.sent_messages[0]

    assert sent["account_id"] == "account-123"
    assert sent["message"]["to"] == ["recipient@example.com"]
    assert sent["message"]["subject"] == "Follow-up"
    assert sent["message"]["body"] == (
        "Just following up on my previous email."
    )
