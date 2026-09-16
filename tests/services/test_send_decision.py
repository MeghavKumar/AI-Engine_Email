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
from app.services.pre_send_workflow import PreSendWorkflowService
from app.services.send_decision import SendDecisionService


def make_state() -> EmailWorkflowState:
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

    workflow = PreSendWorkflowService()

    state = workflow.create_state(
        workflow_id="workflow-001",
        draft=draft,
        recipient_decision=recipient_decision,
        attachment_result=attachment_result,
        security_assessment=security_assessment,
    )

    workflow.validate(state)

    workflow.request_send_approval(
        state=state,
        request_id="send-001",
        requested_by="user-001",
    )

    return state


def test_approve_moves_workflow_to_ready_to_send():
    service = SendDecisionService()
    state = make_state()

    decision = service.approve(
        state=state,
        decided_by="user-001",
        comment="Approved after reviewing recipients.",
    )

    assert decision.status == ApprovalStatus.APPROVED
    assert decision.decided_by == "user-001"
    assert state.status == EmailWorkflowStatus.READY_TO_SEND
    assert state.send_approval_decision == decision


def test_reject_moves_workflow_to_blocked():
    service = SendDecisionService()
    state = make_state()

    decision = service.reject(
        state=state,
        decided_by="user-001",
        comment="Recipient list needs correction.",
    )

    assert decision.status == ApprovalStatus.REJECTED
    assert decision.decided_by == "user-001"
    assert state.status == EmailWorkflowStatus.BLOCKED
    assert state.blocked_reason == "Recipient list needs correction."


def test_decided_request_cannot_be_decided_again():
    service = SendDecisionService()
    state = make_state()

    service.approve(
        state=state,
        decided_by="user-001",
    )

    with pytest.raises(
        ValueError,
        match="waiting for send approval",
    ):
        service.reject(
            state=state,
            decided_by="user-001",
        )
