import pytest
from pydantic import ValidationError

from app.schemas.research import (
    ResearchAssessment,
    ResearchEvidence,
    ResearchContact,
    ResearchResult,
    ResearchSourceType,
)


def test_research_evidence_requires_source_type():
    evidence = ResearchEvidence(
        source_type=ResearchSourceType.MAILBOX,
        source_reference="message:123",
        evidence="Recipient appeared in a previous email.",
    )

    assert evidence.source_type == ResearchSourceType.MAILBOX
    assert evidence.source_reference == "message:123"


def test_research_assessment_accepts_valid_confidence():
    assessment = ResearchAssessment(
        assessment="Historical evidence supports this recipient.",
        confidence=0.85,
    )

    assert assessment.confidence == 0.85


@pytest.mark.parametrize("confidence", [-0.1, 1.1])
def test_research_assessment_rejects_invalid_confidence(confidence):
    with pytest.raises(ValidationError):
        ResearchAssessment(
            assessment="Invalid confidence.",
            confidence=confidence,
        )


def test_research_result_keeps_evidence_and_assessment_separate():
    evidence = ResearchEvidence(
        source_type=ResearchSourceType.MAILBOX,
        source_reference="message:123",
        evidence="Recipient appeared in a previous email.",
    )
    assessment = ResearchAssessment(
        assessment="This is supporting historical evidence.",
        confidence=0.9,
    )

    result = ResearchResult(
        evidence=[evidence],
        assessment=assessment,
    )

    assert len(result.evidence) == 1
    assert result.evidence[0].source_type == ResearchSourceType.MAILBOX
    assert result.assessment is assessment


def test_research_contact_allows_missing_email():
    contact = ResearchContact(
        name="Jane Doe",
        role="Engineering Manager",
        organization="Example Corp",
        source_type=ResearchSourceType.COMPANY_WEBSITE,
        source_reference="https://example.com/team",
        reason="Public company profile identifies the person and role.",
        confidence=0.95,
    )

    assert contact.email is None
    assert contact.email_is_inferred is False


def test_research_contact_marks_inferred_email():
    contact = ResearchContact(
        name="Jane Doe",
        role="Engineering Manager",
        organization="Example Corp",
        email="jane.doe@example.com",
        email_is_inferred=True,
        source_type=ResearchSourceType.INFERENCE,
        source_reference="inference:example",
        reason="Address inferred from an observed company email convention.",
        confidence=0.6,
    )

    assert contact.email == "jane.doe@example.com"
    assert contact.email_is_inferred is True
    assert contact.source_type == ResearchSourceType.INFERENCE
