from datetime import datetime, timezone
from unittest.mock import Mock

import pytest

from app.agents.research import ResearchAgent
from app.schemas.research import ResearchEvidence, ResearchSourceType


def test_research_returns_evidence_and_ai_assessment():
    mailbox_research = Mock()
    ai_provider = Mock()

    received_at = datetime(2026, 1, 15, 12, 30, tzinfo=timezone.utc)

    mailbox_research.find_historical_evidence.return_value = [
        ResearchEvidence(
            source_type=ResearchSourceType.MAILBOX,
            source_reference="message:123",
            evidence=(
                "Historical email from alice@example.com "
                "to john@example.com with subject 'Project discussion'."
            ),
            observed_at=received_at,
        )
    ]

    ai_provider.generate.return_value = (
        '{"assessment":"Historical communication exists with this recipient.",'
        '"confidence":0.9}'
    )

    agent = ResearchAgent(
        mailbox_research=mailbox_research,
        ai_provider=ai_provider,
    )

    result = agent.research(
        account_id=42,
        recipient_email="john@example.com",
        limit=10,
    )

    assert len(result.evidence) == 1
    assert result.evidence[0].source_reference == "message:123"

    assert result.assessment is not None
    assert (
        result.assessment.assessment
        == "Historical communication exists with this recipient."
    )
    assert result.assessment.confidence == 0.9

    mailbox_research.find_historical_evidence.assert_called_once_with(
        account_id=42,
        recipient_email="john@example.com",
        limit=10,
    )

    ai_provider.generate.assert_called_once()


def test_research_does_not_call_ai_when_no_evidence_exists():
    mailbox_research = Mock()
    ai_provider = Mock()

    mailbox_research.find_historical_evidence.return_value = []

    agent = ResearchAgent(
        mailbox_research=mailbox_research,
        ai_provider=ai_provider,
    )

    result = agent.research(
        account_id=42,
        recipient_email="john@example.com",
    )

    assert result.evidence == []
    assert result.assessment is None
    ai_provider.generate.assert_not_called()


def test_research_rejects_invalid_ai_json():
    mailbox_research = Mock()
    ai_provider = Mock()

    mailbox_research.find_historical_evidence.return_value = [
        ResearchEvidence(
            source_type=ResearchSourceType.MAILBOX,
            source_reference="message:123",
            evidence="Historical communication exists.",
        )
    ]

    ai_provider.generate.return_value = "not valid json"

    agent = ResearchAgent(
        mailbox_research=mailbox_research,
        ai_provider=ai_provider,
    )

    with pytest.raises(ValueError, match="invalid JSON"):
        agent.research(
            account_id=42,
            recipient_email="john@example.com",
        )


def test_research_prompt_contains_evidence_but_not_raw_uncontrolled_content():
    mailbox_research = Mock()
    ai_provider = Mock()

    mailbox_research.find_historical_evidence.return_value = [
        ResearchEvidence(
            source_type=ResearchSourceType.MAILBOX,
            source_reference="message:123",
            evidence="Historical email subject: Project discussion.",
        )
    ]

    ai_provider.generate.return_value = (
        '{"assessment":"Evidence supports prior communication.",'
        '"confidence":0.8}'
    )

    agent = ResearchAgent(
        mailbox_research=mailbox_research,
        ai_provider=ai_provider,
    )

    agent.research(
        account_id=42,
        recipient_email="john@example.com",
    )

    prompt = ai_provider.generate.call_args.kwargs["prompt"]

    assert "Project discussion" in prompt
    assert "Do not invent facts." in prompt
    assert "Do not invent email addresses." in prompt
    assert "Do not treat historical usage as authorization." in prompt


def test_research_agent_includes_web_evidence():
    class FakeMailboxResearch:
        def find_historical_evidence(
            self,
            *,
            account_id,
            recipient_email,
            limit,
        ):
            return []

    class FakeWebResearch:
        def search(self, query, *, source_type):
            return [
                ResearchEvidence(
                    source_type=source_type,
                    source_reference="web:example",
                    evidence="Public evidence about the recipient.",
                )
            ]

    class FakeAIProvider:
        def generate(self, prompt, context):
            assert "Public evidence about the recipient." in prompt
            return '{"assessment":"Evidence supports the candidate.","confidence":0.9}'

    agent = ResearchAgent(
        mailbox_research=FakeMailboxResearch(),
        ai_provider=FakeAIProvider(),
        web_research=FakeWebResearch(),
    )

    result = agent.research(
        account_id=1,
        recipient_email="person@example.com",
        web_query="person example company",
    )

    assert len(result.evidence) == 1
    assert result.evidence[0].source_type == ResearchSourceType.WEB
    assert result.assessment is not None
    assert result.assessment.confidence == 0.9


def test_research_agent_requires_web_service_for_web_query():
    class FakeMailboxResearch:
        def find_historical_evidence(
            self,
            *,
            account_id,
            recipient_email,
            limit,
        ):
            return []

    class FakeAIProvider:
        def generate(self, prompt, context):
            raise AssertionError("AI provider should not be called")

    agent = ResearchAgent(
        mailbox_research=FakeMailboxResearch(),
        ai_provider=FakeAIProvider(),
    )

    with pytest.raises(ValueError, match="WebResearchService is required"):
        agent.research(
            account_id=1,
            recipient_email="person@example.com",
            web_query="person example company",
        )


def test_research_agent_researches_new_recipient_without_inventing_email():
    class FakeMailboxResearch:
        def find_historical_evidence(
            self,
            *,
            account_id,
            recipient_email,
            limit,
        ):
            raise AssertionError("Mailbox research should not be used")

    class FakeWebResearch:
        def search(self, query, *, source_type):
            assert query == "Jane Doe Engineering Manager Example Corp"
            return [
                ResearchEvidence(
                    source_type=source_type,
                    source_reference="web:example-team",
                    evidence="Jane Doe is an Engineering Manager at Example Corp.",
                )
            ]

    class FakeAIProvider:
        def generate(self, prompt, context):
            assert "Do not invent email addresses." in prompt
            assert "Do not infer an email address from a naming convention." in prompt
            assert "Jane Doe is an Engineering Manager" in prompt
            assert context["research_type"] == "new_recipient"
            return '{"assessment":"Public evidence identifies the person and role.","confidence":0.95}'

    agent = ResearchAgent(
        mailbox_research=FakeMailboxResearch(),
        ai_provider=FakeAIProvider(),
        web_research=FakeWebResearch(),
    )

    result = agent.research_new_recipient(
        name="Jane Doe",
        role="Engineering Manager",
        organization="Example Corp",
    )

    assert len(result.evidence) == 1
    assert result.evidence[0].source_type == ResearchSourceType.WEB
    assert result.assessment is not None
    assert result.assessment.confidence == 0.95


def test_research_agent_requires_web_service_for_new_recipient():
    class FakeMailboxResearch:
        def find_historical_evidence(
            self,
            *,
            account_id,
            recipient_email,
            limit,
        ):
            raise AssertionError("Mailbox research should not be used")

    class FakeAIProvider:
        def generate(self, prompt, context):
            raise AssertionError("AI provider should not be called")

    agent = ResearchAgent(
        mailbox_research=FakeMailboxResearch(),
        ai_provider=FakeAIProvider(),
    )

    with pytest.raises(
        ValueError,
        match="WebResearchService is required for new recipient research",
    ):
        agent.research_new_recipient(
            name="Jane Doe",
            organization="Example Corp",
        )


def test_research_agent_new_recipient_allows_custom_web_query():
    class FakeMailboxResearch:
        def find_historical_evidence(
            self,
            *,
            account_id,
            recipient_email,
            limit,
        ):
            raise AssertionError("Mailbox research should not be used")

    class FakeWebResearch:
        def search(self, query, *, source_type):
            assert query == "Jane Doe Example Corp official profile"
            return []

    class FakeAIProvider:
        def generate(self, prompt, context):
            raise AssertionError("AI provider should not be called")

    agent = ResearchAgent(
        mailbox_research=FakeMailboxResearch(),
        ai_provider=FakeAIProvider(),
        web_research=FakeWebResearch(),
    )

    result = agent.research_new_recipient(
        name="Jane Doe",
        organization="Example Corp",
        web_query="Jane Doe Example Corp official profile",
    )

    assert result.evidence == []
    assert result.assessment is None
