import pytest
from pydantic import ValidationError

from app.schemas.research import (
    ResearchAssessment,
    ResearchEvidence,
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
