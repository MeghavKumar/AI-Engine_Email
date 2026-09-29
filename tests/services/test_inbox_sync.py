from unittest.mock import Mock

from app.db.repositories.email_account import EmailAccountRepository
from app.db.repositories.email_recipient import EmailRecipientRepository
from app.providers.email.normalization import NormalizedEmailProvider
from app.providers.email.sync import (
    IncrementalEmailSyncProvider,
    PaginatedEmailSyncProvider,
)
from app.schemas.provider import EmailAddress, EmailAttachment, EmailMessage
from app.schemas.sync import SyncPage
from app.services.inbox_sync import InboxSyncService


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
                }
            ],
            next_cursor="next-page",
        )


class FakeNormalizedProvider(NormalizedEmailProvider):
    def __init__(self):
        self.get_message_calls = []

    def get_message(
        self,
        account_id: str,
        message_id: str,
    ) -> dict:
        self.get_message_calls.append(
            (account_id, message_id)
        )

        return {
            "id": message_id,
        }

    def normalize_message(
        self,
        account_id: str,
        raw_message: dict,
    ) -> EmailMessage:
        return EmailMessage(
            provider="fake",
            account_id=account_id,
            message_id=raw_message["id"],
            sender=EmailAddress(
                email="sender@example.com"
            ),
            subject="Test subject",
        )


def test_fetch_page_delegates_to_provider():
    provider = FakeSyncProvider()
    normalized_provider = Mock(spec=NormalizedEmailProvider)
    account_repository = Mock(spec=EmailAccountRepository)
    thread_repository = Mock()
    message_repository = Mock()

    service = InboxSyncService(
        provider=provider,
        normalized_provider=normalized_provider,
        account_repository=account_repository,
        thread_repository=thread_repository,
        message_repository=message_repository,
        recipient_repository=Mock(spec=EmailRecipientRepository),
        attachment_repository=Mock(),
        checkpoint_repository=Mock(),
    )

    result = service.fetch_page(
        account_id="account-1",
        cursor="cursor-1",
        max_results=10,
    )

    assert result.messages == [{"id": "message-1"}]
    assert result.next_cursor == "next-page"


def test_fetch_and_normalize_message():
    provider = FakeSyncProvider()
    normalized_provider = FakeNormalizedProvider()
    account_repository = Mock(spec=EmailAccountRepository)
    thread_repository = Mock()
    message_repository = Mock()

    service = InboxSyncService(
        provider=provider,
        normalized_provider=normalized_provider,
        account_repository=account_repository,
        thread_repository=thread_repository,
        message_repository=message_repository,
        recipient_repository=Mock(spec=EmailRecipientRepository),
        attachment_repository=Mock(),
        checkpoint_repository=Mock(),
    )

    result = service.fetch_and_normalize_message(
        account_id="account-1",
        message_id="message-1",
    )

    assert isinstance(result, EmailMessage)
    assert result.provider == "fake"
    assert result.account_id == "account-1"
    assert result.message_id == "message-1"
    assert result.subject == "Test subject"

    assert normalized_provider.get_message_calls == [
        ("account-1", "message-1")
    ]


def test_get_account_returns_active_account():
    account_repository = Mock(spec=EmailAccountRepository)
    account = Mock()
    account.id = 1
    account.is_active = True

    account_repository.get_by_id.return_value = account

    service = InboxSyncService(
        provider=FakeSyncProvider(),
        normalized_provider=Mock(spec=NormalizedEmailProvider),
        account_repository=account_repository,
        thread_repository=Mock(),
        message_repository=Mock(),
        recipient_repository=Mock(spec=EmailRecipientRepository),
        attachment_repository=Mock(),
        checkpoint_repository=Mock(),
    )

    result = service.get_account(1)

    assert result is account
    account_repository.get_by_id.assert_called_once_with(1)


def test_get_account_rejects_missing_or_inactive_account():
    account_repository = Mock(spec=EmailAccountRepository)
    account_repository.get_by_id.return_value = None

    service = InboxSyncService(
        provider=FakeSyncProvider(),
        normalized_provider=Mock(spec=NormalizedEmailProvider),
        account_repository=account_repository,
        thread_repository=Mock(),
        message_repository=Mock(),
        recipient_repository=Mock(spec=EmailRecipientRepository),
        attachment_repository=Mock(),
        checkpoint_repository=Mock(),
    )

    try:
        service.get_account(999)
        assert False, "Expected ValueError for missing account"
    except ValueError as exc:
        assert str(exc) == "Email account 999 not found."

    inactive_account = Mock()
    inactive_account.id = 2
    inactive_account.is_active = False
    account_repository.get_by_id.return_value = inactive_account

    try:
        service.get_account(2)
        assert False, "Expected ValueError for inactive account"
    except ValueError as exc:
        assert str(exc) == "Email account 2 is inactive."


def test_persist_recipients_persists_to_and_cc():
    recipient_repository = Mock(spec=EmailRecipientRepository)
    recipient_repository.get_by_identity.return_value = None

    service = InboxSyncService(
        provider=FakeSyncProvider(),
        normalized_provider=Mock(spec=NormalizedEmailProvider),
        account_repository=Mock(spec=EmailAccountRepository),
        thread_repository=Mock(),
        message_repository=Mock(),
        recipient_repository=recipient_repository,
        attachment_repository=Mock(),
        checkpoint_repository=Mock(),
    )

    message = EmailMessage(
        provider="fake",
        account_id="account-1",
        message_id="message-1",
        sender=EmailAddress(email="sender@example.com"),
        recipients=[
            EmailAddress(
                name="To Person",
                email="to@example.com",
            )
        ],
        cc=[
            EmailAddress(
                name="CC Person",
                email="cc@example.com",
            )
        ],
        subject="Test subject",
    )

    service.persist_recipients(
        message=message,
        persisted_message_id=42,
    )

    assert recipient_repository.create.call_count == 2

    recipient_repository.create.assert_any_call(
        message_id=42,
        recipient_type="to",
        name="To Person",
        email="to@example.com",
    )

    recipient_repository.create.assert_any_call(
        message_id=42,
        recipient_type="cc",
        name="CC Person",
        email="cc@example.com",
    )


def test_persist_message_creates_thread_message_and_recipients():
    account_repository = Mock(spec=EmailAccountRepository)
    thread_repository = Mock()
    message_repository = Mock()
    recipient_repository = Mock(spec=EmailRecipientRepository)
    recipient_repository.get_by_identity.return_value = None
    attachment_repository = Mock()

    thread = Mock()
    thread.id = 101

    persisted_message = Mock()
    persisted_message.id = 202

    thread_repository.get_by_provider_id.return_value = None
    thread_repository.create.return_value = thread

    message_repository.get_by_provider_id.return_value = None
    message_repository.create.return_value = persisted_message

    service = InboxSyncService(
        provider=FakeSyncProvider(),
        normalized_provider=Mock(spec=NormalizedEmailProvider),
        account_repository=account_repository,
        thread_repository=thread_repository,
        message_repository=message_repository,
        recipient_repository=recipient_repository,
        attachment_repository=attachment_repository,
        checkpoint_repository=Mock(),
    )

    message = EmailMessage(
        provider="gmail",
        account_id="provider-account-1",
        message_id="message-1",
        thread_id="thread-1",
        sender=EmailAddress(
            name="Sender",
            email="sender@example.com",
        ),
        recipients=[
            EmailAddress(
                name="Recipient",
                email="recipient@example.com",
            )
        ],
        cc=[
            EmailAddress(
                name="CC Person",
                email="cc@example.com",
            )
        ],
        subject="Test subject",
        body_text="Hello",
        is_read=False,
        has_attachments=True,
    )

    result = service.persist_message(
        account_id=1,
        message=message,
    )

    assert result is persisted_message

    thread_repository.get_by_provider_id.assert_called_once_with(
        account_id=1,
        provider="gmail",
        provider_thread_id="thread-1",
    )

    thread_repository.create.assert_called_once_with(
        account_id=1,
        provider="gmail",
        provider_thread_id="thread-1",
        subject="Test subject",
    )

    message_repository.get_by_provider_id.assert_called_once_with(
        account_id=1,
        provider="gmail",
        provider_message_id="message-1",
    )

    message_repository.create.assert_called_once_with(
        account_id=1,
        provider="gmail",
        provider_message_id="message-1",
        sender_name="Sender",
        sender_email="sender@example.com",
        subject="Test subject",
        body_text="Hello",
        received_at=None,
        is_read=False,
        has_attachments=True,
        thread_id=101,
    )

    assert recipient_repository.create.call_count == 2
    attachment_repository.get_by_identity.assert_not_called()


def test_persist_message_updates_existing_message():
    thread_repository = Mock()
    message_repository = Mock()
    recipient_repository = Mock(spec=EmailRecipientRepository)
    recipient_repository.get_by_identity.return_value = None

    existing_thread = Mock()
    existing_thread.id = 303

    existing_message = Mock()
    existing_message.id = 404

    thread_repository.get_by_provider_id.return_value = existing_thread
    message_repository.get_by_provider_id.return_value = existing_message
    message_repository.update.return_value = existing_message

    service = InboxSyncService(
        provider=FakeSyncProvider(),
        normalized_provider=Mock(spec=NormalizedEmailProvider),
        account_repository=Mock(spec=EmailAccountRepository),
        thread_repository=thread_repository,
        message_repository=message_repository,
        recipient_repository=recipient_repository,
        attachment_repository=Mock(),
        checkpoint_repository=Mock(),
    )

    message = EmailMessage(
        provider="gmail",
        account_id="provider-account-1",
        message_id="message-1",
        thread_id="thread-1",
        sender=EmailAddress(
            name="Updated Sender",
            email="updated@example.com",
        ),
        recipients=[
            EmailAddress(
                name="Recipient",
                email="recipient@example.com",
            )
        ],
        subject="Updated subject",
        body_text="Updated body",
        is_read=True,
        has_attachments=False,
    )

    result = service.persist_message(
        account_id=1,
        message=message,
    )

    assert result is existing_message

    thread_repository.get_by_provider_id.assert_called_once_with(
        account_id=1,
        provider="gmail",
        provider_thread_id="thread-1",
    )

    thread_repository.update.assert_called_once_with(
        existing_thread,
        subject="Updated subject",
    )

    message_repository.get_by_provider_id.assert_called_once_with(
        account_id=1,
        provider="gmail",
        provider_message_id="message-1",
    )

    message_repository.update.assert_called_once_with(
        existing_message,
        sender_name="Updated Sender",
        sender_email="updated@example.com",
        subject="Updated subject",
        body_text="Updated body",
        received_at=None,
        is_read=True,
        has_attachments=False,
        thread_id=303,
    )

    message_repository.create.assert_not_called()


def test_persist_recipients_does_not_duplicate_existing_recipients():
    thread_repository = Mock()
    message_repository = Mock()
    recipient_repository = Mock(spec=EmailRecipientRepository)

    existing_to = Mock()
    existing_cc = Mock()

    def get_by_identity(*, message_id, recipient_type, email):
        if recipient_type == "to":
            return existing_to
        if recipient_type == "cc":
            return existing_cc
        return None

    recipient_repository.get_by_identity.side_effect = get_by_identity

    service = InboxSyncService(
        provider=Mock(spec=PaginatedEmailSyncProvider),
        normalized_provider=Mock(spec=NormalizedEmailProvider),
        account_repository=Mock(spec=EmailAccountRepository),
        thread_repository=thread_repository,
        message_repository=message_repository,
        recipient_repository=recipient_repository,
        attachment_repository=Mock(),
        checkpoint_repository=Mock(),
    )

    message = EmailMessage(
        provider="gmail",
        account_id="provider-account-1",
        message_id="message-1",
        sender=EmailAddress(
            name="Sender",
            email="sender@example.com",
        ),
        recipients=[
            EmailAddress(
                name="Recipient",
                email="recipient@example.com",
            )
        ],
        cc=[
            EmailAddress(
                name="CC Person",
                email="cc@example.com",
            )
        ],
        subject="Test subject",
        body_text="Hello",
    )

    service.persist_recipients(
        message=message,
        persisted_message_id=101,
    )

    assert recipient_repository.get_by_identity.call_count == 2
    assert recipient_repository.create.call_count == 0


def test_persist_attachments_persists_metadata():
    attachment_repository = Mock()
    attachment_repository.get_by_identity.return_value = None

    service = InboxSyncService(
        provider=FakeSyncProvider(),
        normalized_provider=Mock(spec=NormalizedEmailProvider),
        account_repository=Mock(spec=EmailAccountRepository),
        thread_repository=Mock(),
        message_repository=Mock(),
        recipient_repository=Mock(spec=EmailRecipientRepository),
        attachment_repository=attachment_repository,
        checkpoint_repository=Mock(),
    )

    message = EmailMessage(
        provider="gmail",
        account_id="account-1",
        message_id="message-1",
        sender=EmailAddress(email="sender@example.com"),
        attachments=[
            EmailAttachment(
                provider_attachment_id="attachment-1",
                filename="report.pdf",
                content_type="application/pdf",
                size_bytes=12345,
                is_inline=False,
            )
        ],
    )

    service.persist_attachments(
        message=message,
        persisted_message_id=42,
    )

    attachment_repository.get_by_identity.assert_called_once_with(
        message_id=42,
        provider_attachment_id="attachment-1",
    )

    attachment_repository.create.assert_called_once_with(
        message_id=42,
        provider_attachment_id="attachment-1",
        filename="report.pdf",
        content_type="application/pdf",
        size_bytes=12345,
        is_inline=False,
    )


def test_persist_attachments_does_not_duplicate_existing_attachment():
    attachment_repository = Mock()
    existing_attachment = Mock()
    attachment_repository.get_by_identity.return_value = existing_attachment

    service = InboxSyncService(
        provider=FakeSyncProvider(),
        normalized_provider=Mock(spec=NormalizedEmailProvider),
        account_repository=Mock(spec=EmailAccountRepository),
        thread_repository=Mock(),
        message_repository=Mock(),
        recipient_repository=Mock(spec=EmailRecipientRepository),
        attachment_repository=attachment_repository,
        checkpoint_repository=Mock(),
    )

    message = EmailMessage(
        provider="gmail",
        account_id="account-1",
        message_id="message-1",
        sender=EmailAddress(email="sender@example.com"),
        attachments=[
            EmailAttachment(
                provider_attachment_id="attachment-1",
                filename="report.pdf",
                content_type="application/pdf",
                size_bytes=12345,
                is_inline=False,
            )
        ],
    )

    service.persist_attachments(
        message=message,
        persisted_message_id=42,
    )

    attachment_repository.get_by_identity.assert_called_once_with(
        message_id=42,
        provider_attachment_id="attachment-1",
    )

    attachment_repository.create.assert_not_called()


def test_persist_message_persists_attachment_metadata():
    account_repository = Mock(spec=EmailAccountRepository)
    thread_repository = Mock()
    message_repository = Mock()
    recipient_repository = Mock(spec=EmailRecipientRepository)
    attachment_repository = Mock()

    recipient_repository.get_by_identity.return_value = None
    attachment_repository.get_by_identity.return_value = None

    persisted_message = Mock()
    persisted_message.id = 202

    message_repository.get_by_provider_id.return_value = None
    message_repository.create.return_value = persisted_message

    service = InboxSyncService(
        provider=FakeSyncProvider(),
        normalized_provider=Mock(spec=NormalizedEmailProvider),
        account_repository=account_repository,
        thread_repository=thread_repository,
        message_repository=message_repository,
        recipient_repository=recipient_repository,
        attachment_repository=attachment_repository,
        checkpoint_repository=Mock(),
    )

    message = EmailMessage(
        provider="gmail",
        account_id="account-1",
        message_id="message-1",
        sender=EmailAddress(email="sender@example.com"),
        subject="With attachment",
        body_text="Please see attached.",
        has_attachments=True,
        attachments=[
            EmailAttachment(
                provider_attachment_id="attachment-1",
                filename="report.pdf",
                content_type="application/pdf",
                size_bytes=12345,
                is_inline=False,
            )
        ],
    )

    result = service.persist_message(
        account_id=1,
        message=message,
    )

    assert result is persisted_message

    attachment_repository.get_by_identity.assert_called_once_with(
        message_id=202,
        provider_attachment_id="attachment-1",
    )

    attachment_repository.create.assert_called_once_with(
        message_id=202,
        provider_attachment_id="attachment-1",
        filename="report.pdf",
        content_type="application/pdf",
        size_bytes=12345,
        is_inline=False,
    )


class InitialSyncProvider(PaginatedEmailSyncProvider):
    def __init__(self):
        self.calls = []

    def sync_page(
        self,
        account_id: str,
        cursor: str | None = None,
        max_results: int = 25,
    ) -> SyncPage:
        self.calls.append(
            (account_id, cursor, max_results)
        )

        if cursor is None:
            return SyncPage(
                messages=[
                    {"id": "message-1"},
                    {"id": "message-2"},
                ],
                next_cursor="page-2",
            )

        return SyncPage(
            messages=[
                {"id": "message-3"},
            ],
            next_cursor=None,
        )


def test_sync_initial_fetches_all_pages_normalizes_and_persists_messages():
    provider = InitialSyncProvider()
    normalized_provider = FakeNormalizedProvider()

    account = Mock()
    account.id = 1
    account.is_active = True

    account_repository = Mock(spec=EmailAccountRepository)
    account_repository.get_by_id.return_value = account

    thread_repository = Mock()
    message_repository = Mock()
    recipient_repository = Mock(spec=EmailRecipientRepository)
    attachment_repository = Mock()

    persisted_messages = []

    def persist_message(*, account_id, message):
        persisted_messages.append(
            (account_id, message.message_id)
        )
        return Mock(id=len(persisted_messages))

    service = InboxSyncService(
        provider=provider,
        normalized_provider=normalized_provider,
        account_repository=account_repository,
        thread_repository=thread_repository,
        message_repository=message_repository,
        recipient_repository=recipient_repository,
        attachment_repository=attachment_repository,
        checkpoint_repository=Mock(),
    )

    service.persist_message = persist_message

    result = service.sync_initial(
        account_id=1,
        provider_account_id="provider-account-1",
        max_results=2,
    )

    assert result == {
        "messages_synced": 3,
        "pages_synced": 2,
    }

    assert provider.calls == [
        ("provider-account-1", None, 2),
        ("provider-account-1", "page-2", 2),
    ]

    assert normalized_provider.get_message_calls == [
        ("provider-account-1", "message-1"),
        ("provider-account-1", "message-2"),
        ("provider-account-1", "message-3"),
    ]

    assert persisted_messages == [
        (1, "message-1"),
        (1, "message-2"),
        (1, "message-3"),
    ]


class EmptyInitialSyncProvider(PaginatedEmailSyncProvider):
    def __init__(self):
        self.calls = []

    def sync_page(
        self,
        account_id: str,
        cursor: str | None = None,
        max_results: int = 25,
    ) -> SyncPage:
        self.calls.append(
            (account_id, cursor, max_results)
        )

        return SyncPage(
            messages=[],
            next_cursor=None,
        )


def test_sync_initial_handles_empty_inbox():
    provider = EmptyInitialSyncProvider()
    account = Mock()
    account.id = 1
    account.is_active = True

    account_repository = Mock(spec=EmailAccountRepository)
    account_repository.get_by_id.return_value = account

    service = InboxSyncService(
        provider=provider,
        normalized_provider=Mock(spec=NormalizedEmailProvider),
        account_repository=account_repository,
        thread_repository=Mock(),
        message_repository=Mock(),
        recipient_repository=Mock(spec=EmailRecipientRepository),
        attachment_repository=Mock(),
        checkpoint_repository=Mock(),
    )

    result = service.sync_initial(
        account_id=1,
        provider_account_id="provider-account-1",
    )

    assert result == {
        "messages_synced": 0,
        "pages_synced": 1,
    }

    assert provider.calls == [
        ("provider-account-1", None, 25),
    ]


class DuplicateInitialSyncProvider(PaginatedEmailSyncProvider):
    def sync_page(
        self,
        account_id: str,
        cursor: str | None = None,
        max_results: int = 25,
    ) -> SyncPage:
        if cursor is None:
            return SyncPage(
                messages=[
                    {"id": "message-1"},
                ],
                next_cursor="page-2",
            )

        return SyncPage(
            messages=[
                {"id": "message-1"},
            ],
            next_cursor=None,
        )


def test_sync_initial_deduplicates_duplicate_provider_messages():
    provider = DuplicateInitialSyncProvider()
    normalized_provider = FakeNormalizedProvider()

    account = Mock()
    account.id = 1
    account.is_active = True

    account_repository = Mock(spec=EmailAccountRepository)
    account_repository.get_by_id.return_value = account

    thread_repository = Mock()
    message_repository = Mock()
    recipient_repository = Mock(spec=EmailRecipientRepository)
    attachment_repository = Mock()

    existing_message = Mock()
    existing_message.id = 202

    message_repository.get_by_provider_id.side_effect = [
        None,
        existing_message,
    ]

    created_message = Mock()
    created_message.id = 202
    message_repository.create.return_value = created_message
    message_repository.update.return_value = existing_message

    service = InboxSyncService(
        provider=provider,
        normalized_provider=normalized_provider,
        account_repository=account_repository,
        thread_repository=thread_repository,
        message_repository=message_repository,
        recipient_repository=recipient_repository,
        attachment_repository=attachment_repository,
        checkpoint_repository=Mock(),
    )

    result = service.sync_initial(
        account_id=1,
        provider_account_id="provider-account-1",
    )

    assert result == {
        "messages_synced": 2,
        "pages_synced": 2,
    }

    assert message_repository.get_by_provider_id.call_count == 2
    message_repository.create.assert_called_once()
    message_repository.update.assert_called_once()


def test_persist_message_without_thread_id_remains_unthreaded():
    message_repository = Mock()
    recipient_repository = Mock(spec=EmailRecipientRepository)
    recipient_repository.get_by_identity.return_value = None
    thread_repository = Mock()
    attachment_repository = Mock()

    persisted_message = Mock()
    persisted_message.id = 505

    message_repository.get_by_provider_id.return_value = None
    message_repository.create.return_value = persisted_message

    service = InboxSyncService(
        provider=FakeSyncProvider(),
        normalized_provider=Mock(spec=NormalizedEmailProvider),
        account_repository=Mock(spec=EmailAccountRepository),
        thread_repository=thread_repository,
        message_repository=message_repository,
        recipient_repository=recipient_repository,
        attachment_repository=attachment_repository,
        checkpoint_repository=Mock(),
    )

    message = EmailMessage(
        provider="gmail",
        account_id="provider-account-1",
        message_id="message-no-thread",
        sender=EmailAddress(email="sender@example.com"),
        subject="No thread",
        body_text="This message has no provider thread ID.",
    )

    result = service.persist_message(
        account_id=1,
        message=message,
    )

    assert result is persisted_message

    thread_repository.get_by_provider_id.assert_not_called()
    thread_repository.create.assert_not_called()
    thread_repository.update.assert_not_called()

    message_repository.create.assert_called_once_with(
        account_id=1,
        provider="gmail",
        provider_message_id="message-no-thread",
        sender_name=None,
        sender_email="sender@example.com",
        subject="No thread",
        body_text="This message has no provider thread ID.",
        received_at=None,
        is_read=False,
        has_attachments=False,
        thread_id=None,
    )


class IncrementalSyncProvider(PaginatedEmailSyncProvider, IncrementalEmailSyncProvider):
    def __init__(self):
        self.calls = []

    def sync_page(
        self,
        account_id: str,
        cursor: str | None = None,
        max_results: int = 25,
    ) -> SyncPage:
        raise NotImplementedError

    def sync_changes(
        self,
        account_id: str,
        checkpoint_cursor: str | None = None,
        page_cursor: str | None = None,
        max_results: int = 25,
    ):
        from app.schemas.sync import SyncChanges, SyncChange

        self.calls.append(
            (
                account_id,
                checkpoint_cursor,
                page_cursor,
                max_results,
            )
        )

        return SyncChanges(
            changes=[
                SyncChange(
                    change_type="upsert",
                    message_id="message-1",
                    message={"id": "message-1"},
                )
            ],
            checkpoint_cursor="checkpoint-2",
            has_more=False,
        )


def test_sync_incremental_fetches_full_message_for_upsert():
    provider = IncrementalSyncProvider()

    account = Mock()
    account.id = 1
    account.is_active = True
    account.provider = "gmail"

    account_repository = Mock(spec=EmailAccountRepository)
    account_repository.get_by_id.return_value = account

    checkpoint = Mock()
    checkpoint.sync_cursor = "checkpoint-1"

    checkpoint_repository = Mock()
    checkpoint_repository.get_or_create.return_value = checkpoint

    normalized_provider = Mock(spec=NormalizedEmailProvider)
    normalized_provider.get_message.return_value = {
        "id": "message-1",
        "threadId": "thread-1",
        "full": "message",
    }

    normalized_message = EmailMessage(
        provider="gmail",
        account_id="provider-account-1",
        message_id="message-1",
        sender=EmailAddress(email="sender@example.com"),
        subject="Test",
    )
    normalized_provider.normalize_message.return_value = normalized_message

    message_repository = Mock()
    message_repository.get_by_provider_id.return_value = None

    service = InboxSyncService(
        provider=provider,
        normalized_provider=normalized_provider,
        account_repository=account_repository,
        thread_repository=Mock(),
        message_repository=message_repository,
        recipient_repository=Mock(spec=EmailRecipientRepository),
        attachment_repository=Mock(),
        checkpoint_repository=checkpoint_repository,
    )

    service.persist_message = Mock()

    result = service.sync_incremental(
        account_id=1,
        provider_account_id="provider-account-1",
    )

    assert result == {
        "changes_processed": 1,
        "messages_synced": 1,
        "messages_deleted": 0,
        "pages_synced": 1,
    }

    normalized_provider.get_message.assert_called_once_with(
        account_id="provider-account-1",
        message_id="message-1",
    )

    normalized_provider.normalize_message.assert_called_once_with(
        account_id="provider-account-1",
        raw_message={
            "id": "message-1",
            "threadId": "thread-1",
            "full": "message",
        },
    )

    service.persist_message.assert_called_once_with(
        account_id=1,
        message=normalized_message,
    )

    checkpoint_repository.mark_success.assert_called_once_with(
        checkpoint,
        sync_cursor="checkpoint-2",
    )


def test_sync_incremental_soft_deletes_existing_message():
    provider = IncrementalSyncProvider()

    account = Mock()
    account.id = 1
    account.is_active = True
    account.provider = "gmail"

    account_repository = Mock(spec=EmailAccountRepository)
    account_repository.get_by_id.return_value = account

    checkpoint = Mock()
    checkpoint.sync_cursor = "checkpoint-1"

    checkpoint_repository = Mock()
    checkpoint_repository.get_or_create.return_value = checkpoint

    existing_message = Mock()
    message_repository = Mock()
    message_repository.get_by_provider_id.return_value = existing_message

    provider.sync_changes = Mock(
        return_value=__import__("app.schemas.sync", fromlist=["SyncChanges"]).SyncChanges(
            changes=[
                __import__("app.schemas.sync", fromlist=["SyncChange"]).SyncChange(
                    change_type="delete",
                    message_id="message-1",
                )
            ],
            checkpoint_cursor="checkpoint-2",
            has_more=False,
        )
    )

    service = InboxSyncService(
        provider=provider,
        normalized_provider=Mock(spec=NormalizedEmailProvider),
        account_repository=account_repository,
        thread_repository=Mock(),
        message_repository=message_repository,
        recipient_repository=Mock(spec=EmailRecipientRepository),
        attachment_repository=Mock(),
        checkpoint_repository=checkpoint_repository,
    )

    result = service.sync_incremental(
        account_id=1,
        provider_account_id="provider-account-1",
    )

    assert result == {
        "changes_processed": 1,
        "messages_synced": 0,
        "messages_deleted": 1,
        "pages_synced": 1,
    }

    message_repository.mark_deleted.assert_called_once_with(
        existing_message,
    )

    checkpoint_repository.mark_success.assert_called_once_with(
        checkpoint,
        sync_cursor="checkpoint-2",
    )


def test_sync_incremental_uses_page_cursor_and_advances_checkpoint_only_from_provider():
    provider = IncrementalSyncProvider()

    account = Mock()
    account.id = 1
    account.is_active = True
    account.provider = "gmail"

    account_repository = Mock(spec=EmailAccountRepository)
    account_repository.get_by_id.return_value = account

    checkpoint = Mock()
    checkpoint.sync_cursor = "checkpoint-1"

    checkpoint_repository = Mock()
    checkpoint_repository.get_or_create.return_value = checkpoint

    provider.sync_changes = Mock(
        side_effect=[
            __import__("app.schemas.sync", fromlist=["SyncChanges"]).SyncChanges(
                changes=[],
                next_cursor="page-2",
                checkpoint_cursor=None,
                has_more=True,
            ),
            __import__("app.schemas.sync", fromlist=["SyncChanges"]).SyncChanges(
                changes=[],
                next_cursor=None,
                checkpoint_cursor="checkpoint-2",
                has_more=False,
            ),
        ]
    )

    service = InboxSyncService(
        provider=provider,
        normalized_provider=Mock(spec=NormalizedEmailProvider),
        account_repository=account_repository,
        thread_repository=Mock(),
        message_repository=Mock(),
        recipient_repository=Mock(spec=EmailRecipientRepository),
        attachment_repository=Mock(),
        checkpoint_repository=checkpoint_repository,
    )

    result = service.sync_incremental(
        account_id=1,
        provider_account_id="provider-account-1",
        max_results=10,
    )

    assert result == {
        "changes_processed": 0,
        "messages_synced": 0,
        "messages_deleted": 0,
        "pages_synced": 2,
    }

    assert provider.sync_changes.call_args_list == [
        __import__("unittest.mock", fromlist=["call"]).call(
            account_id="provider-account-1",
            checkpoint_cursor="checkpoint-1",
            page_cursor=None,
            max_results=10,
        ),
        __import__("unittest.mock", fromlist=["call"]).call(
            account_id="provider-account-1",
            checkpoint_cursor="checkpoint-1",
            page_cursor="page-2",
            max_results=10,
        ),
    ]

    checkpoint_repository.mark_success.assert_called_once_with(
        checkpoint,
        sync_cursor="checkpoint-2",
    )


def test_sync_incremental_marks_checkpoint_error_and_preserves_cursor_on_failure():
    provider = IncrementalSyncProvider()

    account = Mock()
    account.id = 1
    account.is_active = True
    account.provider = "gmail"

    account_repository = Mock(spec=EmailAccountRepository)
    account_repository.get_by_id.return_value = account

    checkpoint = Mock()
    checkpoint.sync_cursor = "checkpoint-1"

    checkpoint_repository = Mock()
    checkpoint_repository.get_or_create.return_value = checkpoint

    provider.sync_changes = Mock(
        side_effect=RuntimeError("provider sync failed")
    )

    service = InboxSyncService(
        provider=provider,
        normalized_provider=Mock(spec=NormalizedEmailProvider),
        account_repository=account_repository,
        thread_repository=Mock(),
        message_repository=Mock(),
        recipient_repository=Mock(spec=EmailRecipientRepository),
        attachment_repository=Mock(),
        checkpoint_repository=checkpoint_repository,
    )

    try:
        service.sync_incremental(
            account_id=1,
            provider_account_id="provider-account-1",
        )
    except RuntimeError as exc:
        assert str(exc) == "provider sync failed"
    else:
        raise AssertionError("Expected RuntimeError was not raised.")

    checkpoint_repository.mark_started.assert_called_once_with(
        checkpoint,
    )

    checkpoint_repository.mark_error.assert_called_once_with(
        checkpoint,
        error_message="provider sync failed",
    )

    checkpoint_repository.mark_success.assert_not_called()
