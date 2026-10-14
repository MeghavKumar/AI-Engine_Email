import pytest

from app.schemas.attachment import (
    AttachmentVerificationResult,
    AttachmentVerificationStatus,
)
from app.schemas.email import (
    ApprovalStatus,
    EmailDraft,
    SecurityAssessment,
)
from app.schemas.recipient import (
    RecipientCandidate,
    RecipientVerificationDecision,
    RecipientVerificationStatus,
)
from app.schemas.workflow import (
    EmailWorkflowState,
    EmailWorkflowStatus,
)
from app.services.email_approval_coordinator import EmailApprovalCoordinator


def make_state(
    subject: str = "Project update",
    original_thread_subject: str | None = "Project update",
    safe: bool = True,
) -> EmailWorkflowState:
    recipient = RecipientCandidate(
        name="Recipient",
        email="recipient@example.com",
        source="known_context",
        confidence=0.95,
        reason="Recipient was identified for this message.",
    )

    return EmailWorkflowState(
        workflow_id="coordinator-test-001",
        status=EmailWorkflowStatus.DRAFT_CREATED,
        draft=EmailDraft(
            to=["recipient@example.com"],
            subject=subject,
            body="Here is the project update.",
            confidence=0.95,
        ),
        original_thread_subject=original_thread_subject,
        recipient_verification_decision=RecipientVerificationDecision(
            request_id="recipient-001",
            status=RecipientVerificationStatus.APPROVED,
            decided_by="reviewer",
            approved_recipients=[recipient],
        ),
        attachment_verification_result=AttachmentVerificationResult(
            status=AttachmentVerificationStatus.NOT_REQUIRED,
            required=False,
            reason="No attachment is required.",
        ),
        security_assessment=SecurityAssessment(
            safe=safe,
            pii_detected=False,
            prompt_injection_detected=False,
            reasons=[],
        ),
    )


def test_unchanged_subject_goes_directly_to_send_approval():
    coordinator = EmailApprovalCoordinator()
    state = make_state(
        subject="Re: Project update",
        original_thread_subject="Project update",
    )

    request = coordinator.validate_and_request_approval(
        state=state,
        request_id="send-001",
        requested_by="reviewer",
    )

    assert request is not None
    assert request.request_id == "send-001"
    assert state.status == EmailWorkflowStatus.SEND_APPROVAL
    assert state.subject_change_approval_request is None
    assert state.send_approval_request == request


def test_changed_subject_requires_separate_approval_first():
    coordinator = EmailApprovalCoordinator()
    state = make_state(
        subject="Urgent: project update",
        original_thread_subject="Project update",
    )

    request = coordinator.validate_and_request_approval(
        state=state,
        request_id="subject-001",
        requested_by="reviewer",
    )

    assert request is not None
    assert request.request_id == "subject-001"
    assert state.subject_change_approval_request == request
    assert state.send_approval_request is None

    decision = coordinator.approve_subject_change(
        state=state,
        decided_by="reviewer",
        comment="Subject change reviewed.",
    )

    assert decision.status == ApprovalStatus.APPROVED

    send_request = coordinator.request_send_approval(
        state=state,
        request_id="send-002",
        requested_by="reviewer",
    )

    assert send_request.request_id == "send-002"
    assert state.send_approval_request == send_request


def test_changed_subject_cannot_request_send_approval_without_approval():
    coordinator = EmailApprovalCoordinator()
    state = make_state(
        subject="Urgent: project update",
        original_thread_subject="Project update",
    )

    coordinator.validate_and_request_approval(
        state=state,
        request_id="subject-002",
        requested_by="reviewer",
    )

    with pytest.raises(ValueError, match="Subject change requires explicit approval"):
        coordinator.request_send_approval(
            state=state,
            request_id="send-003",
            requested_by="reviewer",
        )


def test_failed_validation_does_not_create_approval_request():
    coordinator = EmailApprovalCoordinator()
    state = make_state(safe=False)

    request = coordinator.validate_and_request_approval(
        state=state,
        request_id="send-004",
        requested_by="reviewer",
    )

    assert request is None
    assert state.status == EmailWorkflowStatus.BLOCKED
    assert state.send_approval_request is None
    assert state.subject_change_approval_request is None


def test_send_approval_is_still_required_after_subject_approval():
    coordinator = EmailApprovalCoordinator()
    state = make_state(
        subject="Urgent: project update",
        original_thread_subject="Project update",
    )

    coordinator.validate_and_request_approval(
        state=state,
        request_id="subject-003",
        requested_by="reviewer",
    )
    coordinator.approve_subject_change(
        state=state,
        decided_by="reviewer",
    )

    assert state.status == EmailWorkflowStatus.SEND_APPROVAL
    assert state.send_approval_request is None
    assert state.send_approval_decision is None

    coordinator.request_send_approval(
        state=state,
        request_id="send-005",
        requested_by="reviewer",
    )
    decision = coordinator.approve_send(
        state=state,
        decided_by="reviewer",
    )

    assert decision.status == ApprovalStatus.APPROVED
    assert state.status == EmailWorkflowStatus.READY_TO_SEND
