from pydantic import BaseModel, EmailStr, Field


class EmailDraft(BaseModel):
    to: list[EmailStr] = Field(min_length=1)
    cc: list[EmailStr] = []
    bcc: list[EmailStr] = []

    subject: str = Field(
        min_length=1,
        max_length=200,
    )

    body: str = Field(min_length=1)

    attachment_required: bool = False
    attachment_names: list[str] = []

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )


class EmailClassification(BaseModel):
    category: str
    priority: str
    requires_action: bool

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )


class SecurityAssessment(BaseModel):
    safe: bool
    pii_detected: bool = False
    prompt_injection_detected: bool = False
    reasons: list[str] = []
