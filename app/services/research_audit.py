import re

from sqlalchemy.orm import Session

from app.db.repositories.research_audit_event import ResearchAuditEventRepository
from app.models import ResearchAuditEvent


_OPAQUE_SOURCE_REFERENCE_PATTERN = re.compile(
    r"^[a-z][a-z0-9_-]*:[A-Za-z0-9_-]+$"
)


class ResearchAuditService:
    """Persist minimized, structured metadata for research activity."""

    def __init__(self, session: Session):
        self.repository = ResearchAuditEventRepository(session)

    def create(
        self,
        *,
        research_run_id: int,
        event_type: str,
        source_type: str | None = None,
        source_reference: str | None = None,
        confidence: float | None = None,
        verification_status: str | None = None,
        candidate_count: int | None = None,
        decision: str | None = None,
    ) -> ResearchAuditEvent:
        """Create a minimized audit event."""
        if source_reference is not None and not _OPAQUE_SOURCE_REFERENCE_PATTERN.fullmatch(
            source_reference
        ):
            raise ValueError(
                "Audit source_reference must be an opaque internal reference."
            )

        return self.repository.create(
            research_run_id=research_run_id,
            event_type=event_type,
            source_type=source_type,
            source_reference=source_reference,
            confidence=confidence,
            verification_status=verification_status,
            candidate_count=candidate_count,
            decision=decision,
        )

    def get(self, event_id: int) -> ResearchAuditEvent | None:
        """Return an audit event by ID."""
        return self.repository.get(event_id)

    def list_by_research_run(
        self,
        research_run_id: int,
    ) -> list[ResearchAuditEvent]:
        """Return audit events for a research run in creation order."""
        return self.repository.list_by_research_run(research_run_id)
