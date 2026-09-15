from app.services.inbox import InboxService
from app.schemas.provider import EmailAddress, EmailMessage


class FakeEmailProvider:
    def list_messages(
        self,
        account_id: str,
        max_results: int = 25,
    ) -> list[dict]:
        return [
            {
                "id": "message-1",
                "threadId": "thread-1",
            }
        ]

    def get_message(
        self,
        account_id: str,
        message_id: str,
    ) -> dict:
        return {
            "id": message_id,
            "threadId": "thread-1",
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
            subject="Test message",
            body_text="Test body",
        )


def test_inbox_service_returns_normalized_messages():
    service = InboxService(FakeEmailProvider())

    messages = service.get_inbox(
        account_id="test-account",
        max_results=5,
    )

    assert len(messages) == 1
    assert isinstance(messages[0], EmailMessage)
    assert messages[0].message_id == "message-1"
    assert messages[0].subject == "Test message"
