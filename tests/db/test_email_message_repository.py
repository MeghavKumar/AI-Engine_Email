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



def test_find_by_recipient_email_returns_matching_non_deleted_messages():
    from app.models.email_account import EmailAccount
    from app.models.email_recipient import EmailRecipient

    with SessionLocal() as session:
        repository = EmailMessageRepository(session)

        account = EmailAccount(
            user_id="recipient-search-user",
            provider="gmail",
            email_address="recipient-search@example.com",
            provider_account_id="recipient-search-account",
        )
        session.add(account)
        session.flush()

        message = repository.create(
            account_id=account.id,
            provider="gmail",
            provider_message_id="recipient-search-message-1",
            sender_name="Alice",
            sender_email="alice@example.com",
            subject="Historical email",
            body_text="Hello",
            received_at=datetime.now(timezone.utc),
            is_read=False,
            has_attachments=False,
        )

        recipient = EmailRecipient(
            message_id=message.id,
            recipient_type="to",
            name="John Doe",
            email="John@Example.com",
        )
        session.add(recipient)
        session.commit()

        found = repository.find_by_recipient_email(
            account_id=account.id,
            email="john@example.com",
        )

        assert len(found) == 1
        assert found[0].id == message.id

        repository.mark_deleted(message)
        session.commit()

        found_after_delete = repository.find_by_recipient_email(
            account_id=account.id,
            email="john@example.com",
        )
        assert found_after_delete == []

        session.delete(recipient)
        session.delete(message)
        session.flush()
        session.delete(account)
        session.commit()
