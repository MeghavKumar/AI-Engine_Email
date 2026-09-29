from app.db.repositories.email_account import EmailAccountRepository
from app.db.repositories.email_attachment import EmailAttachmentRepository
from app.db.repositories.email_message import EmailMessageRepository
from app.db.repositories.email_recipient import EmailRecipientRepository
from app.db.repositories.email_sync_checkpoint import EmailSyncCheckpointRepository
from app.db.repositories.email_thread import EmailThreadRepository
from app.models.email_account import EmailAccount
from app.providers.email.normalization import NormalizedEmailProvider
from app.providers.email.sync import (
    IncrementalEmailSyncProvider,
    PaginatedEmailSyncProvider,
)
from app.schemas.provider import EmailMessage
from app.schemas.sync import SyncPage


class InboxSyncService:
    """Provider-independent service for synchronizing an email inbox."""

    def __init__(
        self,
        provider: PaginatedEmailSyncProvider,
        normalized_provider: NormalizedEmailProvider,
        account_repository: EmailAccountRepository,
        thread_repository: EmailThreadRepository,
        message_repository: EmailMessageRepository,
        recipient_repository: EmailRecipientRepository,
        attachment_repository: EmailAttachmentRepository,
        checkpoint_repository: EmailSyncCheckpointRepository,
    ):
        self.provider = provider
        self.normalized_provider = normalized_provider
        self.account_repository = account_repository
        self.thread_repository = thread_repository
        self.message_repository = message_repository
        self.recipient_repository = recipient_repository
        self.attachment_repository = attachment_repository
        self.checkpoint_repository = checkpoint_repository

    def get_account(
        self,
        account_id: int,
    ) -> EmailAccount:
        """Return the connected email account or raise ValueError."""

        account = self.account_repository.get_by_id(account_id)

        if account is None:
            raise ValueError(
                f"Email account {account_id} not found."
            )

        if not account.is_active:
            raise ValueError(
                f"Email account {account_id} is inactive."
            )

        return account

    def fetch_page(
        self,
        account_id: str,
        cursor: str | None = None,
        max_results: int = 25,
    ) -> SyncPage:
        """Fetch one page of inbox messages from the provider."""

        return self.provider.sync_page(
            account_id=account_id,
            cursor=cursor,
            max_results=max_results,
        )

    def sync_initial(
        self,
        *,
        account_id: int,
        provider_account_id: str,
        max_results: int = 25,
    ) -> dict[str, int]:
        """Synchronize the complete provider inbox into local storage."""

        self.get_account(account_id)

        cursor = None
        messages_synced = 0
        pages_synced = 0

        while True:
            page = self.fetch_page(
                account_id=provider_account_id,
                cursor=cursor,
                max_results=max_results,
            )

            pages_synced += 1

            for raw_message in page.messages:
                message_id = raw_message.get("id")

                if not message_id:
                    continue

                message = self.fetch_and_normalize_message(
                    account_id=provider_account_id,
                    message_id=message_id,
                )

                self.persist_message(
                    account_id=account_id,
                    message=message,
                )

                messages_synced += 1

            if page.next_cursor is None:
                break

            cursor = page.next_cursor

        return {
            "messages_synced": messages_synced,
            "pages_synced": pages_synced,
        }

    def sync_incremental(
        self,
        *,
        account_id: int,
        provider_account_id: str,
        max_results: int = 25,
    ) -> dict[str, int]:
        '''Synchronize incremental mailbox changes into local storage.'''

        account = self.get_account(account_id)

        if not isinstance(self.provider, IncrementalEmailSyncProvider):
            raise ValueError(
                f"Provider {account.provider} does not support incremental sync."
            )

        checkpoint = self.checkpoint_repository.get_or_create(
            account_id=account_id,
            provider=account.provider,
        )
        self.checkpoint_repository.mark_started(checkpoint)

        checkpoint_cursor = checkpoint.sync_cursor
        page_cursor = None

        changes_processed = 0
        messages_synced = 0
        messages_deleted = 0
        pages_synced = 0

        try:
            while True:
                changes = self.provider.sync_changes(
                    account_id=provider_account_id,
                    checkpoint_cursor=checkpoint_cursor,
                    page_cursor=page_cursor,
                    max_results=max_results,
                )

                pages_synced += 1

                if changes.checkpoint_cursor is not None:
                    checkpoint_cursor = changes.checkpoint_cursor

                for change in changes.changes:
                    changes_processed += 1

                    existing_message = self.message_repository.get_by_provider_id(
                        account_id=account_id,
                        provider=account.provider,
                        provider_message_id=change.message_id,
                    )

                    if change.change_type == "delete":
                        if existing_message is not None:
                            self.message_repository.mark_deleted(existing_message)
                            messages_deleted += 1
                        continue

                    raw_message = self.normalized_provider.get_message(
                        account_id=provider_account_id,
                        message_id=change.message_id,
                    )

                    message = self.normalized_provider.normalize_message(
                        account_id=provider_account_id,
                        raw_message=raw_message,
                    )

                    self.persist_message(
                        account_id=account_id,
                        message=message,
                    )

                    messages_synced += 1

                if not changes.has_more:
                    break

                page_cursor = changes.next_cursor

                if page_cursor is None:
                    raise ValueError(
                        "Incremental sync reported more pages but no next cursor."
                    )

            self.checkpoint_repository.mark_success(
                checkpoint,
                sync_cursor=checkpoint_cursor,
            )

        except Exception as exc:
            self.checkpoint_repository.mark_error(
                checkpoint,
                error_message=str(exc),
            )
            raise

        return {
            "changes_processed": changes_processed,
            "messages_synced": messages_synced,
            "messages_deleted": messages_deleted,
            "pages_synced": pages_synced,
        }


    def persist_message(
        self,
        *,
        account_id: int,
        message: EmailMessage,
    ):
        """Persist one normalized email message and its recipients."""

        existing_message = self.message_repository.get_by_provider_id(
            account_id=account_id,
            provider=message.provider,
            provider_message_id=message.message_id,
        )

        persisted_thread_id = None

        if message.thread_id:
            thread = self.thread_repository.get_by_provider_id(
                account_id=account_id,
                provider=message.provider,
                provider_thread_id=message.thread_id,
            )

            if thread is None:
                thread = self.thread_repository.create(
                    account_id=account_id,
                    provider=message.provider,
                    provider_thread_id=message.thread_id,
                    subject=message.subject,
                )
            else:
                self.thread_repository.update(
                    thread,
                    subject=message.subject,
                )

            persisted_thread_id = thread.id

        if existing_message is None:
            persisted_message = self.message_repository.create(
                account_id=account_id,
                provider=message.provider,
                provider_message_id=message.message_id,
                sender_name=message.sender.name,
                sender_email=str(message.sender.email),
                subject=message.subject,
                body_text=message.body_text,
                received_at=message.received_at,
                is_read=message.is_read,
                has_attachments=message.has_attachments,
                thread_id=persisted_thread_id,
            )
        else:
            persisted_message = self.message_repository.update(
                existing_message,
                sender_name=message.sender.name,
                sender_email=str(message.sender.email),
                subject=message.subject,
                body_text=message.body_text,
                received_at=message.received_at,
                is_read=message.is_read,
                has_attachments=message.has_attachments,
                thread_id=persisted_thread_id,
            )

        self.persist_recipients(
            message=message,
            persisted_message_id=persisted_message.id,
        )

        self.persist_attachments(
            message=message,
            persisted_message_id=persisted_message.id,
        )

        return persisted_message

    def persist_recipients(
        self,
        message: EmailMessage,
        persisted_message_id: int,
    ) -> None:
        """Persist recipients from a normalized email message idempotently."""

        for recipient in message.recipients:
            email = str(recipient.email)

            existing_recipient = self.recipient_repository.get_by_identity(
                message_id=persisted_message_id,
                recipient_type="to",
                email=email,
            )

            if existing_recipient is None:
                self.recipient_repository.create(
                    message_id=persisted_message_id,
                    recipient_type="to",
                    name=recipient.name,
                    email=email,
                )

        for recipient in message.cc:
            email = str(recipient.email)

            existing_recipient = self.recipient_repository.get_by_identity(
                message_id=persisted_message_id,
                recipient_type="cc",
                email=email,
            )

            if existing_recipient is None:
                self.recipient_repository.create(
                    message_id=persisted_message_id,
                    recipient_type="cc",
                    name=recipient.name,
                    email=email,
                )

    def persist_attachments(
        self,
        message: EmailMessage,
        persisted_message_id: int,
    ) -> None:
        """Persist attachment metadata from a normalized email message idempotently."""

        for attachment in message.attachments:
            existing_attachment = self.attachment_repository.get_by_identity(
                message_id=persisted_message_id,
                provider_attachment_id=attachment.provider_attachment_id,
            )

            if existing_attachment is None:
                self.attachment_repository.create(
                    message_id=persisted_message_id,
                    provider_attachment_id=attachment.provider_attachment_id,
                    filename=attachment.filename,
                    content_type=attachment.content_type,
                    size_bytes=attachment.size_bytes,
                    is_inline=attachment.is_inline,
                )

    def fetch_and_normalize_message(
        self,
        account_id: str,
        message_id: str,
    ) -> EmailMessage:
        """Fetch one provider message and normalize it."""

        raw_message = self.normalized_provider.get_message(
            account_id=account_id,
            message_id=message_id,
        )

        return self.normalized_provider.normalize_message(
            account_id=account_id,
            raw_message=raw_message,
        )
