from abc import ABC, abstractmethod

from app.schemas.research import ResearchEvidence, ResearchSourceType


class WebResearchProvider(ABC):
    """Provider interface for approved external research sources."""

    @abstractmethod
    def search(
        self,
        query: str,
        *,
        source_type: ResearchSourceType = ResearchSourceType.WEB,
    ) -> list[ResearchEvidence]:
        """Return auditable evidence from an approved research source."""
        raise NotImplementedError
