from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class ResearchSourceType(str, Enum):
    MAILBOX = "MAILBOX"
    WEB = "WEB"
    COMPANY_WEBSITE = "COMPANY_WEBSITE"
    PROFESSIONAL_PROFILE = "PROFESSIONAL_PROFILE"
    INFERENCE = "INFERENCE"


class ResearchEvidence(BaseModel):
    """Auditable evidence gathered during research."""

    source_type: ResearchSourceType
    source_reference: str
    evidence: str
    observed_at: datetime | None = None


class ResearchAssessment(BaseModel):
    """AI assessment derived from research evidence."""

    assessment: str
    confidence: float = Field(ge=0.0, le=1.0)


class ResearchResult(BaseModel):
    """Structured research result kept separate from AI assessment."""

    evidence: list[ResearchEvidence] = Field(default_factory=list)
    assessment: ResearchAssessment | None = None
