from datetime import datetime, timezone

import pytest

from app.providers.research import WebResearchProvider
from app.schemas.research import ResearchEvidence, ResearchSourceType


def test_web_research_provider_is_abstract():
    with pytest.raises(TypeError):
        WebResearchProvider()


def test_concrete_research_provider_returns_structured_evidence():
    class FakeResearchProvider(WebResearchProvider):
        def search(
            self,
            query: str,
            *,
            source_type: ResearchSourceType = ResearchSourceType.WEB,
        ) -> list[ResearchEvidence]:
            return [
                ResearchEvidence(
                    source_type=source_type,
                    source_reference="https://example.com/contact",
                    evidence="Public company contact information.",
                    observed_at=datetime(
                        2026,
                        1,
                        15,
                        12,
                        30,
                        tzinfo=timezone.utc,
                    ),
                )
            ]

    provider = FakeResearchProvider()

    result = provider.search(
        "John Doe Acme",
        source_type=ResearchSourceType.COMPANY_WEBSITE,
    )

    assert len(result) == 1
    assert result[0].source_type == ResearchSourceType.COMPANY_WEBSITE
    assert result[0].source_reference == "https://example.com/contact"


def test_research_provider_defaults_to_web_source_type():
    class FakeResearchProvider(WebResearchProvider):
        def search(
            self,
            query: str,
            *,
            source_type: ResearchSourceType = ResearchSourceType.WEB,
        ) -> list[ResearchEvidence]:
            return [
                ResearchEvidence(
                    source_type=source_type,
                    source_reference="https://example.com",
                    evidence="Public research result.",
                )
            ]

    provider = FakeResearchProvider()

    result = provider.search("John Doe Acme")

    assert result[0].source_type == ResearchSourceType.WEB
