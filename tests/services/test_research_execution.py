from unittest.mock import Mock

import pytest

from app.schemas.research import ResearchResult
from app.services.research_execution import ResearchExecutionService


def test_research_execution_marks_run_started_and_completed():
    research_agent = Mock()
    research_run_service = Mock()
    research_audit_service = Mock()

    research_run = Mock()
    research_run_service.create.return_value = research_run

    expected_result = ResearchResult(evidence=[])
    research_agent.research.return_value = expected_result

    service = ResearchExecutionService(
        research_agent=research_agent,
        research_run_service=research_run_service,
        research_audit_service=research_audit_service,
    )

    result = service.research(
        account_id=42,
        recipient_email="person@example.com",
        limit=10,
        web_query="person example company",
    )

    assert result == expected_result

    research_run_service.create.assert_called_once()
    create_kwargs = research_run_service.create.call_args.kwargs

    assert create_kwargs["account_id"] == 42
    assert create_kwargs["research_type"] == "recipient_research"
    assert isinstance(create_kwargs["run_id"], str)
    assert create_kwargs["run_id"]

    research_run_service.mark_started.assert_called_once_with(
        research_run,
    )
    research_run_service.mark_success.assert_called_once_with(
        research_run,
    )
    research_run_service.mark_error.assert_not_called()

    research_audit_service.create.assert_any_call(
        research_run_id=research_run.id,
        event_type="research_started",
    )
    research_audit_service.create.assert_any_call(
        research_run_id=research_run.id,
        event_type="research_completed",
    )

    assert research_audit_service.create.call_count == 2

    research_agent.research.assert_called_once_with(
        account_id=42,
        recipient_email="person@example.com",
        limit=10,
        web_query="person example company",
    )


def test_research_execution_marks_run_failed_when_agent_raises():
    research_agent = Mock()
    research_run_service = Mock()
    research_audit_service = Mock()

    research_run = Mock()
    research_run_service.create.return_value = research_run

    research_agent.research.side_effect = RuntimeError(
        "Research provider failed."
    )

    service = ResearchExecutionService(
        research_agent=research_agent,
        research_run_service=research_run_service,
        research_audit_service=research_audit_service,
    )

    with pytest.raises(RuntimeError, match="Research provider failed."):
        service.research(
            account_id=42,
            recipient_email="person@example.com",
        )

    research_run_service.mark_started.assert_called_once_with(
        research_run,
    )
    research_run_service.mark_error.assert_called_once_with(
        research_run,
        "Research provider failed.",
    )
    research_run_service.mark_success.assert_not_called()

    research_audit_service.create.assert_any_call(
        research_run_id=research_run.id,
        event_type="research_started",
    )
    research_audit_service.create.assert_any_call(
        research_run_id=research_run.id,
        event_type="research_failed",
    )

    assert research_audit_service.create.call_count == 2

    failed_call = research_audit_service.create.call_args_list[1]
    assert "Research provider failed." not in str(failed_call.kwargs)


def test_research_execution_new_recipient_tracks_lifecycle():
    research_agent = Mock()
    research_run_service = Mock()
    research_audit_service = Mock()

    research_run = Mock()
    research_run_service.create.return_value = research_run

    expected_result = ResearchResult(evidence=[])
    research_agent.research_new_recipient.return_value = expected_result

    service = ResearchExecutionService(
        research_agent=research_agent,
        research_run_service=research_run_service,
        research_audit_service=research_audit_service,
    )

    result = service.research_new_recipient(
        account_id=42,
        name="Jane Doe",
        role="Engineering Manager",
        organization="Example Corp",
        web_query="Jane Doe Example Corp",
    )

    assert result == expected_result

    create_kwargs = research_run_service.create.call_args.kwargs

    assert create_kwargs["account_id"] == 42
    assert create_kwargs["research_type"] == "new_recipient"
    assert isinstance(create_kwargs["run_id"], str)
    assert create_kwargs["run_id"]

    research_run_service.mark_started.assert_called_once_with(
        research_run,
    )
    research_run_service.mark_success.assert_called_once_with(
        research_run,
    )
    research_run_service.mark_error.assert_not_called()

    research_agent.research_new_recipient.assert_called_once_with(
        name="Jane Doe",
        role="Engineering Manager",
        organization="Example Corp",
        web_query="Jane Doe Example Corp",
    )
