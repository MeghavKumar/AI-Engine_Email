from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.email_sync_checkpoint import EmailSyncCheckpoint


class EmailSyncCheckpointRepository:
    """Database repository for email synchronization checkpoints."""

    def __init__(self, session: Session):
        self.session = session

    def get(
        self,
        account_id: int,
        provider: str,
    ) -> EmailSyncCheckpoint | None:
        statement = select(EmailSyncCheckpoint).where(
            EmailSyncCheckpoint.account_id == account_id,
            EmailSyncCheckpoint.provider == provider,
        )

        return self.session.scalar(statement)

    def get_or_create(
        self,
        account_id: int,
        provider: str,
    ) -> EmailSyncCheckpoint:
        checkpoint = self.get(account_id, provider)

        if checkpoint is not None:
            return checkpoint

        checkpoint = EmailSyncCheckpoint(
            account_id=account_id,
            provider=provider,
            status="pending",
        )

        self.session.add(checkpoint)
        self.session.flush()

        return checkpoint

    def mark_started(
        self,
        checkpoint: EmailSyncCheckpoint,
    ) -> EmailSyncCheckpoint:
        checkpoint.status = "running"
        checkpoint.error_message = None
        self.session.flush()

        return checkpoint

    def mark_success(
        self,
        checkpoint: EmailSyncCheckpoint,
        sync_cursor: str | None,
        synced_at: datetime | None = None,
    ) -> EmailSyncCheckpoint:
        checkpoint.sync_cursor = sync_cursor
        checkpoint.last_synced_at = (
            synced_at
            if synced_at is not None
            else datetime.now(timezone.utc)
        )
        checkpoint.status = "success"
        checkpoint.error_message = None
        self.session.flush()

        return checkpoint

    def mark_error(
        self,
        checkpoint: EmailSyncCheckpoint,
        error_message: str,
    ) -> EmailSyncCheckpoint:
        checkpoint.status = "error"
        checkpoint.error_message = error_message
        self.session.flush()

        return checkpoint
