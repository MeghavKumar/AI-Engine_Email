from app.schemas.follow_up import (
    FollowUpExecutionResult,
    FollowUpOutcome,
)
from app.schemas.notification import (
    NotificationStatus,
    NotificationType,
)
from app.services.follow_up_notification import FollowUpNotificationService


def test_create_notification_for_no_reply():
    result = FollowUpExecutionResult(
        job_id="job-001",
        outcome=FollowUpOutcome.NO_REPLY,
        notification_required=True,
        notification_reason="No reply received after 4 days.",
    )

    notification = FollowUpNotificationService().create_notification(
        result=result,
        user_id="user-001",
    )

    assert notification is not None
    assert notification.notification_type == NotificationType.NO_REPLY
    assert notification.status == NotificationStatus.PENDING
    assert notification.user_id == "user-001"
    assert notification.message == "No reply received after 4 days."


def test_no_notification_when_reply_received():
    result = FollowUpExecutionResult(
        job_id="job-002",
        outcome=FollowUpOutcome.REPLY_RECEIVED,
        reply_message_id="reply-001",
        notification_required=False,
    )

    notification = FollowUpNotificationService().create_notification(
        result=result,
        user_id="user-001",
    )

    assert notification is None


def test_no_notification_when_not_required():
    result = FollowUpExecutionResult(
        job_id="job-003",
        outcome=FollowUpOutcome.NO_REPLY,
        notification_required=False,
    )

    notification = FollowUpNotificationService().create_notification(
        result=result,
        user_id="user-001",
    )

    assert notification is None


class FakeEmailProvider:
    def __init__(self):
        self.sent_messages = []

    def send_message(self, account_id, message):
        self.sent_messages.append(
            {
                "account_id": account_id,
                "message": message,
            }
        )
        return "email-message-001"


def test_no_reply_notification_can_be_delivered_by_email():
    from app.providers.notification.email import EmailNotificationProvider
    from app.services.notification import NotificationService

    result = FollowUpExecutionResult(
        job_id="job-004",
        outcome=FollowUpOutcome.NO_REPLY,
        notification_required=True,
        notification_reason="No reply received after 4 days.",
    )

    notification_service = FollowUpNotificationService()

    notification = notification_service.create_notification(
        result=result,
        user_id="user-001",
    )

    assert notification is not None

    email_provider = FakeEmailProvider()

    notification_provider = EmailNotificationProvider(
        email_provider=email_provider,
        account_id="account-001",
        recipient_email="human@example.com",
    )

    delivery_service = NotificationService()

    provider_id = delivery_service.send(
        notification=notification,
        provider=notification_provider,
    )

    assert provider_id == "email-message-001"
    assert notification.status == NotificationStatus.SENT

    assert len(email_provider.sent_messages) == 1

    sent_message = email_provider.sent_messages[0]

    assert sent_message["account_id"] == "account-001"
    assert sent_message["message"]["to"] == ["human@example.com"]
    assert sent_message["message"]["subject"] == "No reply received"
    assert sent_message["message"]["body"] == (
        "No reply received after 4 days."
    )
