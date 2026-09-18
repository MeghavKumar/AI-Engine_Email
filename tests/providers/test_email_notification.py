from app.providers.email.base import EmailProvider
from app.providers.notification.email import EmailNotificationProvider
from app.schemas.notification import (
    Notification,
    NotificationType,
)


class FakeEmailProvider(EmailProvider):
    def __init__(self):
        self.sent_messages = []

    def list_messages(self, account_id, max_results=25):
        return []

    def get_message(self, account_id, message_id):
        return {}

    def send_message(self, account_id, message):
        self.sent_messages.append(
            {
                "account_id": account_id,
                "message": message,
            }
        )
        return "email-message-001"

    def mark_read(self, account_id, message_id):
        raise NotImplementedError

    def archive_message(self, account_id, message_id):
        raise NotImplementedError

    def get_thread(self, account_id, thread_id):
        return []


def test_email_notification_provider_sends_notification():
    email_provider = FakeEmailProvider()

    provider = EmailNotificationProvider(
        email_provider=email_provider,
        account_id="account-001",
        recipient_email="human@example.com",
    )

    notification = Notification(
        notification_id="notification-001",
        notification_type=NotificationType.NO_REPLY,
        user_id="user-001",
        subject="No reply received",
        message="No reply was received after 4 days.",
    )

    provider_id = provider.send_notification(notification)

    assert provider_id == "email-message-001"
    assert len(email_provider.sent_messages) == 1

    sent = email_provider.sent_messages[0]

    assert sent["account_id"] == "account-001"
    assert sent["message"]["to"] == ["human@example.com"]
    assert sent["message"]["subject"] == "No reply received"
    assert sent["message"]["body"] == (
        "No reply was received after 4 days."
    )


def test_email_notification_provider_uses_configured_recipient():
    email_provider = FakeEmailProvider()

    provider = EmailNotificationProvider(
        email_provider=email_provider,
        account_id="account-002",
        recipient_email="notifications@example.com",
    )

    notification = Notification(
        notification_id="notification-002",
        notification_type=NotificationType.NO_REPLY,
        user_id="user-002",
        subject="Follow-up required",
        message="Please review the pending follow-up.",
    )

    provider.send_notification(notification)

    sent = email_provider.sent_messages[0]

    assert sent["message"]["to"] == ["notifications@example.com"]
