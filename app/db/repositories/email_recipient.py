from app.models.email_recipient import EmailRecipient


class EmailRecipientRepository:
    """Database repository for persisted email recipients."""

    def __init__(self, session):
        self.session = session

    def get_by_identity(
        self,
        *,
        message_id: int,
        recipient_type: str,
        email: str,
    ) -> EmailRecipient | None:
        """Return a recipient by its message-level identity."""

        return (
            self.session.query(EmailRecipient)
            .filter(
                EmailRecipient.message_id == message_id,
                EmailRecipient.recipient_type == recipient_type,
                EmailRecipient.email == email,
            )
            .first()
        )

    def create(
        self,
        *,
        message_id: int,
        recipient_type: str,
        name: str | None,
        email: str,
    ) -> EmailRecipient:
        """Create and flush a persisted email recipient."""

        recipient = EmailRecipient(
            message_id=message_id,
            recipient_type=recipient_type,
            name=name,
            email=email,
        )

        self.session.add(recipient)
        self.session.flush()

        return recipient
