from app.schemas.attachment import AttachmentVerificationStatus
from app.schemas.reminder import (
    ReminderApprovalDecision,
    ReminderApprovalStatus,
    ReminderDraft,
)
from app.schemas.reminder_workflow import (
    ReminderWorkflowStatus,
)
from app.services.reminder_workflow import ReminderWorkflowService


def make_reminder(
    attachment_required: bool = False,
    attachment_names: list[str] | None = None,
) -> ReminderDraft:
    return ReminderDraft(
        to=["recipient@example.com"],
        subject="Follow-up",
        body="Following up on my previous email.",
        attachment_required=attachment_required,
        attachment_names=attachment_names or [],
    )


def test_create_state():
    service = ReminderWorkflowService()

    state = service.create_state(
        workflow_id="workflow-001",
        reminder=make_reminder(),
    )

    assert state.workflow_id == "workflow-001"
    assert state.status == ReminderWorkflowStatus.DRAFT_CREATED
    assert state.reminder is not None
    assert state.reminder.to == ["recipient@example.com"]


def test_security_inspection_allows_safe_reminder():
    service = ReminderWorkflowService()

    state = service.create_state(
        workflow_id="workflow-002",
        reminder=make_reminder(),
    )

    state = service.inspect_security(state)

    assert state.status == ReminderWorkflowStatus.SECURITY_CHECK
    assert state.security_assessment is not None
    assert state.security_assessment.safe is True
    assert state.blocked_reason is None


def test_attachment_verification_when_not_required():
    service = ReminderWorkflowService()

    state = service.create_state(
        workflow_id="workflow-003",
        reminder=make_reminder(),
    )

    state = service.inspect_security(state)
    state = service.verify_attachments(state)

    assert (
        state.status
        == ReminderWorkflowStatus.ATTACHMENT_VERIFICATION
    )
    assert state.attachment_verification_result is not None
    assert (
        state.attachment_verification_result.status
        == AttachmentVerificationStatus.NOT_REQUIRED
    )


def test_required_attachment_is_detected_as_missing():
    service = ReminderWorkflowService()

    state = service.create_state(
        workflow_id="workflow-004",
        reminder=make_reminder(
            attachment_required=True,
            attachment_names=["document.pdf"],
        ),
    )

    state = service.inspect_security(state)
    state = service.verify_attachments(
        state,
        available_attachments=[],
    )

    assert state.status == ReminderWorkflowStatus.ATTACHMENT_VERIFICATION
    assert state.attachment_verification_result is not None
    assert (
        state.attachment_verification_result.status
        == AttachmentVerificationStatus.MISSING
    )
    assert (
        state.attachment_verification_result.missing_attachments
        == ["document.pdf"]
    )


def test_required_attachment_is_verified_when_available():
    service = ReminderWorkflowService()

    state = service.create_state(
        workflow_id="workflow-005",
        reminder=make_reminder(
            attachment_required=True,
            attachment_names=["document.pdf"],
        ),
    )

    state = service.inspect_security(state)
    state = service.verify_attachments(
        state,
        available_attachments=["document.pdf"],
    )

    assert state.attachment_verification_result is not None
    assert (
        state.attachment_verification_result.status
        == AttachmentVerificationStatus.VERIFIED
    )


def test_request_approval_moves_valid_reminder_to_approval():
    service = ReminderWorkflowService()

    state = service.create_state(
        workflow_id="workflow-006",
        reminder=make_reminder(),
    )

    state = service.inspect_security(state)
    state = service.verify_attachments(state)
    state = service.request_approval(
        state,
        requested_by="user-001",
        reason="Reminder requires human approval before sending.",
    )

    assert state.status == ReminderWorkflowStatus.APPROVAL
    assert state.approval_request is not None
    assert state.approval_request.requested_by == "user-001"
    assert state.blocked_reason is None


def test_approved_reminder_moves_to_ready_to_send():
    service = ReminderWorkflowService()

    state = service.create_state(
        workflow_id="workflow-007",
        reminder=make_reminder(),
    )

    state = service.inspect_security(state)
    state = service.verify_attachments(state)
    state = service.request_approval(
        state,
        requested_by="user-001",
        reason="Reminder requires human approval before sending.",
    )

    decision = ReminderApprovalDecision(
        request_id=state.approval_request.request_id,
        status=ReminderApprovalStatus.APPROVED,
        decided_by="user-001",
    )

    state = service.apply_approval_decision(
        state,
        decision=decision,
    )

    assert state.status == ReminderWorkflowStatus.READY_TO_SEND
    assert state.reminder is not None
    assert state.reminder.status.value == "APPROVED"
    assert state.approval_decision is not None
    assert state.blocked_reason is None


def test_rejected_reminder_is_blocked():
    service = ReminderWorkflowService()

    state = service.create_state(
        workflow_id="workflow-008",
        reminder=make_reminder(),
    )

    state = service.inspect_security(state)
    state = service.verify_attachments(state)
    state = service.request_approval(
        state,
        requested_by="user-001",
        reason="Reminder requires human approval before sending.",
    )

    decision = ReminderApprovalDecision(
        request_id=state.approval_request.request_id,
        status=ReminderApprovalStatus.REJECTED,
        decided_by="user-001",
    )

    state = service.apply_approval_decision(
        state,
        decision=decision,
    )

    assert state.status == ReminderWorkflowStatus.BLOCKED
    assert state.reminder is not None
    assert state.reminder.status.value == "REJECTED"
    assert state.approval_decision is not None
    assert state.blocked_reason == "Reminder approval was rejected."
