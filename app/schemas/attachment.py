from enum import Enum

from pydantic import BaseModel, Field


class AttachmentVerificationStatus(str, Enum):
    """Status of attachment verification."""

    NOT_REQUIRED = "NOT_REQUIRED"
    VERIFIED = "VERIFIED"
    MISSING = "MISSING"


class AttachmentVerificationResult(BaseModel):
    """Result of checking required email attachments."""

    status: AttachmentVerificationStatus
    required: bool
    attachment_names: list[str] = Field(
        default_factory=list
    )
    missing_attachments: list[str] = Field(
        default_factory=list
    )
    reason: str


class AttachmentVerificationRequest(BaseModel):
    """Human review request for a missing required attachment."""

    request_id: str
    attachment_names: list[str] = Field(min_length=1)
    status: AttachmentVerificationStatus = (
        AttachmentVerificationStatus.MISSING
    )
    requires_human_action: bool = True
