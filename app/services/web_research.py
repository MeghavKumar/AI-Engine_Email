from app.providers.research import WebResearchProvider
from app.schemas.research import ResearchEvidence, ResearchSourceType


class WebResearchService:
    """Read-only service for approved external research."""

    def __init__(self, provider: WebResearchProvider):
        self.provider = provider

    def search(
        self,
        query: str,
        *,
        source_type: ResearchSourceType = ResearchSourceType.WEB,
    ) -> list[ResearchEvidence]:
        """Return structured evidence from an approved provider."""

        return self.provider.search(
            query,
            source_type=source_type,
        )
