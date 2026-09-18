import pytest

from app.schemas.follow_up import (
    FollowUpExecutionResult,
    FollowUpOutcome,
)
from app.schemas.notification import (
    NotificationStatus,
    NotificationType,
)
from app.services.notification import NotificationService


def test_create_no_reply_notification():
    result = FollowUpExecutionResult(
        job_id="job-001",
        outcome=FollowUpOutcome.NO_REPLY,
        notification_required=True,
        notification_reason="No reply received after 4 days.",
    )

    notification = NotificationService().create_no_reply_notification(
        result=result,
        user_id="user-001",
    )

    assert notification.notification_type == NotificationType.NO_REPLY
    assert notification.status == NotificationStatus.PENDING
    assert notification.user_id == "user-001"
    assert notification.subject == "No reply received"
    assert notification.message == "No reply received after 4 days."
    assert notification.notification_id


def test_create_no_reply_notification_uses_default_reason():
    result = FollowUpExecutionResult(
        job_id="job-002",
        outcome=FollowUpOutcome.NO_REPLY,
        notification_required=True,
    )

    notification = NotificationService().create_no_reply_notification(
        result=result,
        user_id="user-001",
    )

    assert (
        notification.message
        == "No reply was received after the follow-up period."
    )


def test_notification_rejected_when_reply_was_received():
    result = FollowUpExecutionResult(
        job_id="job-003",
        outcome=FollowUpOutcome.REPLY_RECEIVED,
        reply_message_id="reply-001",
    )

    with pytest.raises(
        ValueError,
        match="only be created for a NO_REPLY",
    ):
        NotificationService().create_no_reply_notification(
            result=result,
            user_id="user-001",
        )


def test_notification_rejected_when_not_required():
    result = FollowUpExecutionResult(
        job_id="job-004",
        outcome=FollowUpOutcome.NO_REPLY,
        notification_required=False,
    )

    with pytest.raises(
        ValueError,
        match="does not require notification",
    ):
        NotificationService().create_no_reply_notification(
            result=result,
            user_id="user-001",
        )


class FakeNotificationProvider:
    def __init__(self):
        self.notifications = []

    def send_notification(self, notification):
        self.notifications.append(notification)
        return "provider-notification-001"


def test_send_notification_marks_notification_sent():
    result = FollowUpExecutionResult(
        job_id="job-005",
        outcome=FollowUpOutcome.NO_REPLY,
        notification_required=True,
        notification_reason="No reply received after 4 days.",
    )

    service = NotificationService()
    notification = service.create_no_reply_notification(
        result=result,
        user_id="user-001",
    )

    provider = FakeNotificationProvider()

    provider_id = service.send(
        notification=notification,
        provider=provider,
    )

    assert provider_id == "provider-notification-001"
    assert notification.status == NotificationStatus.SENT
    assert len(provider.notifications) == 1
    assert provider.notifications[0] == notification


def test_send_notification_rejects_already_sent_notification():
    result = FollowUpExecutionResult(
        job_id="job-006",
        outcome=FollowUpOutcome.NO_REPLY,
        notification_required=True,
    )

    service = NotificationService()
    notification = service.create_no_reply_notification(
        result=result,
        user_id="user-001",
    )
    notification.status = NotificationStatus.SENT

    provider = FakeNotificationProvider()

    with pytest.raises(
        ValueError,
        match="Only pending notifications can be sent",
    ):
        service.send(
            notification=notification,
            provider=provider,
        )

    assert len(provider.notifications) == 0
