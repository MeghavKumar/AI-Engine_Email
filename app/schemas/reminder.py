from enum import Enum

from pydantic import BaseModel, EmailStr, Field


class ReminderStatus(str, Enum):
    DRAFT = "DRAFT"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class ReminderDraft(BaseModel):
    to: list[EmailStr] = Field(min_length=1)
    cc: list[EmailStr] = Field(default_factory=list)
    subject: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1)
    attachment_required: bool = False
    attachment_names: list[str] = Field(default_factory=list)
    status: ReminderStatus = ReminderStatus.DRAFT


class ReminderApprovalStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class ReminderApprovalRequest(BaseModel):
    request_id: str
    status: ReminderApprovalStatus = ReminderApprovalStatus.PENDING
    requested_by: str
    reason: str


class ReminderApprovalDecision(BaseModel):
    request_id: str
    status: ReminderApprovalStatus
    decided_by: str
    comment: str | None = None
