from app.agents.classifier import EmailClassifier
from app.schemas.email import EmailCategory, EmailPriority
from app.schemas.provider import EmailAddress, EmailMessage
from app.services.inbox import InboxService
from app.services.inbox_processor import InboxProcessor
from app.services.triage import EmailTriageService


class FakeAIProvider:
    def generate(
        self,
        prompt: str,
        context: dict | None = None,
    ) -> str:
        return """
        {
            "category": "ACTION_REQUIRED",
            "priority": "HIGH",
            "requires_action": true,
            "confidence": 0.96
        }
        """


class FakeEmailProvider:
    def list_messages(
        self,
        account_id: str,
        max_results: int = 25,
    ) -> list[dict]:
        return [
            {
                "id": "message-123",
                "threadId": "thread-123",
            }
        ]

    def get_message(
        self,
        account_id: str,
        message_id: str,
    ) -> dict:
        return {
            "id": message_id,
            "threadId": "thread-123",
        }

    def normalize_message(
        self,
        account_id: str,
        raw_message: dict,
    ) -> EmailMessage:
        return EmailMessage(
            provider="fake",
            account_id=account_id,
            message_id=raw_message["id"],
            thread_id=raw_message["threadId"],
            sender=EmailAddress(
                name="Test Sender",
                email="sender@example.com",
            ),
            subject="Please review",
            body_text="Please review this document.",
        )


def test_inbox_processor_processes_email():
    inbox_service = InboxService(
        FakeEmailProvider()
    )

    classifier = EmailClassifier(
        FakeAIProvider()
    )

    processor = InboxProcessor(
        inbox_service=inbox_service,
        classifier=classifier,
        triage_service=EmailTriageService(),
    )

    results = processor.process(
        account_id="test-account",
        max_results=5,
    )

    assert len(results) == 1

    result = results[0]

    assert result.message.message_id == "message-123"

    assert (
        result.classification.category
        == EmailCategory.ACTION_REQUIRED
    )

    assert (
        result.classification.priority
        == EmailPriority.HIGH
    )

    assert result.classification.requires_action is True

    assert result.triage.action.value == "REVIEW"
