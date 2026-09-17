from app.providers.email.base import EmailProvider
from app.schemas.email import ApprovalStatus
from app.schemas.workflow import (
    EmailWorkflowState,
    EmailWorkflowStatus,
)


class EmailSendService:
    """Safely send an approved email through an email provider."""

    def __init__(self, provider: EmailProvider):
        self.provider = provider

    def send(
        self,
        state: EmailWorkflowState,
        account_id: str,
    ) -> str:
        """Send an email only after human approval."""

        self._validate_ready_state(state)

        if state.draft is None:
            raise ValueError(
                "Email draft is missing."
            )

        if state.send_approval_decision is None:
            raise ValueError(
                "Send approval decision is missing."
            )

        approved_recipients = (
            state.recipient_verification_decision
            .approved_recipients
        )

        if not approved_recipients:
            raise ValueError(
                "No approved recipients are available."
            )

        message = {
            "to": [
                recipient.email
                for recipient in approved_recipients
            ],
            "cc": [
                recipient
                for recipient in state.draft.cc
            ],
            "bcc": [
                recipient
                for recipient in state.draft.bcc
            ],
            "subject": state.draft.subject,
            "body": state.draft.body,
        }

        return self.provider.send_message(
            account_id=account_id,
            message=message,
        )

    def _validate_ready_state(
        self,
        state: EmailWorkflowState,
    ) -> None:
        """Ensure the workflow has explicit human send approval."""

        if state.status != EmailWorkflowStatus.READY_TO_SEND:
            raise ValueError(
                "Email workflow is not approved for sending."
            )

        if state.send_approval_decision is None:
            raise ValueError(
                "Send approval decision is missing."
            )

        if (
            state.send_approval_decision.status
            != ApprovalStatus.APPROVED
        ):
            raise ValueError(
                "Email send approval was not approved."
            )

        if state.recipient_verification_decision is None:
            raise ValueError(
                "Recipient verification decision is missing."
            )
