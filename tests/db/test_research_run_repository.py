from datetime import datetime, timezone

import pytest
from sqlalchemy.exc import IntegrityError

from app.db.repositories.research_run import ResearchRunRepository
from app.db.session import SessionLocal
from app.models import EmailAccount, ResearchRun


def test_create_and_get_research_run():
    with SessionLocal() as session:
        account = EmailAccount(
            user_id="research-run-test-user-create",
            provider="gmail",
            email_address="research-run-create@example.com",
        )
        session.add(account)
        session.flush()

        repository = ResearchRunRepository(session)

        research_run = repository.create(
            run_id="research-run-create-001",
            account_id=account.id,
            research_type="historical_recipient",
        )

        assert research_run.id is not None
        assert research_run.run_id == "research-run-create-001"
        assert research_run.account_id == account.id
        assert research_run.research_type == "historical_recipient"
        assert research_run.status == "pending"

        session.commit()

        loaded = repository.get("research-run-create-001")

        assert loaded is not None
        assert loaded.id == research_run.id
        assert loaded.account_id == account.id
        assert loaded.status == "pending"

        session.delete(loaded)
        session.flush()
        session.delete(account)
        session.commit()


def test_mark_started_sets_running_and_timestamp():
    started_at = datetime(
        2026,
        10,
        5,
        4,
        30,
        tzinfo=timezone.utc,
    )

    with SessionLocal() as session:
        account = EmailAccount(
            user_id="research-run-test-user-start",
            provider="gmail",
            email_address="research-run-start@example.com",
        )
        session.add(account)
        session.flush()

        research_run = ResearchRun(
            run_id="research-run-start-001",
            account_id=account.id,
            research_type="new_recipient",
            status="failed",
            error_message="previous failure",
        )
        session.add(research_run)
        session.flush()

        repository = ResearchRunRepository(session)

        result = repository.mark_started(
            research_run,
            started_at=started_at,
        )

        assert result.status == "running"
        assert result.started_at == started_at
        assert result.error_message is None

        session.delete(research_run)
        session.flush()
        session.delete(account)
        session.commit()


def test_mark_success_sets_completed_status_and_timestamp():
    completed_at = datetime(
        2026,
        10,
        5,
        4,
        45,
        tzinfo=timezone.utc,
    )

    with SessionLocal() as session:
        account = EmailAccount(
            user_id="research-run-test-user-success",
            provider="outlook",
            email_address="research-run-success@example.com",
        )
        session.add(account)
        session.flush()

        research_run = ResearchRun(
            run_id="research-run-success-001",
            account_id=account.id,
            research_type="historical_recipient",
            status="running",
        )
        session.add(research_run)
        session.flush()

        repository = ResearchRunRepository(session)

        result = repository.mark_success(
            research_run,
            completed_at=completed_at,
        )

        assert result.status == "completed"
        assert result.completed_at == completed_at
        assert result.error_message is None

        session.commit()

        loaded = repository.get("research-run-success-001")

        assert loaded is not None
        assert loaded.status == "completed"
        assert loaded.completed_at == completed_at

        session.delete(loaded)
        session.flush()
        session.delete(account)
        session.commit()


def test_mark_error_sets_failed_status_without_persisting_error_content():
    completed_at = datetime(
        2026,
        10,
        5,
        5,
        0,
        tzinfo=timezone.utc,
    )

    with SessionLocal() as session:
        account = EmailAccount(
            user_id="research-run-test-user-error",
            provider="gmail",
            email_address="research-run-error@example.com",
        )
        session.add(account)
        session.flush()

        research_run = ResearchRun(
            run_id="research-run-error-001",
            account_id=account.id,
            research_type="new_recipient",
            status="running",
        )
        session.add(research_run)
        session.flush()

        repository = ResearchRunRepository(session)

        result = repository.mark_error(
            research_run,
            completed_at=completed_at,
        )

        assert result.status == "failed"
        assert result.error_message is None
        assert result.completed_at == completed_at

        session.commit()

        loaded = repository.get("research-run-error-001")

        assert loaded is not None
        assert loaded.status == "failed"
        assert loaded.error_message is None

        session.delete(loaded)
        session.flush()
        session.delete(account)
        session.commit()


def test_run_id_is_unique():
    with SessionLocal() as session:
        account = EmailAccount(
            user_id="research-run-test-user-unique",
            provider="gmail",
            email_address="research-run-unique@example.com",
        )
        session.add(account)
        session.flush()

        first = ResearchRun(
            run_id="research-run-duplicate-001",
            account_id=account.id,
            research_type="historical_recipient",
            status="pending",
        )
        second = ResearchRun(
            run_id="research-run-duplicate-001",
            account_id=account.id,
            research_type="new_recipient",
            status="pending",
        )

        session.add(first)
        session.flush()

        session.add(second)

        with pytest.raises(IntegrityError):
            session.flush()
