from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.research_run import ResearchRun


class ResearchRunRepository:
    """Database repository for research-run metadata."""

    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        *,
        run_id: str,
        account_id: int,
        research_type: str,
        status: str = "pending",
    ) -> ResearchRun:
        research_run = ResearchRun(
            run_id=run_id,
            account_id=account_id,
            research_type=research_type,
            status=status,
        )

        self.session.add(research_run)
        self.session.flush()

        return research_run

    def get(
        self,
        run_id: str,
    ) -> ResearchRun | None:
        statement = select(ResearchRun).where(
            ResearchRun.run_id == run_id,
        )

        return self.session.scalar(statement)

    def mark_started(
        self,
        research_run: ResearchRun,
        started_at: datetime | None = None,
    ) -> ResearchRun:
        research_run.status = "running"
        research_run.started_at = (
            started_at
            if started_at is not None
            else datetime.now(timezone.utc)
        )
        research_run.error_message = None
        self.session.flush()

        return research_run

    def mark_success(
        self,
        research_run: ResearchRun,
        completed_at: datetime | None = None,
    ) -> ResearchRun:
        research_run.status = "completed"
        research_run.completed_at = (
            completed_at
            if completed_at is not None
            else datetime.now(timezone.utc)
        )
        research_run.error_message = None
        self.session.flush()

        return research_run

    def mark_error(
        self,
        research_run: ResearchRun,
        completed_at: datetime | None = None,
    ) -> ResearchRun:
        research_run.status = "failed"
        research_run.completed_at = (
            completed_at
            if completed_at is not None
            else datetime.now(timezone.utc)
        )
        research_run.error_message = None
        self.session.flush()

        return research_run
