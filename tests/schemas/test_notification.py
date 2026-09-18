from app.schemas.notification import (
    Notification,
    NotificationStatus,
    NotificationType,
)


def test_no_reply_notification_defaults_to_pending():
    notification = Notification(
        notification_id="notification-001",
        notification_type=NotificationType.NO_REPLY,
        user_id="user-001",
        subject="No reply received",
        message="No reply was received after the follow-up period.",
    )

    assert notification.notification_type == NotificationType.NO_REPLY
    assert notification.status == NotificationStatus.PENDING
    assert notification.user_id == "user-001"


def test_notification_can_be_marked_sent():
    notification = Notification(
        notification_id="notification-002",
        notification_type=NotificationType.NO_REPLY,
        status=NotificationStatus.SENT,
        user_id="user-001",
        subject="No reply received",
        message="Please review the follow-up.",
    )

    assert notification.status == NotificationStatus.SENT
