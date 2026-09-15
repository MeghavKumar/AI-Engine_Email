from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class EmailAddress(BaseModel):
    name: str | None = None
    email: EmailStr


class EmailMessage(BaseModel):
    provider: str
    account_id: str

    message_id: str
    thread_id: str | None = None

    sender: EmailAddress
    recipients: list[EmailAddress] = Field(default_factory=list)
    cc: list[EmailAddress] = Field(default_factory=list)

    subject: str = ""
    body_text: str = ""

    received_at: datetime | None = None

    is_read: bool = False
    has_attachments: bool = False

    labels: list[str] = Field(default_factory=list)
