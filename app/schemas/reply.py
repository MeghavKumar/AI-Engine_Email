from pydantic import BaseModel, EmailStr, Field


class ReplyDetectionResult(BaseModel):
    """Result of checking an email thread for an inbound reply."""

    replied: bool
    reply_message_id: str | None = None
    reply_from: EmailStr | None = None
    reply_to: list[EmailStr] = Field(default_factory=list)
    reply_cc: list[EmailStr] = Field(default_factory=list)
    suggested_reply_to: list[EmailStr] = Field(default_factory=list)
    suggested_reply_cc: list[EmailStr] = Field(default_factory=list)
    requires_recipient_confirmation: bool = True
