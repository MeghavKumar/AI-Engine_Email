from datetime import datetime, timezone

from app.scheduler.schema import (
    ScheduledJob,
    ScheduledJobStatus,
    ScheduledJobType,
)


def test_scheduled_job_defaults():
    now = datetime.now(timezone.utc)

    job = ScheduledJob(
        id="job-123",
        user_id="user-123",
        job_type=ScheduledJobType.FOLLOW_UP_CHECK,
        email_thread_id="thread-123",
        scheduled_for=now,
        created_at=now,
    )

    assert job.status == ScheduledJobStatus.SCHEDULED
    assert job.attempts == 0
    assert job.payload == {}
    assert job.completed_at is None


def test_scheduled_job_supports_completion():
    now = datetime.now(timezone.utc)

    job = ScheduledJob(
        id="job-456",
        user_id="user-123",
        job_type=ScheduledJobType.REMINDER,
        email_thread_id="thread-456",
        scheduled_for=now,
        created_at=now,
        status=ScheduledJobStatus.COMPLETED,
        completed_at=now,
    )

    assert job.status == ScheduledJobStatus.COMPLETED
    assert job.completed_at == now


def test_scheduled_job_attempts_cannot_be_negative():
    now = datetime.now(timezone.utc)

    try:
        ScheduledJob(
            id="job-789",
            user_id="user-123",
            job_type=ScheduledJobType.FOLLOW_UP_CHECK,
            email_thread_id="thread-789",
            scheduled_for=now,
            created_at=now,
            attempts=-1,
        )
        assert False, "Expected validation error"
    except ValueError:
        pass
