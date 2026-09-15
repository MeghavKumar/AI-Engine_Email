from app.schemas.recipient import (
    RecipientCandidate,
    RecipientDiscoveryResult,
)


class RecipientDiscoveryService:
    """Discover possible email recipients from known context."""

    def discover(
        self,
        candidates: list[RecipientCandidate] | None = None,
    ) -> RecipientDiscoveryResult:
        """Return candidate recipients for human verification."""

        return RecipientDiscoveryResult(
            candidates=candidates or [],
            requires_human_verification=True,
        )
