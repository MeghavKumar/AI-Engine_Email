from app.providers.email.gmail import GmailProvider
from app.providers.email.gmail_auth import GmailAuth


def test_gmail_list_messages():
    credentials = GmailAuth().authenticate()
    provider = GmailProvider(credentials)

    messages = provider.list_messages(
        account_id="meghav27071982@gmail.com",
        max_results=5,
    )

    assert isinstance(messages, list)

    for message in messages:
        assert "id" in message
        assert "threadId" in message
