from enum import Enum

from pydantic import BaseModel, EmailStr, Field


class EmailCategory(str, Enum):
    SPAM = "SPAM"
    PROMOTION = "PROMOTION"
    ACTION_REQUIRED = "ACTION_REQUIRED"
    INFORMATIONAL = "INFORMATIONAL"


class EmailPriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"


class EmailDraft(BaseModel):
    to: list[EmailStr] = Field(min_length=1)
    cc: list[EmailStr] = Field(default_factory=list)
    bcc: list[EmailStr] = Field(default_factory=list)
    subject: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1)
    attachment_required: bool = False
    attachment_names: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)


class EmailClassification(BaseModel):
    category: EmailCategory
    priority: EmailPriority
    requires_action: bool
    confidence: float = Field(ge=0.0, le=1.0)


class SecurityAssessment(BaseModel):
    safe: bool
    pii_detected: bool = False
    prompt_injection_detected: bool = False
    reasons: list[str] = Field(default_factory=list)


class TriageAction(str, Enum):
    NO_ACTION = "NO_ACTION"
    ARCHIVE = "ARCHIVE"
    REVIEW = "REVIEW"


class TriageDecision(BaseModel):
    action: TriageAction
    reason: str


class ApprovalStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class ApprovalRequest(BaseModel):
    request_id: str
    status: ApprovalStatus = ApprovalStatus.PENDING
    requested_by: str
    reason: str


class ApprovalDecision(BaseModel):
    request_id: str
    status: ApprovalStatus
    decided_by: str
    comment: str | None = None
