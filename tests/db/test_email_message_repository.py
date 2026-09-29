from datetime import datetime, timezone

from app.db.repositories.email_message import EmailMessageRepository
from app.db.session import SessionLocal


def test_create_and_get_by_provider_id():
    with SessionLocal() as session:
        repository = EmailMessageRepository(session)

        message = repository.create(
            account_id=1,
            provider="gmail",
            provider_message_id="repository-gmail-message-1",
            sender_name="Alice",
            sender_email="alice@example.com",
            subject="Hello",
            body_text="Test message",
            received_at=datetime.now(timezone.utc),
            is_read=False,
            has_attachments=False,
        )

        try:
            session.commit()

            assert message.id is not None

            found = repository.get_by_provider_id(
                account_id=1,
                provider="gmail",
                provider_message_id="repository-gmail-message-1",
            )

            assert found is message
        finally:
            session.delete(message)
            session.commit()


def test_get_by_provider_id_returns_none_for_different_provider():
    with SessionLocal() as session:
        repository = EmailMessageRepository(session)

        message = repository.create(
            account_id=1,
            provider="gmail",
            provider_message_id="repository-same-id",
            sender_name=None,
            sender_email="alice@example.com",
            subject="Hello",
            body_text="Test",
            received_at=None,
            is_read=False,
            has_attachments=False,
        )

        try:
            session.commit()

            found = repository.get_by_provider_id(
                account_id=1,
                provider="outlook",
                provider_message_id="repository-same-id",
            )

            assert found is None
        finally:
            session.delete(message)
            session.commit()


def test_update_changes_message_fields():
    with SessionLocal() as session:
        repository = EmailMessageRepository(session)

        message = repository.create(
            account_id=1,
            provider="gmail",
            provider_message_id="repository-gmail-message-2",
            sender_name="Alice",
            sender_email="alice@example.com",
            subject="Old subject",
            body_text="Old body",
            received_at=None,
            is_read=False,
            has_attachments=False,
        )

        try:
            session.commit()

            updated = repository.update(
                message,
                sender_name="Alice Smith",
                sender_email="alice@example.com",
                subject="New subject",
                body_text="New body",
                received_at=None,
                is_read=True,
                has_attachments=True,
            )

            session.commit()

            assert updated is message
            assert message.sender_name == "Alice Smith"
            assert message.subject == "New subject"
            assert message.body_text == "New body"
            assert message.is_read is True
            assert message.has_attachments is True
        finally:
            session.delete(message)
            session.commit()

def test_mark_deleted_and_restore():
    with SessionLocal() as session:
        repository = EmailMessageRepository(session)

        message = repository.create(
            account_id=1,
            provider="gmail",
            provider_message_id="repository-gmail-soft-delete-1",
            sender_name="Alice",
            sender_email="alice@example.com",
            subject="Soft delete test",
            body_text="Test",
            received_at=None,
            is_read=False,
            has_attachments=False,
        )

        try:
            session.commit()

            assert message.is_deleted is False

            deleted = repository.mark_deleted(message)
            session.commit()

            assert deleted is message
            assert message.is_deleted is True

            restored = repository.restore(message)
            session.commit()

            assert restored is message
            assert message.is_deleted is False
        finally:
            session.delete(message)
            session.commit()
