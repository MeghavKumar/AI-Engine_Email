from app.providers.email.gmail import GmailProvider
from app.providers.email.gmail_auth import GmailAuth
from app.services.reply_detection import ReplyDetectionService


ACCOUNT_EMAIL = "meghav27071982@gmail.com"
THREAD_ID = "1a0ad5f11d7a1fed"


def test_real_gmail_reply_detection():
    credentials = GmailAuth().authenticate()
    provider = GmailProvider(credentials)

    service = ReplyDetectionService(provider)

    result = service.detect_reply(
        account_id=ACCOUNT_EMAIL,
        thread_id=THREAD_ID,
        account_email=ACCOUNT_EMAIL,
    )

    assert result.replied is False
    assert result.reply_message_id is None
    assert result.reply_from is None
    assert result.suggested_reply_to == []
    assert result.suggested_reply_cc == []
    assert result.requires_recipient_confirmation is True
