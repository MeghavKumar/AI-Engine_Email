from app.schemas.follow_up import FollowUpExecutionResult, FollowUpOutcome
from app.schemas.notification import Notification
from app.services.notification import NotificationService


class FollowUpNotificationService:
    """Create notifications when a follow-up check finds no reply."""

    def __init__(
        self,
        notification_service: NotificationService | None = None,
    ):
        self.notification_service = (
            notification_service or NotificationService()
        )

    def create_notification(
        self,
        result: FollowUpExecutionResult,
        user_id: str,
    ) -> Notification | None:
        if result.outcome != FollowUpOutcome.NO_REPLY:
            return None

        if not result.notification_required:
            return None

        return self.notification_service.create_no_reply_notification(
            result=result,
            user_id=user_id,
        )
