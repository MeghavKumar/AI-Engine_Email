from enum import Enum

from pydantic import BaseModel, Field

from app.schemas.email_attachment import EmailAttachment
from app.schemas.attachment import (
    AttachmentVerificationResult,
    AttachmentVerificationRequest,
)
from app.schemas.email import (
    ApprovalDecision,
    ApprovalRequest,
    EmailDraft,
    SecurityAssessment,
)
from app.schemas.recipient import (
    RecipientVerificationDecision,
    RecipientVerificationRequest,
)


class EmailWorkflowStatus(str, Enum):
    """Current status of the pre-send email workflow."""

    DRAFT_CREATED = "DRAFT_CREATED"
    RECIPIENT_VERIFICATION = "RECIPIENT_VERIFICATION"
    ATTACHMENT_VERIFICATION = "ATTACHMENT_VERIFICATION"
    SECURITY_CHECK = "SECURITY_CHECK"
    SEND_APPROVAL = "SEND_APPROVAL"
    READY_TO_SEND = "READY_TO_SEND"
    BLOCKED = "BLOCKED"


class EmailWorkflowState(BaseModel):
    """State carried through the email pre-send workflow."""

    workflow_id: str
    status: EmailWorkflowStatus

    draft: EmailDraft | None = None

    recipient_verification_request: (
        RecipientVerificationRequest | None
    ) = None

    recipient_verification_decision: (
        RecipientVerificationDecision | None
    ) = None

    attachment_verification_result: (
        AttachmentVerificationResult | None
    ) = None

    attachments: list[EmailAttachment] = Field(
        default_factory=list
    )

    attachment_action_request: (
        AttachmentVerificationRequest | None
    ) = None

    security_assessment: SecurityAssessment | None = None

    send_approval_request: ApprovalRequest | None = None

    send_approval_decision: ApprovalDecision | None = None

    blocked_reason: str | None = None
