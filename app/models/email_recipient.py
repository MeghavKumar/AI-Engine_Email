from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class EmailRecipient(Base):
    """Persisted email recipient."""

    __tablename__ = "email_recipients"

    __table_args__ = (
        UniqueConstraint(
            "message_id",
            "recipient_type",
            "email",
            name="uq_email_recipient_message_type_email",
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

    recipient_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    email: Mapped[str] = mapped_column(
        String(320),
        nullable=False,
    )

    message: Mapped["EmailMessageRecord"] = relationship(
        "EmailMessageRecord",
        back_populates="recipients",
        foreign_keys=[message_id],
    )
