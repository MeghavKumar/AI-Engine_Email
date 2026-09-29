from app.models.email_attachment import EmailAttachment


class EmailAttachmentRepository:
    """Database repository for persisted email attachments."""

    def __init__(self, session):
        self.session = session

    def get_by_identity(
        self,
        *,
        message_id: int,
        provider_attachment_id: str,
    ) -> EmailAttachment | None:
        """Return an attachment by its message-level provider identity."""

        return (
            self.session.query(EmailAttachment)
            .filter(
                EmailAttachment.message_id == message_id,
                EmailAttachment.provider_attachment_id
                == provider_attachment_id,
            )
            .first()
        )

    def create(
        self,
        *,
        message_id: int,
        provider_attachment_id: str,
        filename: str,
        content_type: str | None,
        size_bytes: int | None,
        is_inline: bool,
    ) -> EmailAttachment:
        """Create and flush persisted attachment metadata."""

        attachment = EmailAttachment(
            message_id=message_id,
            provider_attachment_id=provider_attachment_id,
            filename=filename,
            content_type=content_type,
            size_bytes=size_bytes,
            is_inline=is_inline,
        )

        self.session.add(attachment)
        self.session.flush()

        return attachment
