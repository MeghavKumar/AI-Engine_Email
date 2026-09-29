from datetime import datetime, timezone

import pytest
from sqlalchemy.exc import IntegrityError

from app.db.session import SessionLocal
from app.models import (
    EmailAccount,
    EmailAttachment,
    EmailMessageRecord,
    EmailRecipient,
    EmailThread,
)


def test_email_thread_persists_and_enforces_provider_identity():
    with SessionLocal() as session:
        account = EmailAccount(
            user_id="user-1",
            provider="gmail",
            email_address="user1@example.com",
        )
        session.add(account)
        session.flush()

        thread = EmailThread(
            account_id=account.id,
            provider="gmail",
            provider_thread_id="thread-123",
            subject="Test thread",
        )
        session.add(thread)
        session.commit()

        assert thread.id is not None
        assert thread.provider_thread_id == "thread-123"

        duplicate = EmailThread(
            account_id=account.id,
            provider="gmail",
            provider_thread_id="thread-123",
            subject="Duplicate thread",
        )
        session.add(duplicate)

        with pytest.raises(IntegrityError):
            session.commit()

        session.rollback()

        session.delete(thread)
        session.flush()

        session.delete(account)
        session.commit()


def test_email_message_persists_with_recipients_and_attachment():
    with SessionLocal() as session:
        account = EmailAccount(
            user_id="user-2",
            provider="gmail",
            email_address="user2@example.com",
        )
        session.add(account)
        session.flush()

        thread = EmailThread(
            account_id=account.id,
            provider="gmail",
            provider_thread_id="thread-456",
            subject="Inbox test",
        )
        session.add(thread)
        session.flush()

        message = EmailMessageRecord(
            account_id=account.id,
            thread_id=thread.id,
            provider="gmail",
            provider_message_id="message-123",
            sender_name="Sender",
            sender_email="sender@example.com",
            subject="Hello",
            body_text="Hello from the inbox.",
            received_at=datetime.now(timezone.utc),
            is_read=False,
            has_attachments=True,
        )
        session.add(message)
        session.flush()

        recipient = EmailRecipient(
            message_id=message.id,
            recipient_type="to",
            name="Recipient",
            email="recipient@example.com",
        )
        cc_recipient = EmailRecipient(
            message_id=message.id,
            recipient_type="cc",
            name="CC Recipient",
            email="cc@example.com",
        )

        attachment = EmailAttachment(
            message_id=message.id,
            provider_attachment_id="attachment-123",
            filename="document.pdf",
            content_type="application/pdf",
            size_bytes=1024,
            is_inline=False,
        )

        session.add_all([
            recipient,
            cc_recipient,
            attachment,
        ])
        session.commit()

        session.refresh(message)

        assert message.id is not None
        assert message.thread_id == thread.id
        assert len(message.recipients) == 2
        assert len(message.attachments) == 1
        assert message.recipients[0].email in {
            "recipient@example.com",
            "cc@example.com",
        }
        assert message.attachments[0].filename == "document.pdf"

        session.delete(message)
        session.flush()

        session.delete(thread)
        session.flush()

        session.delete(account)
        session.commit()


def test_email_message_enforces_provider_identity():
    with SessionLocal() as session:
        account = EmailAccount(
            user_id="user-3",
            provider="outlook",
            email_address="user3@example.com",
        )
        session.add(account)
        session.flush()

        message = EmailMessageRecord(
            account_id=account.id,
            provider="outlook",
            provider_message_id="message-duplicate",
            sender_email="sender@example.com",
        )
        session.add(message)
        session.commit()

        duplicate = EmailMessageRecord(
            account_id=account.id,
            provider="outlook",
            provider_message_id="message-duplicate",
            sender_email="sender@example.com",
        )
        session.add(duplicate)

        with pytest.raises(IntegrityError):
            session.commit()

        session.rollback()

        session.delete(message)
        session.flush()

        session.delete(account)
        session.commit()


def test_email_attachment_enforces_provider_identity():
    with SessionLocal() as session:
        account = EmailAccount(
            user_id="user-4",
            provider="gmail",
            email_address="user4@example.com",
        )
        session.add(account)
        session.flush()

        message = EmailMessageRecord(
            account_id=account.id,
            provider="gmail",
            provider_message_id="message-attachment-test",
            sender_email="sender@example.com",
        )
        session.add(message)
        session.flush()

        attachment = EmailAttachment(
            message_id=message.id,
            provider_attachment_id="attachment-duplicate",
            filename="file.txt",
        )
        session.add(attachment)
        session.commit()

        duplicate = EmailAttachment(
            message_id=message.id,
            provider_attachment_id="attachment-duplicate",
            filename="file-2.txt",
        )
        session.add(duplicate)

        with pytest.raises(IntegrityError):
            session.commit()

        session.rollback()

        session.delete(message)
        session.flush()

        session.delete(account)
        session.commit()
