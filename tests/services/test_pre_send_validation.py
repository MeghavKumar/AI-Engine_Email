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
from app.services.pre_send_validation import (
    PreSendValidationService,
)


def make_draft() -> EmailDraft:
    return EmailDraft(
        to=["recipient@example.com"],
        subject="Project update",
        body="Here is the project update.",
        confidence=0.95,
    )


def make_approved_recipient_decision() -> RecipientVerificationDecision:
    recipient = RecipientCandidate(
        name="Recipient",
        email="recipient@example.com",
        source="known_context",
        confidence=0.95,
        reason="Recipient provided by the user.",
    )

    return RecipientVerificationDecision(
        request_id="recipient-001",
        status=RecipientVerificationStatus.APPROVED,
        decided_by="user-001",
        approved_recipients=[recipient],
    )


def make_verified_attachment_result() -> AttachmentVerificationResult:
    return AttachmentVerificationResult(
        status=AttachmentVerificationStatus.NOT_REQUIRED,
        required=False,
        reason="No attachment is required.",
    )


def make_safe_security_assessment() -> SecurityAssessment:
    return SecurityAssessment(
        safe=True,
        pii_detected=False,
        prompt_injection_detected=False,
        reasons=[],
    )


def make_ready_state() -> EmailWorkflowState:
    return EmailWorkflowState(
        workflow_id="workflow-001",
        status=EmailWorkflowStatus.DRAFT_CREATED,
        draft=make_draft(),
        recipient_verification_decision=(
            make_approved_recipient_decision()
        ),
        attachment_verification_result=(
            make_verified_attachment_result()
        ),
        security_assessment=make_safe_security_assessment(),
    )


def test_missing_draft_blocks_workflow():
    service = PreSendValidationService()

    state = EmailWorkflowState(
        workflow_id="workflow-001",
        status=EmailWorkflowStatus.DRAFT_CREATED,
    )

    result = service.validate(state)

    assert result.status == EmailWorkflowStatus.BLOCKED
    assert result.blocked_reason == "Email draft is missing."


def test_missing_recipient_verification_blocks_workflow():
    service = PreSendValidationService()

    state = make_ready_state()
    state.recipient_verification_decision = None

    result = service.validate(state)

    assert result.status == EmailWorkflowStatus.BLOCKED
    assert (
        result.blocked_reason
        == "Recipient verification has not been completed."
    )


def test_rejected_recipient_verification_blocks_workflow():
    service = PreSendValidationService()

    state = make_ready_state()
    state.recipient_verification_decision = (
        RecipientVerificationDecision(
            request_id="recipient-001",
            status=RecipientVerificationStatus.REJECTED,
            decided_by="user-001",
            approved_recipients=[],
        )
    )

    result = service.validate(state)

    assert result.status == EmailWorkflowStatus.BLOCKED
    assert (
        result.blocked_reason
        == "Recipient verification was not approved."
    )


def test_missing_attachment_verification_blocks_workflow():
    service = PreSendValidationService()

    state = make_ready_state()
    state.attachment_verification_result = None

    result = service.validate(state)

    assert result.status == EmailWorkflowStatus.BLOCKED
    assert (
        result.blocked_reason
        == "Attachment verification has not been completed."
    )


def test_missing_required_attachment_blocks_workflow():
    service = PreSendValidationService()

    state = make_ready_state()
    state.attachment_verification_result = (
        AttachmentVerificationResult(
            status=AttachmentVerificationStatus.MISSING,
            required=True,
            attachment_names=["report.pdf"],
            missing_attachments=["report.pdf"],
            reason="Required attachment is missing.",
        )
    )

    result = service.validate(state)

    assert result.status == EmailWorkflowStatus.BLOCKED
    assert (
        result.blocked_reason
        == "Required attachments are missing."
    )


def test_missing_security_assessment_blocks_workflow():
    service = PreSendValidationService()

    state = make_ready_state()
    state.security_assessment = None

    result = service.validate(state)

    assert result.status == EmailWorkflowStatus.BLOCKED
    assert (
        result.blocked_reason
        == "Security assessment has not been completed."
    )


def test_failed_security_assessment_blocks_workflow():
    service = PreSendValidationService()

    state = make_ready_state()
    state.security_assessment = SecurityAssessment(
        safe=False,
        pii_detected=True,
        prompt_injection_detected=False,
        reasons=["Sensitive information detected."],
    )

    result = service.validate(state)

    assert result.status == EmailWorkflowStatus.BLOCKED
    assert (
        result.blocked_reason
        == "Security assessment did not approve the email."
    )


def test_all_pre_send_gates_pass():
    service = PreSendValidationService()

    state = make_ready_state()

    result = service.validate(state)

    assert result.status == EmailWorkflowStatus.SEND_APPROVAL
    assert result.blocked_reason is None
