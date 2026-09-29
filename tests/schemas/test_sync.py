from app.schemas.sync import SyncChange, SyncChanges, SyncPage


def test_sync_page_defaults():
    page = SyncPage()
    assert page.messages == []
    assert page.next_cursor is None


def test_sync_changes_defaults():
    changes = SyncChanges()
    assert changes.changes == []
    assert changes.next_cursor is None
    assert changes.checkpoint_cursor is None
    assert changes.has_more is False


def test_sync_changes_accepts_upsert_and_delete_changes():
    changes = SyncChanges(
        changes=[
            SyncChange(
                change_type="upsert",
                message_id="message-1",
                message={"id": "message-1"},
            ),
            SyncChange(
                change_type="delete",
                message_id="message-2",
            ),
        ],
        next_cursor="page-token-2",
        checkpoint_cursor="checkpoint-100",
        has_more=True,
    )

    assert len(changes.changes) == 2
    assert changes.changes[0].change_type == "upsert"
    assert changes.changes[0].message_id == "message-1"
    assert changes.changes[0].message == {"id": "message-1"}
    assert changes.changes[1].change_type == "delete"
    assert changes.changes[1].message_id == "message-2"
    assert changes.changes[1].message is None
    assert changes.next_cursor == "page-token-2"
    assert changes.checkpoint_cursor == "checkpoint-100"
    assert changes.has_more is True
