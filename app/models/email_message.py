from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class EmailMessageRecord(Base):
    """Persisted normalized email message."""

    __tablename__ = "email_messages"

    __table_args__ = (
        UniqueConstraint(
            "account_id",
            "provider",
            "provider_message_id",
            name="uq_email_message_account_provider_message",
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

    thread_id: Mapped[int | None] = mapped_column(
        ForeignKey("email_threads.id"),
        nullable=True,
        index=True,
    )

    provider: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    provider_message_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    sender_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    sender_email: Mapped[str] = mapped_column(
        String(320),
        nullable=False,
    )

    subject: Mapped[str] = mapped_column(
        String(998),
        nullable=False,
        default="",
    )

    body_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
    )

    received_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    is_read: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    has_attachments: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
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

    thread: Mapped["EmailThread | None"] = relationship(
        "EmailThread",
        back_populates="messages",
    )

    attachments: Mapped[list["EmailAttachment"]] = relationship(
        "EmailAttachment",
        back_populates="message",
        cascade="all, delete-orphan",
    )

    recipients: Mapped[list["EmailRecipient"]] = relationship(
        "EmailRecipient",
        back_populates="message",
        cascade="all, delete-orphan",
        foreign_keys="EmailRecipient.message_id",
    )
