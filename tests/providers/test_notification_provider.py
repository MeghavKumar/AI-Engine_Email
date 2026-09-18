import pytest

from app.providers.notification.base import NotificationProvider
from app.schemas.notification import (
    Notification,
    NotificationType,
)


class FakeNotificationProvider(NotificationProvider):
    def __init__(self):
        self.notifications = []

    def send_notification(
        self,
        notification: Notification,
    ) -> str:
        self.notifications.append(notification)
        return "provider-notification-001"


def make_notification():
    return Notification(
        notification_id="notification-001",
        notification_type=NotificationType.NO_REPLY,
        user_id="user-001",
        subject="No reply received",
        message="No reply was received after 4 days.",
    )


def test_notification_provider_can_send_notification():
    provider = FakeNotificationProvider()
    notification = make_notification()

    provider_id = provider.send_notification(notification)

    assert provider_id == "provider-notification-001"
    assert len(provider.notifications) == 1
    assert provider.notifications[0] == notification


def test_notification_provider_requires_send_notification():
    class IncompleteProvider(NotificationProvider):
        pass

    with pytest.raises(TypeError):
        IncompleteProvider()
