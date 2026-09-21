from app.schemas.reminder_workflow import (
    ReminderWorkflowState,
    ReminderWorkflowStatus,
)
from app.schemas.reminder import ReminderDraft


def test_reminder_workflow_state_defaults():
    reminder = ReminderDraft(
        to=["recipient@example.com"],
        subject="Follow-up",
        body="Following up on my previous email.",
    )

    state = ReminderWorkflowState(
        workflow_id="workflow-001",
        status=ReminderWorkflowStatus.DRAFT_CREATED,
        reminder=reminder,
    )

    assert state.workflow_id == "workflow-001"
    assert state.status == ReminderWorkflowStatus.DRAFT_CREATED
    assert state.reminder == reminder
    assert state.security_assessment is None
    assert state.attachment_verification_result is None
    assert state.approval_request is None
    assert state.approval_decision is None
    assert state.attachments == []
    assert state.blocked_reason is None


def test_reminder_workflow_state_supports_ready_to_send():
    reminder = ReminderDraft(
        to=["recipient@example.com"],
        subject="Follow-up",
        body="Following up on my previous email.",
    )

    state = ReminderWorkflowState(
        workflow_id="workflow-002",
        status=ReminderWorkflowStatus.READY_TO_SEND,
        reminder=reminder,
    )

    assert state.status == ReminderWorkflowStatus.READY_TO_SEND
