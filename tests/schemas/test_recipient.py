import pytest
from pydantic import ValidationError

from app.schemas.recipient import (
    RecipientCandidate,
    RecipientDiscoveryResult,
)


def test_valid_recipient_candidate():
    candidate = RecipientCandidate(
        name="John Doe",
        email="john@example.com",
        source="user_context",
        confidence=0.95,
        reason="Recipient was explicitly identified by the user.",
    )

    assert candidate.name == "John Doe"
    assert candidate.email == "john@example.com"
    assert candidate.source == "user_context"
    assert candidate.confidence == 0.95


def test_invalid_recipient_email_is_rejected():
    with pytest.raises(ValidationError):
        RecipientCandidate(
            name="John Doe",
            email="not-an-email",
            source="user_context",
            confidence=0.95,
            reason="Invalid test recipient.",
        )


def test_confidence_must_be_between_zero_and_one():
    with pytest.raises(ValidationError):
        RecipientCandidate(
            name="John Doe",
            email="john@example.com",
            source="research",
            confidence=1.5,
            reason="Invalid confidence.",
        )


def test_discovery_result_requires_human_verification():
    result = RecipientDiscoveryResult()

    assert result.candidates == []
    assert result.requires_human_verification is True


def test_discovery_result_accepts_candidates():
    candidate = RecipientCandidate(
        name="Jane Doe",
        email="jane@example.com",
        source="research",
        confidence=0.82,
        reason="Found from approved research context.",
    )

    result = RecipientDiscoveryResult(
        candidates=[candidate]
    )

    assert len(result.candidates) == 1
    assert result.candidates[0].email == "jane@example.com"
    assert result.requires_human_verification is True


def test_recipient_verification_request_starts_pending():
    candidate = RecipientCandidate(
        name="John Doe",
        email="john@example.com",
        source="research",
        confidence=0.90,
        reason="Found from approved research context.",
    )

    from app.schemas.recipient import (
        RecipientVerificationRequest,
        RecipientVerificationStatus,
    )

    request = RecipientVerificationRequest(
        request_id="recipient-approval-123",
        recipients=[candidate],
        requested_by="user-123",
    )

    assert request.status == RecipientVerificationStatus.PENDING
    assert len(request.recipients) == 1


def test_recipient_verification_decision_can_approve():
    from app.schemas.recipient import (
        RecipientVerificationDecision,
        RecipientVerificationStatus,
    )

    candidate = RecipientCandidate(
        name="John Doe",
        email="john@example.com",
        source="user_context",
        confidence=0.99,
        reason="Explicitly provided by the user.",
    )

    decision = RecipientVerificationDecision(
        request_id="recipient-approval-123",
        status=RecipientVerificationStatus.APPROVED,
        decided_by="user-123",
        approved_recipients=[candidate],
        comment="Recipient verified.",
    )

    assert decision.status == RecipientVerificationStatus.APPROVED
    assert decision.decided_by == "user-123"
    assert len(decision.approved_recipients) == 1


def test_recipient_verification_decision_can_reject():
    from app.schemas.recipient import (
        RecipientVerificationDecision,
        RecipientVerificationStatus,
    )

    decision = RecipientVerificationDecision(
        request_id="recipient-approval-456",
        status=RecipientVerificationStatus.REJECTED,
        decided_by="user-123",
        comment="Wrong recipient.",
    )

    assert decision.status == RecipientVerificationStatus.REJECTED
    assert decision.approved_recipients == []
