from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.research_audit_event import ResearchAuditEvent


class ResearchAuditEventRepository:
    """Database repository for minimized research audit events."""

    def __init__(self, session: Session):
        self.session = session

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
        event = ResearchAuditEvent(
            research_run_id=research_run_id,
            event_type=event_type,
            source_type=source_type,
            source_reference=source_reference,
            confidence=confidence,
            verification_status=verification_status,
            candidate_count=candidate_count,
            decision=decision,
        )

        self.session.add(event)
        self.session.flush()

        return event

    def get(
        self,
        event_id: int,
    ) -> ResearchAuditEvent | None:
        statement = select(ResearchAuditEvent).where(
            ResearchAuditEvent.id == event_id,
        )

        return self.session.scalar(statement)

    def list_by_research_run(
        self,
        research_run_id: int,
    ) -> list[ResearchAuditEvent]:
        statement = (
            select(ResearchAuditEvent)
            .where(
                ResearchAuditEvent.research_run_id == research_run_id,
            )
            .order_by(ResearchAuditEvent.id)
        )

        return list(self.session.scalars(statement).all())
