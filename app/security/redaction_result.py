from pydantic import BaseModel, Field

from app.schemas.email import SecurityAssessment


class RedactionResult(BaseModel):
    """Sanitized content and its corresponding security assessment."""

    redacted_text: str
    assessment: SecurityAssessment
    replacements: dict[str, str] = Field(default_factory=dict)
