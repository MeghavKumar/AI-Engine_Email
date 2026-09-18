from uuid import uuid4

from app.providers.notification.base import NotificationProvider
from app.schemas.follow_up import FollowUpExecutionResult, FollowUpOutcome
from app.schemas.notification import (
    Notification,
    NotificationStatus,
    NotificationType,
)


class NotificationService:
    """Create and deliver human notifications."""

    def create_no_reply_notification(
        self,
        result: FollowUpExecutionResult,
        user_id: str,
    ) -> Notification:
        if result.outcome != FollowUpOutcome.NO_REPLY:
            raise ValueError(
                "A no-reply notification can only be created "
                "for a NO_REPLY follow-up result."
            )

        if not result.notification_required:
            raise ValueError(
                "Follow-up result does not require notification."
            )

        return Notification(
            notification_id=str(uuid4()),
            notification_type=NotificationType.NO_REPLY,
            user_id=user_id,
            subject="No reply received",
            message=(
                result.notification_reason
                or "No reply was received after the follow-up period."
            ),
        )

    def send(
        self,
        notification: Notification,
        provider: NotificationProvider,
    ) -> str:
        """Deliver a pending notification through a provider."""

        if notification.status != NotificationStatus.PENDING:
            raise ValueError(
                "Only pending notifications can be sent."
            )

        provider_id = provider.send_notification(notification)

        notification.status = NotificationStatus.SENT

        return provider_id
