from datetime import datetime, timedelta, timezone

from app.services.follow_up_scheduler import FollowUpScheduler
from app.scheduler.schema import ScheduledJobStatus, ScheduledJobType


def test_schedule_reply_check_for_four_days_later():
    scheduler = FollowUpScheduler()

    sent_at = datetime(
        2026,
        9,
        17,
        10,
        30,
        tzinfo=timezone.utc,
    )

    job = scheduler.schedule_reply_check(
        user_id="user-123",
        email_thread_id="thread-123",
        sent_at=sent_at,
    )

    assert job.user_id == "user-123"
    assert job.email_thread_id == "thread-123"
    assert job.job_type == ScheduledJobType.FOLLOW_UP_CHECK
    assert job.status == ScheduledJobStatus.SCHEDULED
    assert job.scheduled_for == sent_at + timedelta(days=4)
    assert job.created_at.tzinfo is not None


def test_schedule_reply_check_generates_unique_job_ids():
    scheduler = FollowUpScheduler()

    sent_at = datetime(
        2026,
        9,
        17,
        10,
        30,
        tzinfo=timezone.utc,
    )

    first_job = scheduler.schedule_reply_check(
        user_id="user-123",
        email_thread_id="thread-123",
        sent_at=sent_at,
    )

    second_job = scheduler.schedule_reply_check(
        user_id="user-123",
        email_thread_id="thread-123",
        sent_at=sent_at,
    )

    assert first_job.id != second_job.id
