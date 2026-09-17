from datetime import datetime, timezone

import pytest

from app.scheduler.schema import (
    ScheduledJob,
    ScheduledJobStatus,
    ScheduledJobType,
)
from app.schemas.follow_up import FollowUpOutcome
from app.services.follow_up_execution import FollowUpExecutionService


ACCOUNT_EMAIL = "meghav27071982@gmail.com"


class FakeEmailProvider:
    def __init__(self, messages):
        self.messages = messages

    def get_thread(self, account_id, thread_id):
        return self.messages


def make_job():
    now = datetime.now(timezone.utc)

    return ScheduledJob(
        id="job-123",
        user_id="user-123",
        job_type=ScheduledJobType.FOLLOW_UP_CHECK,
        email_thread_id="thread-123",
        scheduled_for=now,
        created_at=now,
    )


def test_execute_returns_no_reply_and_requires_notification():
    provider = FakeEmailProvider(
        [
            {
                "id": "sent-123",
                "payload": {
                    "headers": [
                        {
                            "name": "From",
                            "value": ACCOUNT_EMAIL,
                        }
                    ]
                },
            }
        ]
    )

    service = FollowUpExecutionService(provider)
    job = make_job()

    result = service.execute(
        job=job,
        account_id=ACCOUNT_EMAIL,
        account_email=ACCOUNT_EMAIL,
    )

    assert result.outcome == FollowUpOutcome.NO_REPLY
    assert result.notification_required is True
    assert result.reply_message_id is None
    assert job.status == ScheduledJobStatus.COMPLETED
    assert job.attempts == 1


def test_execute_returns_reply_received():
    provider = FakeEmailProvider(
        [
            {
                "id": "sent-123",
                "payload": {
                    "headers": [
                        {
                            "name": "From",
                            "value": ACCOUNT_EMAIL,
                        }
                    ]
                },
            },
            {
                "id": "reply-456",
                "payload": {
                    "headers": [
                        {
                            "name": "From",
                            "value": "person@example.com",
                        },
                        {
                            "name": "To",
                            "value": ACCOUNT_EMAIL,
                        },
                    ]
                },
            },
        ]
    )

    service = FollowUpExecutionService(provider)
    job = make_job()

    result = service.execute(
        job=job,
        account_id=ACCOUNT_EMAIL,
        account_email=ACCOUNT_EMAIL,
    )

    assert result.outcome == FollowUpOutcome.REPLY_RECEIVED
    assert result.reply_message_id == "reply-456"
    assert result.notification_required is False
    assert job.status == ScheduledJobStatus.COMPLETED
    assert job.attempts == 1


def test_execute_rejects_non_scheduled_job():
    provider = FakeEmailProvider([])
    service = FollowUpExecutionService(provider)
    job = make_job()
    job.status = ScheduledJobStatus.COMPLETED

    with pytest.raises(ValueError):
        service.execute(
            job=job,
            account_id=ACCOUNT_EMAIL,
            account_email=ACCOUNT_EMAIL,
        )
