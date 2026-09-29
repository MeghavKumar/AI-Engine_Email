from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class EmailThread(Base):
    """Persisted email conversation/thread."""

    __tablename__ = "email_threads"

    __table_args__ = (
        UniqueConstraint(
            "account_id",
            "provider",
            "provider_thread_id",
            name="uq_email_thread_account_provider_thread",
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

    provider_thread_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    subject: Mapped[str] = mapped_column(
        String(998),
        nullable=False,
        default="",
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

    messages: Mapped[list["EmailMessageRecord"]] = relationship(
        "EmailMessageRecord",
        back_populates="thread",
        cascade="all, delete-orphan",
    )
