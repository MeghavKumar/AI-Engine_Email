from enum import Enum

from pydantic import BaseModel, EmailStr, Field


class RecipientCandidate(BaseModel):
    """A possible email recipient discovered by the engine."""

    name: str | None = None
    email: EmailStr
    source: str
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str


class RecipientDiscoveryResult(BaseModel):
    """Results returned by recipient discovery."""

    candidates: list[RecipientCandidate] = Field(
        default_factory=list
    )
    requires_human_verification: bool = True


class RecipientVerificationStatus(str, Enum):
    """Status of recipient verification."""

    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class RecipientVerificationRequest(BaseModel):
    """Human verification request for a recipient list."""

    request_id: str
    recipients: list[RecipientCandidate] = Field(min_length=1)
    status: RecipientVerificationStatus = (
        RecipientVerificationStatus.PENDING
    )
    requested_by: str


class RecipientVerificationDecision(BaseModel):
    """Human decision on a recipient verification request."""

    request_id: str
    status: RecipientVerificationStatus
    decided_by: str
    approved_recipients: list[RecipientCandidate] = Field(
        default_factory=list
    )
    comment: str | None = None
