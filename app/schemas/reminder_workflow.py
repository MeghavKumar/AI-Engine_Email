from enum import Enum

from pydantic import BaseModel, Field

from app.schemas.attachment import (
    AttachmentVerificationRequest,
    AttachmentVerificationResult,
)
from app.schemas.email_attachment import EmailAttachment
from app.schemas.reminder import (
    ReminderApprovalDecision,
    ReminderApprovalRequest,
    ReminderDraft,
)
from app.schemas.email import SecurityAssessment


class ReminderWorkflowStatus(str, Enum):
    DRAFT_CREATED = "DRAFT_CREATED"
    SECURITY_CHECK = "SECURITY_CHECK"
    ATTACHMENT_VERIFICATION = "ATTACHMENT_VERIFICATION"
    APPROVAL = "APPROVAL"
    READY_TO_SEND = "READY_TO_SEND"
    BLOCKED = "BLOCKED"


class ReminderWorkflowState(BaseModel):
    workflow_id: str
    status: ReminderWorkflowStatus

    reminder: ReminderDraft | None = None

    security_assessment: SecurityAssessment | None = None

    attachment_verification_result: (
        AttachmentVerificationResult | None
    ) = None

    attachment_action_request: (
        AttachmentVerificationRequest | None
    ) = None

    attachments: list[EmailAttachment] = Field(
        default_factory=list
    )

    approval_request: ReminderApprovalRequest | None = None
    approval_decision: ReminderApprovalDecision | None = None

    blocked_reason: str | None = None
