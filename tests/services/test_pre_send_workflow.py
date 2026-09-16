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
    EmailWorkflowStatus,
)
from app.services.pre_send_workflow import PreSendWorkflowService


def make_inputs():
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

    return (
        draft,
        recipient_decision,
        attachment_result,
        security_assessment,
    )


def test_create_state():
    service = PreSendWorkflowService()

    (
        draft,
        recipient_decision,
        attachment_result,
        security_assessment,
    ) = make_inputs()

    state = service.create_state(
        workflow_id="workflow-001",
        draft=draft,
        recipient_decision=recipient_decision,
        attachment_result=attachment_result,
        security_assessment=security_assessment,
    )

    assert state.workflow_id == "workflow-001"
    assert state.status == EmailWorkflowStatus.DRAFT_CREATED
    assert state.draft == draft
    assert state.recipient_verification_decision == recipient_decision
    assert state.attachment_verification_result == attachment_result
    assert state.security_assessment == security_assessment


def test_validate_moves_valid_workflow_to_send_approval():
    service = PreSendWorkflowService()

    (
        draft,
        recipient_decision,
        attachment_result,
        security_assessment,
    ) = make_inputs()

    state = service.create_state(
        workflow_id="workflow-002",
        draft=draft,
        recipient_decision=recipient_decision,
        attachment_result=attachment_result,
        security_assessment=security_assessment,
    )

    validated_state = service.validate(state)

    assert validated_state.status == EmailWorkflowStatus.SEND_APPROVAL
    assert validated_state.blocked_reason is None


def test_request_send_approval():
    service = PreSendWorkflowService()

    (
        draft,
        recipient_decision,
        attachment_result,
        security_assessment,
    ) = make_inputs()

    state = service.create_state(
        workflow_id="workflow-003",
        draft=draft,
        recipient_decision=recipient_decision,
        attachment_result=attachment_result,
        security_assessment=security_assessment,
    )

    service.validate(state)

    request = service.request_send_approval(
        state=state,
        request_id="send-001",
        requested_by="user-001",
    )

    assert request.request_id == "send-001"
    assert request.requested_by == "user-001"
    assert state.send_approval_request == request
