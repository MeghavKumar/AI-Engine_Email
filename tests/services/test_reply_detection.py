from app.services.reply_detection import ReplyDetectionService


ACCOUNT_EMAIL = "meghav27071982@gmail.com"


class FakeEmailProvider:
    def __init__(self, messages):
        self.messages = messages

    def get_thread(self, account_id, thread_id):
        return self.messages


def test_detect_reply_and_propose_reply_to_sender():
    provider = FakeEmailProvider(
        [
            {
                "id": "sent-123",
                "payload": {
                    "headers": [
                        {
                            "name": "From",
                            "value": ACCOUNT_EMAIL,
                        }
                    ]
                },
            },
            {
                "id": "reply-456",
                "payload": {
                    "headers": [
                        {
                            "name": "From",
                            "value": "person@example.com",
                        },
                        {
                            "name": "To",
                            "value": ACCOUNT_EMAIL,
                        },
                        {
                            "name": "Cc",
                            "value": "colleague@example.com",
                        },
                    ]
                },
            },
        ]
    )

    service = ReplyDetectionService(provider)

    result = service.detect_reply(
        account_id=ACCOUNT_EMAIL,
        thread_id="thread-123",
        account_email=ACCOUNT_EMAIL,
    )

    assert result.replied is True
    assert result.reply_message_id == "reply-456"
    assert result.reply_from == "person@example.com"
    assert result.reply_to == [ACCOUNT_EMAIL]
    assert result.reply_cc == ["colleague@example.com"]
    assert result.suggested_reply_to == ["person@example.com"]
    assert result.suggested_reply_cc == ["colleague@example.com"]
    assert result.requires_recipient_confirmation is True


def test_no_reply_when_all_messages_are_from_account():
    provider = FakeEmailProvider(
        [
            {
                "id": "sent-123",
                "payload": {
                    "headers": [
                        {
                            "name": "From",
                            "value": ACCOUNT_EMAIL,
                        }
                    ]
                },
            }
        ]
    )

    service = ReplyDetectionService(provider)

    result = service.detect_reply(
        account_id=ACCOUNT_EMAIL,
        thread_id="thread-123",
        account_email=ACCOUNT_EMAIL,
    )

    assert result.replied is False
    assert result.reply_message_id is None
    assert result.reply_from is None
    assert result.suggested_reply_to == []
    assert result.suggested_reply_cc == []
    assert result.requires_recipient_confirmation is True


def test_detect_reply_email_address_case_insensitively():
    provider = FakeEmailProvider(
        [
            {
                "id": "sent-123",
                "payload": {
                    "headers": [
                        {
                            "name": "From",
                            "value": "MEGHAV27071982@GMAIL.COM",
                        }
                    ]
                },
            },
            {
                "id": "reply-456",
                "payload": {
                    "headers": [
                        {
                            "name": "From",
                            "value": "person@example.com",
                        },
                        {
                            "name": "To",
                            "value": ACCOUNT_EMAIL,
                        },
                    ]
                },
            },
        ]
    )

    service = ReplyDetectionService(provider)

    result = service.detect_reply(
        account_id=ACCOUNT_EMAIL,
        thread_id="thread-123",
        account_email=ACCOUNT_EMAIL,
    )

    assert result.replied is True
    assert result.reply_message_id == "reply-456"
    assert result.reply_from == "person@example.com"
    assert result.suggested_reply_to == ["person@example.com"]
    assert result.suggested_reply_cc == []
    assert result.requires_recipient_confirmation is True
