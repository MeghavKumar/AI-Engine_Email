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


def test_send_message_supports_multiple_attachments(tmp_path):
    provider = make_provider()

    report_v1 = tmp_path / "Quarterly_Report_v1.pdf"
    report_v2 = tmp_path / "Quarterly_Report_v2.pdf"
    invoice = tmp_path / "Invoice.xlsx"

    report_v1.write_bytes(b"report version 1")
    report_v2.write_bytes(b"report version 2")
    invoice.write_bytes(b"invoice contents")

    from app.schemas.email_attachment import EmailAttachment

    message_id = provider.send_message(
        account_id="account-001",
        message={
            "to": ["recipient@example.com"],
            "subject": "Documents",
            "body": "Please find the documents attached.",
            "attachments": [
                EmailAttachment(
                    filename="Quarterly_Report_v1.pdf",
                    content_type="application/pdf",
                    file_path=report_v1,
                ),
                EmailAttachment(
                    filename="Quarterly_Report_v2.pdf",
                    content_type="application/pdf",
                    file_path=report_v2,
                ),
                EmailAttachment(
                    filename="Invoice.xlsx",
                    content_type=(
                        "application/vnd.openxmlformats-officedocument"
                        ".spreadsheetml.sheet"
                    ),
                    file_path=invoice,
                ),
            ],
        },
    )

    assert message_id == "gmail-message-001"

    request_body = (
        provider.service
        .users_api
        .messages_api
        .last_body
    )

    decoded = base64.urlsafe_b64decode(
        request_body["raw"]
    )

    parsed = message_from_bytes(decoded)

    assert parsed.is_multipart()

    attachments = [
        part
        for part in parsed.walk()
        if part.get_filename()
    ]

    assert len(attachments) == 3

    filenames = {
        part.get_filename()
        for part in attachments
    }

    assert filenames == {
        "Quarterly_Report_v1.pdf",
        "Quarterly_Report_v2.pdf",
        "Invoice.xlsx",
    }

    contents = {
        part.get_filename(): part.get_payload(
            decode=True
        )
        for part in attachments
    }

    assert contents["Quarterly_Report_v1.pdf"] == (
        b"report version 1"
    )

    assert contents["Quarterly_Report_v2.pdf"] == (
        b"report version 2"
    )

    assert contents["Invoice.xlsx"] == (
        b"invoice contents"
    )
