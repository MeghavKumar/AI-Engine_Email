from app.schemas.recipient import RecipientCandidate
from app.schemas.research import ResearchContact, ResearchSourceType
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


def test_discover_historical_candidate_creates_candidate_from_evidence():
    from unittest.mock import Mock

    from app.schemas.research import ResearchEvidence, ResearchSourceType

    mailbox_research = Mock()
    mailbox_research.find_historical_evidence.return_value = [
        ResearchEvidence(
            source_type=ResearchSourceType.MAILBOX,
            source_reference="message:123",
            evidence="Historical communication with john@example.com.",
        ),
        ResearchEvidence(
            source_type=ResearchSourceType.MAILBOX,
            source_reference="message:456",
            evidence="Another historical communication.",
        ),
    ]

    service = RecipientDiscoveryService(
        mailbox_research=mailbox_research,
    )

    result = service.discover_historical_candidate(
        account_id=42,
        email="john@example.com",
        name="John Doe",
        limit=10,
    )

    assert len(result.candidates) == 1

    candidate = result.candidates[0]

    assert candidate.name == "John Doe"
    assert candidate.email == "john@example.com"
    assert candidate.source == "historical_mailbox"
    assert candidate.confidence == 1.0
    assert "2 message(s)" in candidate.reason
    assert "does not constitute recipient authorization" in candidate.reason
    assert result.requires_human_verification is True

    mailbox_research.find_historical_evidence.assert_called_once_with(
        account_id=42,
        recipient_email="john@example.com",
        limit=10,
    )


def test_discover_historical_candidate_returns_empty_when_no_evidence():
    from unittest.mock import Mock

    mailbox_research = Mock()
    mailbox_research.find_historical_evidence.return_value = []

    service = RecipientDiscoveryService(
        mailbox_research=mailbox_research,
    )

    result = service.discover_historical_candidate(
        account_id=42,
        email="john@example.com",
    )

    assert result.candidates == []
    assert result.requires_human_verification is True


def test_discover_historical_candidate_requires_mailbox_research_service():
    service = RecipientDiscoveryService()

    import pytest

    with pytest.raises(
        ValueError,
        match="MailboxResearchService is required",
    ):
        service.discover_historical_candidate(
            account_id=42,
            email="john@example.com",
        )


def test_discover_researched_candidate_requires_email():
    service = RecipientDiscoveryService()

    contact = ResearchContact(
        name="Jane Doe",
        role="Engineering Manager",
        organization="Example Corp",
        source_type=ResearchSourceType.COMPANY_WEBSITE,
        source_reference="company:example",
        reason="Public company profile identifies the person.",
        confidence=0.95,
    )

    result = service.discover_researched_candidate(contact)

    assert result.candidates == []
    assert result.requires_human_verification is True


def test_discover_researched_candidate_from_public_research():
    service = RecipientDiscoveryService()

    contact = ResearchContact(
        name="Jane Doe",
        role="Engineering Manager",
        organization="Example Corp",
        email="jane.doe@example.com",
        source_type=ResearchSourceType.COMPANY_WEBSITE,
        source_reference="company:example",
        reason="Public company profile lists this email address.",
        confidence=0.95,
    )

    result = service.discover_researched_candidate(contact)

    assert len(result.candidates) == 1
    candidate = result.candidates[0]
    assert candidate.email == "jane.doe@example.com"
    assert candidate.source == "company_website"
    assert candidate.confidence == 0.95
    assert result.requires_human_verification is True
    assert "human verification is required" in candidate.reason


def test_discover_researched_candidate_marks_inferred_email():
    service = RecipientDiscoveryService()

    contact = ResearchContact(
        name="Jane Doe",
        organization="Example Corp",
        email="jane.doe@example.com",
        email_is_inferred=True,
        source_type=ResearchSourceType.INFERENCE,
        source_reference="inference:example",
        reason="Email address inferred from an observed company convention.",
        confidence=0.6,
    )

    result = service.discover_researched_candidate(contact)

    assert len(result.candidates) == 1
    candidate = result.candidates[0]
    assert candidate.email == "jane.doe@example.com"
    assert candidate.source == "inference"
    assert result.requires_human_verification is True
