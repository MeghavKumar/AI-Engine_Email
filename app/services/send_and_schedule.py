from datetime import datetime

from app.providers.email.base import EmailProvider
from app.scheduler.schema import ScheduledJob
from app.services.email_send import EmailSendService
from app.services.follow_up_scheduler import FollowUpScheduler


class SendAndScheduleService:
    """Send an approved email and schedule its follow-up check."""

    def __init__(
        self,
        provider: EmailProvider,
        follow_up_scheduler: FollowUpScheduler | None = None,
    ):
        self.email_send = EmailSendService(provider)
        self.provider = provider
        self.follow_up_scheduler = (
            follow_up_scheduler or FollowUpScheduler()
        )

    def send_and_schedule(
        self,
        state,
        account_id: str,
        user_id: str,
        sent_at: datetime | None = None,
    ) -> tuple[str, ScheduledJob]:
        """Send an approved email and schedule a reply check."""

        message_id = self.email_send.send(
            state=state,
            account_id=account_id,
        )

        sent_message = self.provider.get_message(
            account_id=account_id,
            message_id=message_id,
        )

        thread_id = sent_message.get("threadId")

        if not thread_id:
            raise ValueError(
                "Sent message does not contain a thread ID."
            )

        job = self.follow_up_scheduler.schedule_reply_check(
            user_id=user_id,
            email_thread_id=thread_id,
            sent_at=sent_at,
        )

        return message_id, job
