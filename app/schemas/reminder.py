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
    status: ReminderStatus = ReminderStatus.DRAFT
