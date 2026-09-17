from collections.abc import Callable
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler


class SchedulerRunner:
    """Manage application background jobs with APScheduler."""

    def __init__(self):
        self.scheduler = BackgroundScheduler()

    def start(self) -> None:
        if not self.scheduler.running:
            self.scheduler.start()

    def shutdown(self) -> None:
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)

    def schedule_once(
        self,
        job_id: str,
        run_at: datetime,
        callback: Callable,
        *args,
    ) -> None:
        self.scheduler.add_job(
            callback,
            trigger="date",
            run_date=run_at,
            args=args,
            id=job_id,
            replace_existing=True,
        )
