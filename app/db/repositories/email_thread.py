from app.models.email_thread import EmailThread


class EmailThreadRepository:
    """Database repository for persisted email threads."""

    def __init__(self, session):
        self.session = session

    def get_by_provider_id(
        self,
        account_id: int,
        provider: str,
        provider_thread_id: str,
    ) -> EmailThread | None:
        """Return a thread by its provider-specific identity."""

        return (
            self.session.query(EmailThread)
            .filter(
                EmailThread.account_id == account_id,
                EmailThread.provider == provider,
                EmailThread.provider_thread_id == provider_thread_id,
            )
            .first()
        )

    def create(
        self,
        *,
        account_id: int,
        provider: str,
        provider_thread_id: str,
        subject: str = "",
    ) -> EmailThread:
        """Create and flush a persisted email thread."""

        thread = EmailThread(
            account_id=account_id,
            provider=provider,
            provider_thread_id=provider_thread_id,
            subject=subject,
        )

        self.session.add(thread)
        self.session.flush()

        return thread

    def update(
        self,
        thread: EmailThread,
        *,
        subject: str,
    ) -> EmailThread:
        """Update mutable thread fields."""

        thread.subject = subject

        self.session.flush()

        return thread
