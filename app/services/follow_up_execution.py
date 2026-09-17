from app.providers.email.base import EmailProvider
from app.schemas.follow_up import (
    FollowUpExecutionResult,
    FollowUpOutcome,
)
from app.services.reply_detection import ReplyDetectionService
from app.scheduler.schema import (
    ScheduledJob,
    ScheduledJobStatus,
)


class FollowUpExecutionService:
    """Execute a scheduled reply check."""

    def __init__(self, provider: EmailProvider):
        self.reply_detection = ReplyDetectionService(provider)

    def execute(
        self,
        job: ScheduledJob,
        account_id: str,
        account_email: str,
    ) -> FollowUpExecutionResult:
        if job.status != ScheduledJobStatus.SCHEDULED:
            raise ValueError(
                f"Job {job.id} is not scheduled for execution."
            )

        result = self.reply_detection.detect_reply(
            account_id=account_id,
            thread_id=job.email_thread_id,
            account_email=account_email,
        )

        job.status = ScheduledJobStatus.COMPLETED
        job.attempts += 1

        if result.replied:
            return FollowUpExecutionResult(
                job_id=job.id,
                outcome=FollowUpOutcome.REPLY_RECEIVED,
                reply_message_id=result.reply_message_id,
            )

        return FollowUpExecutionResult(
            job_id=job.id,
            outcome=FollowUpOutcome.NO_REPLY,
            notification_required=True,
            notification_reason=(
                "No reply received after follow-up period."
            ),
        )
