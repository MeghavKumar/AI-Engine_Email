from app.schemas.provider import EmailAddress, EmailMessage


def test_email_message_schema():
    message = EmailMessage(
        provider="gmail",
        account_id="test-account",
        message_id="message-123",
        thread_id="thread-456",
        sender=EmailAddress(
            name="Test Sender",
            email="sender@example.com",
        ),
        recipients=[
            EmailAddress(
                name="Test Recipient",
                email="recipient@example.com",
            )
        ],
        subject="Test email",
        body_text="This is a test email.",
    )

    assert message.provider == "gmail"
    assert message.message_id == "message-123"
    assert message.sender.email == "sender@example.com"
    assert len(message.recipients) == 1
    assert message.subject == "Test email"
