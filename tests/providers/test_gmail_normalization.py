from app.providers.email.gmail import GmailProvider
from app.providers.email.gmail_auth import GmailAuth
from app.schemas.provider import EmailMessage


def test_gmail_message_normalization():
    credentials = GmailAuth().authenticate()
    provider = GmailProvider(credentials)

    messages = provider.list_messages(
        account_id="meghav27071982@gmail.com",
        max_results=1,
    )

    assert messages

    raw_message = provider.get_message(
        account_id="meghav27071982@gmail.com",
        message_id=messages[0]["id"],
    )

    normalized = provider.normalize_message(
        account_id="meghav27071982@gmail.com",
        raw_message=raw_message,
    )

    assert isinstance(normalized, EmailMessage)
    assert normalized.provider == "gmail"
    assert normalized.account_id == "meghav27071982@gmail.com"
    assert normalized.message_id
    assert normalized.sender.email
    assert isinstance(normalized.subject, str)
    assert isinstance(normalized.body_text, str)
    assert isinstance(normalized.recipients, list)
    assert isinstance(normalized.cc, list)
    assert isinstance(normalized.labels, list)
