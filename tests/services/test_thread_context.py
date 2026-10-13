from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from app.services.thread_context import ThreadContextService


def make_message(sender, subject, body, day=1):
    return SimpleNamespace(
        sender_email=sender,
        subject=subject,
        body_text=body,
        received_at=datetime(2026, 1, day, tzinfo=timezone.utc),
    )


def test_build_context_returns_chronological_account_scoped_messages():
    repository = Mock()
    repository.list_by_thread.return_value = [
        make_message("alice@example.com", "First", "Earlier", 1),
        make_message("bob@example.com", "Second", "Latest", 2),
    ]
    service = ThreadContextService(repository)

    result = service.build_context(account_id=7, thread_id=42)

    repository.list_by_thread.assert_called_once_with(
        account_id=7,
        thread_id=42,
        limit=10,
    )
    assert result["account_id"] == 7
    assert result["thread_id"] == 42
    assert [m["subject"] for m in result["messages"]] == [
        "First",
        "Second",
    ]
    assert [m["body_text"] for m in result["messages"]] == [
        "Earlier",
        "Latest",
    ]
    assert result["truncated"] is False


def test_build_context_respects_message_limit():
    repository = Mock()
    repository.list_by_thread.return_value = [
        make_message("alice@example.com", "One", "First"),
    ]
    service = ThreadContextService(repository)

    service.build_context(
        account_id=7,
        thread_id=42,
        max_messages=3,
    )

    repository.list_by_thread.assert_called_once_with(
        account_id=7,
        thread_id=42,
        limit=3,
    )


def test_build_context_bounds_total_content_characters():
    repository = Mock()
    repository.list_by_thread.return_value = [
        make_message("a@b.com", "Old", "older body", 1),
        make_message("c@d.com", "New", "newest body", 2),
    ]
    service = ThreadContextService(repository)

    result = service.build_context(
        account_id=7,
        thread_id=42,
        max_chars=60,
    )

    total_chars = sum(
        len(m["sender_email"])
        + len(m["subject"])
        + len(m["received_at"] or "")
        + len(m["body_text"])
        for m in result["messages"]
    )
    assert total_chars <= 60
    assert result["truncated"] is True
    assert result["messages"][-1]["subject"] == "New"


@pytest.mark.parametrize(
    ("options", "message"),
    [
        ({"max_messages": 0}, "max_messages must be at least 1"),
        ({"max_chars": 0}, "max_chars must be at least 1"),
    ],
)
def test_build_context_rejects_invalid_limits(options, message):
    service = ThreadContextService(Mock())

    with pytest.raises(ValueError, match=message):
        service.build_context(
            account_id=7,
            thread_id=42,
            **options,
        )


def test_build_context_handles_empty_thread():
    repository = Mock()
    repository.list_by_thread.return_value = []
    service = ThreadContextService(repository)

    result = service.build_context(account_id=7, thread_id=42)

    assert result["messages"] == []
    assert result["truncated"] is False
