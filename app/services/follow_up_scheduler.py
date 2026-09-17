from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.core.config import settings
from app.scheduler.schema import (
    ScheduledJob,
    ScheduledJobType,
)


class FollowUpScheduler:
    """Create scheduled jobs for post-send reply checks."""

    def schedule_reply_check(
        self,
        user_id: str,
        email_thread_id: str,
        sent_at: datetime | None = None,
    ) -> ScheduledJob:
        if sent_at is None:
            sent_at = datetime.now(timezone.utc)

        scheduled_for = (
            sent_at
            + timedelta(days=settings.follow_up_days)
        )

        return ScheduledJob(
            id=str(uuid4()),
            user_id=user_id,
            job_type=ScheduledJobType.FOLLOW_UP_CHECK,
            email_thread_id=email_thread_id,
            scheduled_for=scheduled_for,
            created_at=datetime.now(timezone.utc),
        )
