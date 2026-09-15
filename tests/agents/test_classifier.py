import pytest
from pydantic import ValidationError

from app.agents.classifier import EmailClassifier
from app.schemas.email import EmailCategory, EmailPriority
from app.schemas.provider import EmailAddress, EmailMessage


class FakeAIProvider:
    def __init__(self, response: str):
        self.response = response

    def generate(
        self,
        prompt: str,
        context: dict | None = None,
    ) -> str:
        return self.response


def make_test_message() -> EmailMessage:
    return EmailMessage(
        provider="fake",
        account_id="test-account",
        message_id="message-123",
        thread_id="thread-123",
        sender=EmailAddress(
            name="Test Sender",
            email="sender@example.com",
        ),
        subject="Please review this document",
        body_text="Could you review this document and respond by Friday?",
    )


def test_classifier_returns_valid_classification():
    ai_provider = FakeAIProvider(
        """
        {
            "category": "ACTION_REQUIRED",
            "priority": "HIGH",
            "requires_action": true,
            "confidence": 0.95
        }
        """
    )

    classifier = EmailClassifier(ai_provider)

    result = classifier.classify(make_test_message())

    assert result.category == EmailCategory.ACTION_REQUIRED
    assert result.priority == EmailPriority.HIGH
    assert result.requires_action is True
    assert result.confidence == 0.95


def test_classifier_rejects_invalid_category():
    ai_provider = FakeAIProvider(
        """
        {
            "category": "INVALID",
            "priority": "HIGH",
            "requires_action": true,
            "confidence": 0.95
        }
        """
    )

    classifier = EmailClassifier(ai_provider)

    with pytest.raises(ValidationError):
        classifier.classify(make_test_message())


def test_classifier_rejects_invalid_json():
    ai_provider = FakeAIProvider(
        "This is not JSON"
    )

    classifier = EmailClassifier(ai_provider)

    with pytest.raises(ValueError):
        classifier.classify(make_test_message())


def test_classifier_accepts_json_code_block():
    ai_provider = FakeAIProvider(
        """
        ```json
        {
            "category": "INFORMATIONAL",
            "priority": "LOW",
            "requires_action": false,
            "confidence": 0.88
        }
        ```
        """
    )

    classifier = EmailClassifier(ai_provider)

    result = classifier.classify(make_test_message())

    assert result.category == EmailCategory.INFORMATIONAL
    assert result.priority == EmailPriority.LOW
    assert result.requires_action is False
    assert result.confidence == 0.88
