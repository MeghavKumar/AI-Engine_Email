from datetime import datetime, timezone
from unittest.mock import Mock

from app.models.email_message import EmailMessageRecord
from app.schemas.research import ResearchSourceType
from app.services.mailbox_research import MailboxResearchService


def test_find_historical_evidence_returns_auditable_mailbox_evidence():
    repository = Mock()

    received_at = datetime(2026, 1, 15, 12, 30, tzinfo=timezone.utc)

    message = EmailMessageRecord(
        id=123,
        sender_email="alice@example.com",
        subject="Project discussion",
        received_at=received_at,
        body_text="SECRET_EMAIL_BODY with sensitive mailbox content.",
    )

    repository.find_by_recipient_email.return_value = [message]

    service = MailboxResearchService(repository)

    result = service.find_historical_evidence(
        account_id=42,
        recipient_email="john@example.com",
        limit=10,
    )

    assert len(result) == 1

    evidence = result[0]

    assert evidence.source_type == ResearchSourceType.MAILBOX
    assert evidence.source_reference == "message:123"
    assert "alice@example.com" in evidence.evidence
    assert "john@example.com" in evidence.evidence
    assert "Project discussion" in evidence.evidence
    assert "SECRET_EMAIL_BODY" not in evidence.evidence
    assert "sensitive mailbox content" not in evidence.evidence
    assert evidence.observed_at == received_at

    repository.find_by_recipient_email.assert_called_once_with(
        account_id=42,
        email="john@example.com",
        limit=10,
    )
