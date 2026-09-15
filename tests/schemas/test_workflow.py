from app.schemas.attachment import (
    AttachmentVerificationResult,
    AttachmentVerificationStatus,
)
from app.schemas.email import (
    ApprovalRequest,
    ApprovalStatus,
    EmailDraft,
    SecurityAssessment,
)
from app.schemas.recipient import (
    RecipientCandidate,
    RecipientVerificationRequest,
)
from app.schemas.workflow import (
    EmailWorkflowState,
    EmailWorkflowStatus,
)


def test_workflow_state_can_hold_email_draft():
    draft = EmailDraft(
        to=["recipient@example.com"],
        subject="Project update",
        body="Here is the latest project update.",
        confidence=0.95,
    )

    state = EmailWorkflowState(
        workflow_id="workflow-001",
        status=EmailWorkflowStatus.DRAFT_CREATED,
        draft=draft,
    )

    assert state.workflow_id == "workflow-001"
    assert state.status == EmailWorkflowStatus.DRAFT_CREATED
    assert state.draft == draft


def test_workflow_state_can_hold_recipient_verification():
    recipient = RecipientCandidate(
        name="John Doe",
        email="john@example.com",
        source="known_context",
        confidence=0.90,
        reason="Recipient identified from the request.",
    )

    request = RecipientVerificationRequest(
        request_id="recipient-001",
        recipients=[recipient],
        requested_by="user-001",
    )

    state = EmailWorkflowState(
        workflow_id="workflow-002",
        status=EmailWorkflowStatus.RECIPIENT_VERIFICATION,
        recipient_verification_request=request,
    )

    assert state.status == EmailWorkflowStatus.RECIPIENT_VERIFICATION
    assert state.recipient_verification_request == request


def test_workflow_state_can_hold_attachment_verification():
    result = AttachmentVerificationResult(
        status=AttachmentVerificationStatus.VERIFIED,
        required=True,
        attachment_names=["report.pdf"],
        reason="Required attachment is present.",
    )

    state = EmailWorkflowState(
        workflow_id="workflow-003",
        status=EmailWorkflowStatus.ATTACHMENT_VERIFICATION,
        attachment_verification_result=result,
    )

    assert state.status == EmailWorkflowStatus.ATTACHMENT_VERIFICATION
    assert state.attachment_verification_result == result


def test_workflow_state_can_hold_security_and_send_approval():
    security = SecurityAssessment(
        safe=True,
        pii_detected=False,
        prompt_injection_detected=False,
        reasons=[],
    )

    approval = ApprovalRequest(
        request_id="send-001",
        requested_by="user-001",
        reason="Email is ready for human send approval.",
    )

    state = EmailWorkflowState(
        workflow_id="workflow-004",
        status=EmailWorkflowStatus.SEND_APPROVAL,
        security_assessment=security,
        send_approval_request=approval,
    )

    assert state.status == EmailWorkflowStatus.SEND_APPROVAL
    assert state.security_assessment == security
    assert state.send_approval_request == approval


def test_workflow_state_defaults_to_no_optional_components():
    state = EmailWorkflowState(
        workflow_id="workflow-005",
        status=EmailWorkflowStatus.DRAFT_CREATED,
    )

    assert state.draft is None
    assert state.recipient_verification_request is None
    assert state.recipient_verification_decision is None
    assert state.attachment_verification_result is None
    assert state.attachment_action_request is None
    assert state.security_assessment is None
    assert state.send_approval_request is None
    assert state.send_approval_decision is None
    assert state.blocked_reason is None
