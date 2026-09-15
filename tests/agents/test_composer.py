import pytest
from pydantic import ValidationError

from app.agents.composer import EmailComposer
from app.schemas.email import EmailDraft


class FakeAIProvider:
    def __init__(self, response: str):
        self.response = response

    def generate(
        self,
        prompt: str,
        context: dict | None = None,
    ) -> str:
        return self.response


def test_composer_returns_valid_email_draft():
    ai_provider = FakeAIProvider(
        """
        {
            "to": ["recipient@example.com"],
            "cc": [],
            "bcc": [],
            "subject": "Project update",
            "body": "Here is the requested project update.",
            "attachment_required": false,
            "attachment_names": [],
            "confidence": 0.94
        }
        """
    )

    composer = EmailComposer(ai_provider)

    result = composer.compose(
        prompt="Send the recipient a project update."
    )

    assert isinstance(result, EmailDraft)
    assert result.to == ["recipient@example.com"]
    assert result.subject == "Project update"
    assert result.body
    assert result.attachment_required is False
    assert result.confidence == 0.94


def test_composer_rejects_invalid_recipient():
    ai_provider = FakeAIProvider(
        """
        {
            "to": ["not-an-email"],
            "cc": [],
            "bcc": [],
            "subject": "Test",
            "body": "Test body",
            "attachment_required": false,
            "attachment_names": [],
            "confidence": 0.90
        }
        """
    )

    composer = EmailComposer(ai_provider)

    with pytest.raises(ValidationError):
        composer.compose(
            prompt="Send a test email."
        )


def test_composer_rejects_invalid_json():
    ai_provider = FakeAIProvider(
        "This is not JSON"
    )

    composer = EmailComposer(ai_provider)

    with pytest.raises(ValueError):
        composer.compose(
            prompt="Send a test email."
        )


def test_composer_accepts_json_code_block():
    ai_provider = FakeAIProvider(
        """
        ```json
        {
            "to": ["recipient@example.com"],
            "cc": [],
            "bcc": [],
            "subject": "Meeting follow-up",
            "body": "Thank you for the meeting.",
            "attachment_required": false,
            "attachment_names": [],
            "confidence": 0.91
        }
        ```
        """
    )

    composer = EmailComposer(ai_provider)

    result = composer.compose(
        prompt="Write a meeting follow-up."
    )

    assert result.subject == "Meeting follow-up"
    assert result.body == "Thank you for the meeting."
    assert result.confidence == 0.91
