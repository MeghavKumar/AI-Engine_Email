from app.providers.email.base import EmailProvider
from app.schemas.email import ApprovalStatus
from app.schemas.workflow import EmailWorkflowState, EmailWorkflowStatus
from app.services.draft_integrity import draft_fingerprint
from app.services.subject_change_approval import SubjectChangeApprovalService


class EmailSendService:
    """Safely send an approved email through an email provider."""

    def __init__(self, provider: EmailProvider):
        self.provider = provider
        self.subject_approval = SubjectChangeApprovalService()

    def send(self, state: EmailWorkflowState, account_id: str) -> str:
        """Send only the exact draft and attachments approved by a human."""

        self._validate_ready_state(state)

        if state.draft is None:
            raise ValueError("Email draft is missing.")
        if state.send_approval_decision is None:
            raise ValueError("Send approval decision is missing.")

        if (
            state.approved_draft_fingerprint is None
            or state.approved_draft_fingerprint != draft_fingerprint(state)
        ):
            state.send_approval_request = None
            state.send_approval_decision = None
            state.approved_draft_fingerprint = None
            state.status = EmailWorkflowStatus.SEND_APPROVAL
            state.blocked_reason = (
                "Draft changed after approval; a new send approval is required."
            )
            if state.original_thread_subject is not None:
                state.subject_change_approval_request = None
                state.subject_change_approval_decision = None
                state.subject_change_approval_fingerprint = None
            raise ValueError(
                "Draft changed after approval; a new send approval is required."
            )

        if self.subject_approval.requires_approval(state):
            subject_decision = state.subject_change_approval_decision
            if (
                subject_decision is None
                or subject_decision.status != ApprovalStatus.APPROVED
                or state.subject_change_approval_fingerprint
                != draft_fingerprint(state)
            ):
                raise ValueError(
                    "Subject change requires explicit approval before sending."
                )

        if state.recipient_verification_decision is None:
            raise ValueError("Recipient verification decision is missing.")

        approved_recipients = (
            state.recipient_verification_decision.approved_recipients
        )
        if not approved_recipients:
            raise ValueError("No approved recipients are available.")

        message = {
            "to": [recipient.email for recipient in approved_recipients],
            "cc": list(state.draft.cc),
            "bcc": list(state.draft.bcc),
            "subject": state.draft.subject,
            "body": state.draft.body,
            "attachments": list(state.attachments),
        }
        return self.provider.send_message(account_id=account_id, message=message)

    def _validate_ready_state(self, state: EmailWorkflowState) -> None:
        """Ensure the workflow has explicit human send approval."""

        if state.status != EmailWorkflowStatus.READY_TO_SEND:
            raise ValueError("Email workflow is not approved for sending.")
        if state.send_approval_decision is None:
            raise ValueError("Send approval decision is missing.")
        if state.send_approval_decision.status != ApprovalStatus.APPROVED:
            raise ValueError("Email send approval was not approved.")
        if state.recipient_verification_decision is None:
            raise ValueError("Recipient verification decision is missing.")
