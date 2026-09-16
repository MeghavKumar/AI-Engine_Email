import pytest

from app.schemas.attachment import (
    AttachmentVerificationResult,
    AttachmentVerificationStatus,
)
from app.schemas.email import EmailDraft, SecurityAssessment
from app.schemas.recipient import (
    RecipientCandidate,
    RecipientVerificationDecision,
    RecipientVerificationStatus,
)
from app.schemas.workflow import (
    EmailWorkflowState,
    EmailWorkflowStatus,
)
from app.services.send_approval import SendApprovalService


def make_validated_state() -> EmailWorkflowState:
    draft = EmailDraft(
        to=["recipient@example.com"],
        subject="Project update",
        body="Here is the project update.",
        confidence=0.95,
    )

    recipient = RecipientCandidate(
        name="Recipient",
        email="recipient@example.com",
        source="known_context",
        confidence=0.95,
        reason="Recipient provided by the user.",
    )

    recipient_decision = RecipientVerificationDecision(
        request_id="recipient-001",
        status=RecipientVerificationStatus.APPROVED,
        decided_by="user-001",
        approved_recipients=[recipient],
    )

    attachment_result = AttachmentVerificationResult(
        status=AttachmentVerificationStatus.NOT_REQUIRED,
        required=False,
        reason="No attachment is required.",
    )

    security_assessment = SecurityAssessment(
        safe=True,
        pii_detected=False,
        prompt_injection_detected=False,
        reasons=[],
    )

    return EmailWorkflowState(
        workflow_id="workflow-001",
        status=EmailWorkflowStatus.SEND_APPROVAL,
        draft=draft,
        recipient_verification_decision=recipient_decision,
        attachment_verification_result=attachment_result,
        security_assessment=security_assessment,
    )


def test_validated_workflow_creates_send_approval_request():
    service = SendApprovalService()
    state = make_validated_state()

    request = service.create_request(
        state=state,
        request_id="send-001",
        requested_by="user-001",
    )

    assert request.request_id == "send-001"
    assert request.requested_by == "user-001"
    assert state.send_approval_request == request


def test_unvalidated_workflow_cannot_request_send_approval():
    service = SendApprovalService()
    state = make_validated_state()
    state.status = EmailWorkflowStatus.BLOCKED

    with pytest.raises(ValueError, match="pre-send validation"):
        service.create_request(
            state=state,
            request_id="send-002",
            requested_by="user-001",
        )


def test_workflow_without_draft_cannot_request_send_approval():
    service = SendApprovalService()
    state = make_validated_state()
    state.draft = None

    with pytest.raises(ValueError, match="draft is required"):
        service.create_request(
            state=state,
            request_id="send-003",
            requested_by="user-001",
        )
