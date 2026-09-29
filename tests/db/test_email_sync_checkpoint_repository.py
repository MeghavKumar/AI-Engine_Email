from datetime import datetime, timezone

import pytest
from sqlalchemy.exc import IntegrityError

from app.db.repositories.email_sync_checkpoint import (
    EmailSyncCheckpointRepository,
)
from app.db.session import SessionLocal
from app.models import EmailAccount, EmailSyncCheckpoint


def test_get_returns_checkpoint():
    with SessionLocal() as session:
        account = EmailAccount(
            user_id="checkpoint-test-user-get",
            provider="gmail",
            email_address="checkpoint-get@example.com",
        )
        session.add(account)
        session.flush()

        checkpoint = EmailSyncCheckpoint(
            account_id=account.id,
            provider="gmail",
            status="pending",
        )
        session.add(checkpoint)
        session.flush()

        repository = EmailSyncCheckpointRepository(session)

        loaded = repository.get(
            account.id,
            "gmail",
        )

        assert loaded is not None
        assert loaded.id == checkpoint.id
        assert loaded.account_id == account.id
        assert loaded.provider == "gmail"
        assert loaded.status == "pending"

        session.delete(checkpoint)
        session.flush()
        session.delete(account)
        session.commit()


def test_get_or_create_creates_checkpoint_once():
    with SessionLocal() as session:
        account = EmailAccount(
            user_id="checkpoint-test-user-create",
            provider="gmail",
            email_address="checkpoint-create@example.com",
        )
        session.add(account)
        session.flush()

        repository = EmailSyncCheckpointRepository(session)

        first = repository.get_or_create(
            account.id,
            "gmail",
        )
        second = repository.get_or_create(
            account.id,
            "gmail",
        )

        assert first.id is not None
        assert second.id == first.id
        assert second.account_id == account.id
        assert second.provider == "gmail"

        session.delete(first)
        session.flush()
        session.delete(account)
        session.commit()


def test_mark_started_sets_running_and_clears_error():
    with SessionLocal() as session:
        account = EmailAccount(
            user_id="checkpoint-test-user-start",
            provider="outlook",
            email_address="checkpoint-start@example.com",
        )
        session.add(account)
        session.flush()

        checkpoint = EmailSyncCheckpoint(
            account_id=account.id,
            provider="outlook",
            status="error",
            error_message="previous failure",
        )
        session.add(checkpoint)
        session.flush()

        repository = EmailSyncCheckpointRepository(session)

        result = repository.mark_started(checkpoint)

        assert result.id == checkpoint.id
        assert result.status == "running"
        assert result.error_message is None

        session.delete(checkpoint)
        session.flush()
        session.delete(account)
        session.commit()


def test_mark_success_persists_cursor_and_timestamp():
    synced_at = datetime(
        2026,
        9,
        26,
        20,
        30,
        tzinfo=timezone.utc,
    )

    with SessionLocal() as session:
        account = EmailAccount(
            user_id="checkpoint-test-user-success",
            provider="gmail",
            email_address="checkpoint-success@example.com",
        )
        session.add(account)
        session.flush()

        checkpoint = EmailSyncCheckpoint(
            account_id=account.id,
            provider="gmail",
            status="running",
        )
        session.add(checkpoint)
        session.flush()

        repository = EmailSyncCheckpointRepository(session)

        result = repository.mark_success(
            checkpoint,
            sync_cursor="history-12345",
            synced_at=synced_at,
        )

        assert result.status == "success"
        assert result.sync_cursor == "history-12345"
        assert result.last_synced_at == synced_at
        assert result.error_message is None

        session.commit()

        loaded = repository.get(
            account.id,
            "gmail",
        )

        assert loaded is not None
        assert loaded.sync_cursor == "history-12345"
        assert loaded.last_synced_at == synced_at
        assert loaded.status == "success"

        session.delete(loaded)
        session.flush()
        session.delete(account)
        session.commit()


def test_mark_error_preserves_last_successful_checkpoint():
    synced_at = datetime(
        2026,
        9,
        26,
        20,
        45,
        tzinfo=timezone.utc,
    )

    with SessionLocal() as session:
        account = EmailAccount(
            user_id="checkpoint-test-user-error",
            provider="gmail",
            email_address="checkpoint-error@example.com",
        )
        session.add(account)
        session.flush()

        checkpoint = EmailSyncCheckpoint(
            account_id=account.id,
            provider="gmail",
            status="success",
            sync_cursor="history-last-good",
            last_synced_at=synced_at,
        )
        session.add(checkpoint)
        session.flush()

        repository = EmailSyncCheckpointRepository(session)

        result = repository.mark_error(
            checkpoint,
            "temporary provider failure",
        )

        assert result.status == "error"
        assert result.error_message == "temporary provider failure"
        assert result.sync_cursor == "history-last-good"
        assert result.last_synced_at == synced_at

        session.commit()

        loaded = repository.get(
            account.id,
            "gmail",
        )

        assert loaded is not None
        assert loaded.status == "error"
        assert loaded.error_message == "temporary provider failure"
        assert loaded.sync_cursor == "history-last-good"
        assert loaded.last_synced_at == synced_at

        session.delete(loaded)
        session.flush()
        session.delete(account)
        session.commit()


def test_checkpoint_enforces_account_provider_uniqueness():
    with SessionLocal() as session:
        account = EmailAccount(
            user_id="checkpoint-test-user-unique",
            provider="gmail",
            email_address="checkpoint-unique@example.com",
        )
        session.add(account)
        session.flush()

        first = EmailSyncCheckpoint(
            account_id=account.id,
            provider="gmail",
            status="pending",
        )
        second = EmailSyncCheckpoint(
            account_id=account.id,
            provider="gmail",
            status="pending",
        )

        session.add(first)
        session.flush()

        session.add(second)

        with pytest.raises(IntegrityError):
            session.flush()

        session.rollback()
