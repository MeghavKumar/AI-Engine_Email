from app.db.repositories.email_recipient import EmailRecipientRepository
from app.db.session import SessionLocal
from app.models.email_account import EmailAccount
from app.models.email_message import EmailMessageRecord


def test_create_recipient_persists_record():
    session = SessionLocal()

    try:
        account = EmailAccount(
            user_id="user-1",
            provider="gmail",
            email_address="user@example.com",
            provider_account_id="provider-account-1",
        )
        session.add(account)
        session.flush()

        message = EmailMessageRecord(
            account_id=account.id,
            provider="gmail",
            provider_message_id="message-1",
            sender_name="Sender",
            sender_email="sender@example.com",
            subject="Test",
            body_text="Hello",
        )
        session.add(message)
        session.flush()

        repository = EmailRecipientRepository(session)

        recipient = repository.create(
            message_id=message.id,
            recipient_type="to",
            name="Recipient",
            email="recipient@example.com",
        )

        session.commit()

        assert recipient.id is not None
        assert recipient.message_id == message.id
        assert recipient.recipient_type == "to"
        assert recipient.name == "Recipient"
        assert recipient.email == "recipient@example.com"

    finally:
        session.rollback()
        session.close()


def test_get_by_identity_returns_existing_recipient():
    session = SessionLocal()

    try:
        account = EmailAccount(
            user_id="user-2",
            provider="gmail",
            email_address="lookup@example.com",
            provider_account_id="provider-account-2",
        )
        session.add(account)
        session.flush()

        message = EmailMessageRecord(
            account_id=account.id,
            provider="gmail",
            provider_message_id="lookup-message-1",
            sender_name="Sender",
            sender_email="sender@example.com",
            subject="Lookup",
            body_text="Hello",
        )
        session.add(message)
        session.flush()

        repository = EmailRecipientRepository(session)

        created = repository.create(
            message_id=message.id,
            recipient_type="to",
            name="Recipient",
            email="lookup-recipient@example.com",
        )

        session.commit()

        found = repository.get_by_identity(
            message_id=message.id,
            recipient_type="to",
            email="lookup-recipient@example.com",
        )

        assert found is not None
        assert found.id == created.id
        assert found.email == "lookup-recipient@example.com"

    finally:
        session.rollback()
        session.close()
