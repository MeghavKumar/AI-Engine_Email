from unittest.mock import Mock

from app.services.email_composition import EmailCompositionService


def test_composition_uses_bounded_context_for_correct_account_and_thread():
    composer = Mock()
    context_service = Mock()

    expected_context = {
        "account_id": 42,
        "thread_id": 17,
        "messages": [
            {
                "sender_email": "person@example.com",
                "subject": "Project update",
                "received_at": None,
                "body_text": "We discussed the project timeline.",
            }
        ],
        "truncated": False,
    }
    expected_draft = Mock()
    context_service.build_context.return_value = expected_context
    composer.compose.return_value = expected_draft

    service = EmailCompositionService(
        composer=composer,
        thread_context_service=context_service,
    )

    result = service.compose_for_thread(
        prompt="Draft a reply about the project timeline.",
        account_id=42,
        thread_id=17,
        max_messages=5,
        max_chars=4000,
    )

    assert result is expected_draft

    context_service.build_context.assert_called_once_with(
        account_id=42,
        thread_id=17,
        max_messages=5,
        max_chars=4000,
    )
    composer.compose.assert_called_once_with(
        prompt="Draft a reply about the project timeline.",
        context=expected_context,
    )


def test_composition_uses_default_context_limits():
    composer = Mock()
    context_service = Mock()
    context_service.build_context.return_value = {"messages": []}

    service = EmailCompositionService(
        composer=composer,
        thread_context_service=context_service,
    )

    service.compose_for_thread(
        prompt="Draft a reply.",
        account_id=7,
        thread_id=9,
    )

    context_service.build_context.assert_called_once_with(
        account_id=7,
        thread_id=9,
        max_messages=10,
        max_chars=12000,
    )


def test_composition_does_not_call_composer_if_context_retrieval_fails():
    composer = Mock()
    context_service = Mock()
    context_service.build_context.side_effect = RuntimeError(
        "Thread context unavailable"
    )

    service = EmailCompositionService(
        composer=composer,
        thread_context_service=context_service,
    )

    try:
        service.compose_for_thread(
            prompt="Draft a reply.",
            account_id=7,
            thread_id=9,
        )
    except RuntimeError as exc:
        assert str(exc) == "Thread context unavailable"
    else:
        raise AssertionError("Expected context retrieval to fail")

    composer.compose.assert_not_called()


def test_composition_includes_structured_research_evidence():
    from datetime import datetime, timezone

    from app.schemas.research import (
        ResearchAssessment,
        ResearchEvidence,
        ResearchResult,
        ResearchSourceType,
    )
    from app.schemas.email import EmailDraft

    composer = Mock()
    context_service = Mock()
    context_service.build_context.return_value = {
        "account_id": 42,
        "thread_id": 17,
        "messages": [],
        "truncated": False,
    }
    expected_draft = EmailDraft(
        to=["recipient@example.com"],
        subject="Project update",
        body="Here is the update.",
        confidence=0.9,
    )
    composer.compose.return_value = expected_draft

    research = ResearchResult(
        evidence=[
            ResearchEvidence(
                source_type=ResearchSourceType.MAILBOX,
                source_reference="message-123",
                evidence="The recipient previously requested a project update.",
                observed_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            )
        ],
        assessment=ResearchAssessment(
            assessment="A concise update is relevant.",
            confidence=0.85,
        ),
    )

    service = EmailCompositionService(
        composer=composer,
        thread_context_service=context_service,
    )

    result = service.compose_for_thread(
        prompt="Draft a project update.",
        account_id=42,
        thread_id=17,
        research_result=research,
    )

    assert result == expected_draft

    passed_context = composer.compose.call_args.kwargs["context"]
    assert passed_context["account_id"] == 42
    assert passed_context["thread_id"] == 17
    assert passed_context["research"]["evidence"][0]["source_reference"] == (
        "message-123"
    )
    assert passed_context["research"]["assessment"]["confidence"] == 0.85


def test_composition_omits_research_when_not_provided():
    composer = Mock()
    context_service = Mock()
    context_service.build_context.return_value = {
        "account_id": 7,
        "thread_id": 9,
        "messages": [],
        "truncated": False,
    }

    service = EmailCompositionService(
        composer=composer,
        thread_context_service=context_service,
    )

    service.compose_for_thread(
        prompt="Draft a reply.",
        account_id=7,
        thread_id=9,
    )

    passed_context = composer.compose.call_args.kwargs["context"]
    assert "research" not in passed_context
