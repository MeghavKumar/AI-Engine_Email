from app.schemas.recipient import (
    RecipientCandidate,
    RecipientDiscoveryResult,
)
from app.schemas.research import ResearchContact
from app.services.mailbox_research import MailboxResearchService


class RecipientDiscoveryService:
    """Discover possible email recipients from known context."""

    def __init__(
        self,
        mailbox_research: MailboxResearchService | None = None,
    ):
        self.mailbox_research = mailbox_research

    def discover(
        self,
        candidates: list[RecipientCandidate] | None = None,
    ) -> RecipientDiscoveryResult:
        """Return candidate recipients for human verification."""

        return RecipientDiscoveryResult(
            candidates=candidates or [],
            requires_human_verification=True,
        )

    def discover_researched_candidate(
        self,
        contact: ResearchContact,
    ) -> RecipientDiscoveryResult:
        """Convert researched contact evidence into a candidate."""

        if contact.email is None:
            return RecipientDiscoveryResult(
                candidates=[],
                requires_human_verification=True,
            )

        source = contact.source_type.value.lower()

        if contact.email_is_inferred:
            source = "inference"

        candidate = RecipientCandidate(
            name=contact.name,
            email=contact.email,
            source=source,
            confidence=contact.confidence,
            reason=(
                f"{contact.reason} "
                "Research evidence does not constitute recipient "
                "authorization; human verification is required."
            ),
        )

        return RecipientDiscoveryResult(
            candidates=[candidate],
            requires_human_verification=True,
        )

    def discover_historical_candidate(
        self,
        *,
        account_id: int,
        email: str,
        name: str | None = None,
        limit: int = 20,
    ) -> RecipientDiscoveryResult:
        """Create a candidate only for an explicitly identified email."""

        if self.mailbox_research is None:
            raise ValueError(
                "MailboxResearchService is required for historical discovery."
            )

        evidence = self.mailbox_research.find_historical_evidence(
            account_id=account_id,
            recipient_email=email,
            limit=limit,
        )

        if not evidence:
            return RecipientDiscoveryResult(
                candidates=[],
                requires_human_verification=True,
            )

        candidate = RecipientCandidate(
            name=name,
            email=email,
            source="historical_mailbox",
            confidence=1.0,
            reason=(
                f"Historical mailbox evidence references this recipient "
                f"across {len(evidence)} message(s). "
                "Historical usage is evidence only and does not constitute "
                "recipient authorization."
            ),
        )

        return RecipientDiscoveryResult(
            candidates=[candidate],
            requires_human_verification=True,
        )
