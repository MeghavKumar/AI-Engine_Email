from datetime import datetime

from sqlalchemy.orm import Session

from app.db.repositories.research_run import ResearchRunRepository
from app.models import ResearchRun


class ResearchRunService:
    """Manage the persisted lifecycle of a research run."""

    def __init__(self, session: Session):
        self.repository = ResearchRunRepository(session)

    def create(
        self,
        *,
        run_id: str,
        account_id: int,
        research_type: str,
    ) -> ResearchRun:
        """Create a pending research run."""
        return self.repository.create(
            run_id=run_id,
            account_id=account_id,
            research_type=research_type,
        )

    def get(self, run_id: str) -> ResearchRun | None:
        """Return a research run by external run ID."""
        return self.repository.get(run_id)

    def mark_started(
        self,
        research_run: ResearchRun,
        *,
        started_at: datetime | None = None,
    ) -> ResearchRun:
        """Mark a research run as running."""
        return self.repository.mark_started(
            research_run,
            started_at=started_at,
        )

    def mark_success(
        self,
        research_run: ResearchRun,
        *,
        completed_at: datetime | None = None,
    ) -> ResearchRun:
        """Mark a research run as completed."""
        return self.repository.mark_success(
            research_run,
            completed_at=completed_at,
        )

    def mark_error(
        self,
        research_run: ResearchRun,
        *,
        completed_at: datetime | None = None,
    ) -> ResearchRun:
        """Mark a research run as failed without persisting exception content."""
        return self.repository.mark_error(
            research_run,
            completed_at=completed_at,
        )
