from app.db.repositories.email_message import EmailMessageRepository
from app.schemas.research import ResearchEvidence, ResearchSourceType


class MailboxResearchService:
    """Read-only service for historical mailbox research."""

    def __init__(self, repository: EmailMessageRepository):
        self.repository = repository

    def find_historical_evidence(
        self,
        *,
        account_id: int,
        recipient_email: str,
        limit: int = 20,
    ) -> list[ResearchEvidence]:
        """Return auditable evidence from historical mailbox messages."""

        messages = self.repository.find_by_recipient_email(
            account_id=account_id,
            email=recipient_email,
            limit=limit,
        )

        return [
            ResearchEvidence(
                source_type=ResearchSourceType.MAILBOX,
                source_reference=f"message:{message.id}",
                evidence=(
                    f"Historical email from {message.sender_email} "
                    f"to {recipient_email} with subject "
                    f"{message.subject!r}."
                ),
                observed_at=message.received_at,
            )
            for message in messages
        ]
