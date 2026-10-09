from app.models.email_message import EmailMessageRecord
from sqlalchemy import func

from app.models.email_recipient import EmailRecipient


class EmailMessageRepository:
    """Database repository for persisted email messages."""

    def __init__(self, session):
        self.session = session

    def get_by_provider_id(
        self,
        account_id: int,
        provider: str,
        provider_message_id: str,
    ) -> EmailMessageRecord | None:
        return (
            self.session.query(EmailMessageRecord)
            .filter(
                EmailMessageRecord.account_id == account_id,
                EmailMessageRecord.provider == provider,
                EmailMessageRecord.provider_message_id
                == provider_message_id,
            )
            .first()
        )

    def list_by_thread(
        self,
        *,
        account_id: int,
        thread_id: int,
        limit: int = 100,
    ) -> list[EmailMessageRecord]:
        """List the most recent non-deleted thread messages chronologically."""

        if limit < 1:
            raise ValueError("limit must be at least 1")

        messages = (
            self.session.query(EmailMessageRecord)
            .filter(
                EmailMessageRecord.account_id == account_id,
                EmailMessageRecord.thread_id == thread_id,
                EmailMessageRecord.is_deleted.is_(False),
            )
            .order_by(
                EmailMessageRecord.received_at.desc(),
                EmailMessageRecord.id.desc(),
            )
            .limit(limit)
            .all()
        )

        return list(reversed(messages))

    def find_by_recipient_email(
        self,
        *,
        account_id: int,
        email: str,
        limit: int = 20,
    ) -> list[EmailMessageRecord]:
        """Find non-deleted messages sent to a recipient email."""

        normalized_email = email.strip().lower()

        return (
            self.session.query(EmailMessageRecord)
            .join(EmailRecipient)
            .filter(
                EmailMessageRecord.account_id == account_id,
                EmailMessageRecord.is_deleted.is_(False),
                func.lower(EmailRecipient.email) == normalized_email,
            )
            .order_by(EmailMessageRecord.received_at.desc())
            .limit(limit)
            .all()
        )

    def create(
        self,
        *,
        account_id: int,
        provider: str,
        provider_message_id: str,
        sender_name: str | None,
        sender_email: str,
        subject: str,
        body_text: str,
        received_at,
        is_read: bool,
        has_attachments: bool,
        thread_id: int | None = None,
    ) -> EmailMessageRecord:
        message = EmailMessageRecord(
            account_id=account_id,
            thread_id=thread_id,
            provider=provider,
            provider_message_id=provider_message_id,
            sender_name=sender_name,
            sender_email=sender_email,
            subject=subject,
            body_text=body_text,
            received_at=received_at,
            is_read=is_read,
            has_attachments=has_attachments,
        )

        self.session.add(message)
        self.session.flush()

        return message

    def update(
        self,
        message: EmailMessageRecord,
        *,
        sender_name: str | None,
        sender_email: str,
        subject: str,
        body_text: str,
        received_at,
        is_read: bool,
        has_attachments: bool,
        thread_id: int | None = None,
    ) -> EmailMessageRecord:
        message.sender_name = sender_name
        message.sender_email = sender_email
        message.subject = subject
        message.body_text = body_text
        message.received_at = received_at
        message.is_read = is_read
        message.has_attachments = has_attachments
        message.thread_id = thread_id
        message.is_deleted = False

        self.session.flush()

        return message

    def mark_deleted(
        self,
        message: EmailMessageRecord,
    ) -> EmailMessageRecord:
        message.is_deleted = True
        self.session.flush()
        return message

    def restore(
        self,
        message: EmailMessageRecord,
    ) -> EmailMessageRecord:
        message.is_deleted = False
        self.session.flush()
        return message
