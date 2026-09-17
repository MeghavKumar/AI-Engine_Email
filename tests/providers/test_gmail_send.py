import base64
from email import message_from_bytes

import pytest

from app.providers.email.gmail import GmailProvider


class FakeSendRequest:
    def __init__(self, response):
        self.response = response

    def execute(self):
        return self.response


class FakeMessages:
    def __init__(self):
        self.last_body = None

    def send(self, userId, body):
        self.last_body = body
        return FakeSendRequest({"id": "gmail-message-001"})


class FakeUsers:
    def __init__(self):
        self.messages_api = FakeMessages()

    def messages(self):
        return self.messages_api


class FakeGmailService:
    def __init__(self):
        self.users_api = FakeUsers()

    def users(self):
        return self.users_api


def make_provider():
    provider = object.__new__(GmailProvider)
    provider.credentials = None
    provider.service = FakeGmailService()
    return provider


def test_send_message_builds_gmail_message():
    provider = make_provider()

    message_id = provider.send_message(
        account_id="account-001",
        message={
            "to": ["recipient@example.com"],
            "cc": ["copy@example.com"],
            "bcc": ["blind@example.com"],
            "subject": "Test email",
            "body": "Hello from the AI Email Engine.",
        },
    )

    assert message_id == "gmail-message-001"

    request_body = (
        provider.service
        .users_api
        .messages_api
        .last_body
    )

    assert request_body["raw"]

    decoded = base64.urlsafe_b64decode(
        request_body["raw"]
    )

    parsed = message_from_bytes(decoded)

    assert parsed["To"] == "recipient@example.com"
    assert parsed["Cc"] == "copy@example.com"
    assert parsed["Bcc"] == "blind@example.com"
    assert parsed["Subject"] == "Test email"
    assert parsed.get_payload().strip() == (
        "Hello from the AI Email Engine."
    )


def test_send_message_requires_recipient():
    provider = make_provider()

    with pytest.raises(
        ValueError,
        match="At least one recipient is required",
    ):
        provider.send_message(
            account_id="account-001",
            message={
                "subject": "No recipient",
                "body": "This must not be sent.",
            },
        )

    assert (
        provider.service
        .users_api
        .messages_api
        .last_body
        is None
    )
