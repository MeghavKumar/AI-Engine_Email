from datetime import datetime, timezone

from app.db.session import SessionLocal
from app.services.research_run import ResearchRunService


def test_create_and_get_research_run():
    with SessionLocal() as session:
        service = ResearchRunService(session)

        created = service.create(
            run_id="research-service-run-001",
            account_id=1,
            research_type="historical_recipient",
        )

        assert created.run_id == "research-service-run-001"
        assert created.account_id == 1
        assert created.research_type == "historical_recipient"
        assert created.status == "pending"

        fetched = service.get("research-service-run-001")

        assert fetched is not None
        assert fetched.id == created.id

        session.delete(created)
        session.commit()


def test_mark_started_research_run():
    with SessionLocal() as session:
        service = ResearchRunService(session)

        research_run = service.create(
            run_id="research-service-run-002",
            account_id=1,
            research_type="historical_recipient",
        )

        started_at = datetime(2026, 1, 1, tzinfo=timezone.utc)

        service.mark_started(
            research_run,
            started_at=started_at,
        )

        assert research_run.status == "running"
        assert research_run.started_at == started_at
        assert research_run.error_message is None

        session.delete(research_run)
        session.commit()


def test_mark_success_research_run():
    with SessionLocal() as session:
        service = ResearchRunService(session)

        research_run = service.create(
            run_id="research-service-run-003",
            account_id=1,
            research_type="new_recipient",
        )

        completed_at = datetime(2026, 1, 1, 1, tzinfo=timezone.utc)

        service.mark_success(
            research_run,
            completed_at=completed_at,
        )

        assert research_run.status == "completed"
        assert research_run.completed_at == completed_at
        assert research_run.error_message is None

        session.delete(research_run)
        session.commit()


def test_mark_error_research_run():
    with SessionLocal() as session:
        service = ResearchRunService(session)

        research_run = service.create(
            run_id="research-service-run-004",
            account_id=1,
            research_type="new_recipient",
        )

        completed_at = datetime(2026, 1, 1, 2, tzinfo=timezone.utc)

        service.mark_error(
            research_run,
            "Research provider failed.",
            completed_at=completed_at,
        )

        assert research_run.status == "failed"
        assert research_run.completed_at == completed_at
        assert research_run.error_message == "Research provider failed."

        session.delete(research_run)
        session.commit()
