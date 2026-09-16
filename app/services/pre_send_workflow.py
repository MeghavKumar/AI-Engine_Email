from app.schemas.attachment import AttachmentVerificationResult
from app.schemas.email import EmailDraft, SecurityAssessment
from app.schemas.recipient import (
    RecipientVerificationDecision,
)
from app.schemas.workflow import (
    EmailWorkflowState,
    EmailWorkflowStatus,
)
from app.services.pre_send_validation import PreSendValidationService
from app.services.send_approval import SendApprovalService


class PreSendWorkflowService:
    """Orchestrate the email pre-send workflow."""

    def __init__(
        self,
        validation_service: PreSendValidationService | None = None,
        send_approval_service: SendApprovalService | None = None,
    ):
        self.validation_service = (
            validation_service or PreSendValidationService()
        )
        self.send_approval_service = (
            send_approval_service or SendApprovalService()
        )

    def create_state(
        self,
        workflow_id: str,
        draft: EmailDraft,
        recipient_decision: RecipientVerificationDecision,
        attachment_result: AttachmentVerificationResult,
        security_assessment: SecurityAssessment,
    ) -> EmailWorkflowState:
        """Create the initial pre-send workflow state."""

        return EmailWorkflowState(
            workflow_id=workflow_id,
            status=EmailWorkflowStatus.DRAFT_CREATED,
            draft=draft,
            recipient_verification_decision=recipient_decision,
            attachment_verification_result=attachment_result,
            security_assessment=security_assessment,
        )

    def validate(
        self,
        state: EmailWorkflowState,
    ) -> EmailWorkflowState:
        """Run all pre-send validation gates."""

        return self.validation_service.validate(state)

    def request_send_approval(
        self,
        state: EmailWorkflowState,
        request_id: str,
        requested_by: str,
    ):
        """Create human approval after validation succeeds."""

        return self.send_approval_service.create_request(
            state=state,
            request_id=request_id,
            requested_by=requested_by,
        )
