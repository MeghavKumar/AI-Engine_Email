import pytest

from app.providers.email.sync import IncrementalEmailSyncProvider, PaginatedEmailSyncProvider
from app.schemas.sync import SyncChange, SyncChanges, SyncPage


class FakeSyncProvider(PaginatedEmailSyncProvider):
    def sync_page(
        self,
        account_id: str,
        cursor: str | None = None,
        max_results: int = 25,
    ) -> SyncPage:
        return SyncPage(
            messages=[
                {
                    "id": "message-1",
                    "threadId": "thread-1",
                }
            ],
            next_cursor="next-page",
        )


def test_sync_page_schema():
    page = SyncPage(
        messages=[{"id": "message-1"}],
        next_cursor="cursor-2",
    )

    assert page.messages == [{"id": "message-1"}]
    assert page.next_cursor == "cursor-2"


def test_sync_page_defaults():
    page = SyncPage()

    assert page.messages == []
    assert page.next_cursor is None


def test_paginated_sync_provider_contract():
    provider = FakeSyncProvider()

    page = provider.sync_page(
        account_id="test@example.com",
        max_results=10,
    )

    assert isinstance(page, SyncPage)
    assert page.messages[0]["id"] == "message-1"
    assert page.next_cursor == "next-page"


def test_paginated_sync_provider_remains_abstract():
    with pytest.raises(TypeError):
        PaginatedEmailSyncProvider()


class FakeIncrementalSyncProvider(IncrementalEmailSyncProvider):
    def sync_changes(
        self,
        account_id: str,
        checkpoint_cursor: str | None = None,
        page_cursor: str | None = None,
        max_results: int = 25,
    ) -> SyncChanges:
        return SyncChanges(
            changes=[
                SyncChange(
                    change_type="upsert",
                    message_id="message-1",
                    message={"id": "message-1"},
                )
            ],
            next_cursor="cursor-2",
            has_more=True,
        )


def test_incremental_email_sync_provider_returns_changes():
    provider = FakeIncrementalSyncProvider()

    result = provider.sync_changes("account-1", checkpoint_cursor="cursor-1")

    assert isinstance(result, SyncChanges)
    assert len(result.changes) == 1
    assert result.changes[0].change_type == "upsert"
    assert result.changes[0].message_id == "message-1"
    assert result.changes[0].message == {"id": "message-1"}
    assert result.next_cursor == "cursor-2"
    assert result.has_more is True
