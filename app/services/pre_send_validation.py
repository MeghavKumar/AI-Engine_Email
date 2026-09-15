from app.schemas.attachment import AttachmentVerificationStatus
from app.schemas.email import ApprovalStatus
from app.schemas.recipient import RecipientVerificationStatus
from app.schemas.workflow import (
    EmailWorkflowState,
    EmailWorkflowStatus,
)


class PreSendValidationService:
    """Validate all required gates before human send approval."""

    def validate(
        self,
        state: EmailWorkflowState,
    ) -> EmailWorkflowState:
        """Validate recipient, attachment, and security gates."""

        if state.draft is None:
            return self._block(
                state,
                "Email draft is missing.",
            )

        recipient_decision = state.recipient_verification_decision

        if recipient_decision is None:
            return self._block(
                state,
                "Recipient verification has not been completed.",
            )

        if (
            recipient_decision.status
            != RecipientVerificationStatus.APPROVED
        ):
            return self._block(
                state,
                "Recipient verification was not approved.",
            )

        attachment_result = state.attachment_verification_result

        if attachment_result is None:
            return self._block(
                state,
                "Attachment verification has not been completed.",
            )

        if attachment_result.status not in {
            AttachmentVerificationStatus.NOT_REQUIRED,
            AttachmentVerificationStatus.VERIFIED,
        }:
            return self._block(
                state,
                "Required attachments are missing.",
            )

        security_assessment = state.security_assessment

        if security_assessment is None:
            return self._block(
                state,
                "Security assessment has not been completed.",
            )

        if not security_assessment.safe:
            return self._block(
                state,
                "Security assessment did not approve the email.",
            )

        state.status = EmailWorkflowStatus.SEND_APPROVAL
        state.blocked_reason = None

        return state

    def _block(
        self,
        state: EmailWorkflowState,
        reason: str,
    ) -> EmailWorkflowState:
        """Mark the workflow as blocked."""

        state.status = EmailWorkflowStatus.BLOCKED
        state.blocked_reason = reason

        return state
