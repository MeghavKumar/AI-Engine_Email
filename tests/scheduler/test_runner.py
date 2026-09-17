import time
from datetime import datetime, timedelta, timezone
from threading import Event

from app.scheduler.runner import SchedulerRunner


def test_schedule_once_registers_job():
    runner = SchedulerRunner()

    try:
        run_at = datetime.now(timezone.utc) + timedelta(minutes=5)

        runner.schedule_once(
            job_id="job-123",
            run_at=run_at,
            callback=lambda: None,
        )

        job = runner.scheduler.get_job("job-123")

        assert job is not None
        assert job.id == "job-123"
    finally:
        runner.shutdown()


def test_scheduler_runs_callback():
    runner = SchedulerRunner()
    completed = Event()

    def callback():
        completed.set()

    try:
        runner.schedule_once(
            job_id="job-456",
            run_at=datetime.now(timezone.utc)
            + timedelta(seconds=0.2),
            callback=callback,
        )

        runner.start()

        assert completed.wait(timeout=2)
    finally:
        runner.shutdown()


def test_scheduler_can_start_and_shutdown():
    runner = SchedulerRunner()

    assert runner.scheduler.running is False

    runner.start()

    try:
        assert runner.scheduler.running is True
    finally:
        runner.shutdown()

    assert runner.scheduler.running is False
