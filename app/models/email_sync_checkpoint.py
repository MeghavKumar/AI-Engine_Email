from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class EmailSyncCheckpoint(Base):
    """Persisted synchronization state for an email account."""

    __tablename__ = "email_sync_checkpoints"

    __table_args__ = (
        UniqueConstraint(
            "account_id",
            "provider",
            name="uq_email_sync_checkpoint_account_provider",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    account_id: Mapped[int] = mapped_column(
        ForeignKey("email_accounts.id"),
        nullable=False,
        index=True,
    )

    provider: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    sync_cursor: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    last_synced_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="pending",
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
