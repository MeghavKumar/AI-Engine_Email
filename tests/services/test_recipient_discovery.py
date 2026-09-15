from app.schemas.recipient import RecipientCandidate
from app.services.recipient_discovery import RecipientDiscoveryService


def test_discovery_returns_empty_result_when_no_candidates_exist():
    service = RecipientDiscoveryService()

    result = service.discover()

    assert result.candidates == []
    assert result.requires_human_verification is True


def test_discovery_returns_candidate_recipients():
    service = RecipientDiscoveryService()

    candidate = RecipientCandidate(
        name="John Doe",
        email="john@example.com",
        source="user_context",
        confidence=0.95,
        reason="Recipient was explicitly identified by the user.",
    )

    result = service.discover(
        candidates=[candidate]
    )

    assert len(result.candidates) == 1
    assert result.candidates[0].name == "John Doe"
    assert result.candidates[0].email == "john@example.com"
    assert result.candidates[0].confidence == 0.95


def test_discovery_always_requires_human_verification():
    service = RecipientDiscoveryService()

    candidate = RecipientCandidate(
        name="Jane Doe",
        email="jane@example.com",
        source="research",
        confidence=0.99,
        reason="Recipient discovered from research context.",
    )

    result = service.discover(
        candidates=[candidate]
    )

    assert result.requires_human_verification is True
