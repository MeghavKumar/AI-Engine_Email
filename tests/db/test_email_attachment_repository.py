from app.db.repositories.email_attachment import EmailAttachmentRepository
from app.db.session import SessionLocal
from app.models.email_account import EmailAccount
from app.models.email_attachment import EmailAttachment
from app.models.email_message import EmailMessageRecord


def test_create_attachment_persists_metadata():
    session = SessionLocal()

    try:
        account = EmailAccount(
            user_id="user-1",
            provider="gmail",
            email_address="attachment@example.com",
            provider_account_id="provider-account-1",
        )
        session.add(account)
        session.flush()

        message = EmailMessageRecord(
            account_id=account.id,
            provider="gmail",
            provider_message_id="attachment-message-1",
            sender_name="Sender",
            sender_email="sender@example.com",
            subject="Attachment",
            body_text="See attached.",
        )
        session.add(message)
        session.flush()

        repository = EmailAttachmentRepository(session)

        attachment = repository.create(
            message_id=message.id,
            provider_attachment_id="attachment-1",
            filename="report.pdf",
            content_type="application/pdf",
            size_bytes=12345,
            is_inline=False,
        )

        session.commit()

        assert attachment.id is not None
        assert attachment.message_id == message.id
        assert attachment.provider_attachment_id == "attachment-1"
        assert attachment.filename == "report.pdf"
        assert attachment.content_type == "application/pdf"
        assert attachment.size_bytes == 12345
        assert attachment.is_inline is False

    finally:
        session.rollback()
        session.close()


def test_get_by_identity_returns_existing_attachment():
    session = SessionLocal()

    try:
        account = EmailAccount(
            user_id="user-2",
            provider="gmail",
            email_address="lookup-attachment@example.com",
            provider_account_id="provider-account-2",
        )
        session.add(account)
        session.flush()

        message = EmailMessageRecord(
            account_id=account.id,
            provider="gmail",
            provider_message_id="lookup-attachment-message-1",
            sender_name="Sender",
            sender_email="sender@example.com",
            subject="Lookup attachment",
            body_text="Hello",
        )
        session.add(message)
        session.flush()

        repository = EmailAttachmentRepository(session)

        created = repository.create(
            message_id=message.id,
            provider_attachment_id="lookup-attachment-1",
            filename="invoice.pdf",
            content_type="application/pdf",
            size_bytes=5000,
            is_inline=False,
        )

        session.commit()

        found = repository.get_by_identity(
            message_id=message.id,
            provider_attachment_id="lookup-attachment-1",
        )

        assert found is not None
        assert found.id == created.id
        assert found.filename == "invoice.pdf"

    finally:
        session.rollback()
        session.close()
