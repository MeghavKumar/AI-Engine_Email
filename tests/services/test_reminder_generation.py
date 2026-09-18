import pytest

from app.providers.ai.base import AIProvider
from app.schemas.reminder import ReminderDraft
from app.services.reminder_generation import ReminderGenerationService


class FakeAIProvider(AIProvider):
    def __init__(self, response: str):
        self.response = response
        self.last_prompt = None

    def generate(
        self,
        prompt: str,
        context: dict | None = None,
    ) -> str:
        self.last_prompt = prompt
        return self.response


def test_generate_valid_reminder():
    provider = FakeAIProvider(
        response="""{
            "to": ["recipient@example.com"],
            "cc": [],
            "subject": "Follow-up: Project update",
            "body": "Just following up on my previous email."
        }"""
    )

    service = ReminderGenerationService(provider)

    reminder = service.generate(
        original_subject="Project update",
        original_body="Please review the attached proposal.",
        recipient_email="recipient@example.com",
    )

    assert isinstance(reminder, ReminderDraft)
    assert reminder.to == ["recipient@example.com"]
    assert reminder.subject == "Follow-up: Project update"
    assert reminder.body == (
        "Just following up on my previous email."
    )


def test_generate_builds_prompt_with_email_context():
    provider = FakeAIProvider(
        response="""{
            "to": ["recipient@example.com"],
            "cc": [],
            "subject": "Follow-up",
            "body": "Following up."
        }"""
    )

    service = ReminderGenerationService(provider)

    service.generate(
        original_subject="Important project",
        original_body="Please review the proposal.",
        recipient_email="recipient@example.com",
    )

    assert "Important project" in provider.last_prompt
    assert "Please review the proposal." in provider.last_prompt
    assert "recipient@example.com" in provider.last_prompt


def test_invalid_json_is_rejected():
    provider = FakeAIProvider(
        response="This is not JSON."
    )

    service = ReminderGenerationService(provider)

    with pytest.raises(
        ValueError,
        match="not valid JSON",
    ):
        service.generate(
            original_subject="Project update",
            original_body="Please review.",
            recipient_email="recipient@example.com",
        )


def test_invalid_schema_is_rejected():
    provider = FakeAIProvider(
        response="""{
            "to": [],
            "cc": [],
            "subject": "Follow-up",
            "body": "Following up."
        }"""
    )

    service = ReminderGenerationService(provider)

    with pytest.raises(
        ValueError,
        match="failed schema validation",
    ):
        service.generate(
            original_subject="Project update",
            original_body="Please review.",
            recipient_email="recipient@example.com",
        )


def test_generated_reminder_can_be_checked_against_expected_recipient():
    provider = FakeAIProvider(
        response="""{
            "to": ["different@example.com"],
            "cc": [],
            "subject": "Follow-up",
            "body": "Following up."
        }"""
    )

    service = ReminderGenerationService(provider)

    reminder = service.generate(
        original_subject="Project update",
        original_body="Please review.",
        recipient_email="recipient@example.com",
    )

    assert reminder.to != ["recipient@example.com"]
