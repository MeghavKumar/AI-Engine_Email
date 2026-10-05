from unittest.mock import Mock

from app.schemas.research import ResearchEvidence, ResearchSourceType
from app.services.web_research import WebResearchService


def test_web_research_service_returns_provider_evidence():
    provider = Mock()

    provider.search.return_value = [
        ResearchEvidence(
            source_type=ResearchSourceType.COMPANY_WEBSITE,
            source_reference="https://example.com/contact",
            evidence="Public company contact information.",
        )
    ]

    service = WebResearchService(provider)

    result = service.search(
        "John Doe Acme",
        source_type=ResearchSourceType.COMPANY_WEBSITE,
    )

    assert len(result) == 1
    assert result[0].source_type == ResearchSourceType.COMPANY_WEBSITE
    assert result[0].source_reference == "https://example.com/contact"

    provider.search.assert_called_once_with(
        "John Doe Acme",
        source_type=ResearchSourceType.COMPANY_WEBSITE,
    )


def test_web_research_service_defaults_to_web_source():
    provider = Mock()
    provider.search.return_value = []

    service = WebResearchService(provider)

    result = service.search("John Doe Acme")

    assert result == []

    provider.search.assert_called_once_with(
        "John Doe Acme",
        source_type=ResearchSourceType.WEB,
    )
