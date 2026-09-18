from datetime import datetime, timezone

import pytest

from app.scheduler.schema import ScheduledJobStatus, ScheduledJobType
from app.services.send_and_schedule import SendAndScheduleService
from tests.services.test_email_send import make_approved_state


class FakeEmailProvider:
    def __init__(self, sent_message=None):
        self.sent_message = sent_message
        self.sent_messages = []

    def list_messages(self, account_id, max_results=25):
        return []

    def get_message(self, account_id, message_id):
        if self.sent_message is None:
            raise ValueError("No fake sent message configured.")

        return self.sent_message

    def send_message(self, account_id, message):
        self.sent_messages.append(message)
        return "fake-message-001"

    def mark_read(self, account_id, message_id):
        raise NotImplementedError

    def archive_message(self, account_id, message_id):
        raise NotImplementedError

    def get_thread(self, account_id, thread_id):
        raise NotImplementedError


def test_send_and_schedule_uses_sent_message_thread_id():
    provider = FakeEmailProvider(
        sent_message={
            "id": "fake-message-001",
            "threadId": "fake-thread-001",
        }
    )

    service = SendAndScheduleService(provider)

    sent_at = datetime(
        2026,
        9,
        17,
        10,
        30,
        tzinfo=timezone.utc,
    )

    message_id, job = service.send_and_schedule(
        state=make_approved_state(),
        account_id="account-001",
        user_id="user-001",
        sent_at=sent_at,
    )

    assert message_id == "fake-message-001"
    assert job.user_id == "user-001"
    assert job.email_thread_id == "fake-thread-001"
    assert job.job_type == ScheduledJobType.FOLLOW_UP_CHECK
    assert job.status == ScheduledJobStatus.SCHEDULED
    assert job.scheduled_for == datetime(
        2026,
        9,
        21,
        10,
        30,
        tzinfo=timezone.utc,
    )
    assert len(provider.sent_messages) == 1


def test_send_and_schedule_requires_thread_id():
    provider = FakeEmailProvider(
        sent_message={
            "id": "fake-message-001",
        }
    )

    service = SendAndScheduleService(provider)

    with pytest.raises(
        ValueError,
        match="does not contain a thread ID",
    ):
        service.send_and_schedule(
            state=make_approved_state(),
            account_id="account-001",
            user_id="user-001",
        )
