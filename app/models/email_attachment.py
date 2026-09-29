from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class EmailAttachment(Base):
    """Persisted metadata for an email attachment."""

    __tablename__ = "email_attachments"

    __table_args__ = (
        UniqueConstraint(
            "message_id",
            "provider_attachment_id",
            name="uq_email_attachment_message_provider_attachment",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    message_id: Mapped[int] = mapped_column(
        ForeignKey("email_messages.id"),
        nullable=False,
        index=True,
    )

    provider_attachment_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        default="",
    )

    content_type: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    size_bytes: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )

    is_inline: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    message: Mapped["EmailMessageRecord"] = relationship(
        "EmailMessageRecord",
        back_populates="attachments",
    )
