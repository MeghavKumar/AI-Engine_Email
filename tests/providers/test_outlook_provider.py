import httpx

from app.providers.email.outlook import OutlookProvider
from app.schemas.provider import EmailMessage


def make_client(handler):
    return httpx.Client(
        transport=httpx.MockTransport(handler),
        base_url=OutlookProvider.GRAPH_BASE_URL,
    )


def test_outlook_list_messages():
    def handler(request):
        assert request.url.path == (
            "/v1.0/users/test@example.com/mailFolders/inbox/messages"
        )
        assert request.url.params["$top"] == "5"
        assert request.url.params["$orderby"] == "receivedDateTime DESC"

        return httpx.Response(
            200,
            json={
                "value": [
                    {"id": "message-1"},
                    {"id": "message-2"},
                ]
            },
        )

    provider = OutlookProvider(
        access_token="test-token",
        client=make_client(handler),
    )

    messages = provider.list_messages(
        account_id="test@example.com",
        max_results=5,
    )

    assert messages == [
        {"id": "message-1"},
        {"id": "message-2"},
    ]


def test_outlook_get_message():
    def handler(request):
        assert request.url.path == (
            "/v1.0/users/test@example.com/messages/message-1"
        )
        assert request.headers["Authorization"] == "Bearer test-token"

        return httpx.Response(
            200,
            json={"id": "message-1", "subject": "Test subject"},
        )

    provider = OutlookProvider(
        access_token="test-token",
        client=make_client(handler),
    )

    message = provider.get_message(
        account_id="test@example.com",
        message_id="message-1",
    )

    assert message["id"] == "message-1"
    assert message["subject"] == "Test subject"


def test_outlook_get_thread():
    def handler(request):
        assert request.url.path == (
            "/v1.0/users/test@example.com/messages"
        )
        assert request.url.params["$filter"] == (
            "conversationId eq 'conversation-1'"
        )
        assert request.url.params["$orderby"] == (
            "receivedDateTime ASC"
        )

        return httpx.Response(
            200,
            json={
                "value": [
                    {"id": "message-1"},
                    {"id": "message-2"},
                ]
            },
        )

    provider = OutlookProvider(
        access_token="test-token",
        client=make_client(handler),
    )

    messages = provider.get_thread(
        account_id="test@example.com",
        thread_id="conversation-1",
    )

    assert messages == [
        {"id": "message-1"},
        {"id": "message-2"},
    ]


def test_outlook_message_normalization():
    provider = OutlookProvider()

    raw_message = {
        "id": "message-1",
        "conversationId": "conversation-1",
        "from": {
            "emailAddress": {
                "name": "Alice",
                "address": "alice@example.com",
            }
        },
        "toRecipients": [
            {
                "emailAddress": {
                    "name": "Bob",
                    "address": "bob@example.com",
                }
            }
        ],
        "ccRecipients": [],
        "subject": "Test subject",
        "body": {
            "contentType": "text",
            "content": "Hello from Outlook.",
        },
        "receivedDateTime": "2026-09-23T14:00:00Z",
        "isRead": False,
        "hasAttachments": True,
    }

    normalized = provider.normalize_message(
        account_id="test@example.com",
        raw_message=raw_message,
    )

    assert isinstance(normalized, EmailMessage)
    assert normalized.provider == "outlook"
    assert normalized.account_id == "test@example.com"
    assert normalized.message_id == "message-1"
    assert normalized.thread_id == "conversation-1"
    assert normalized.sender.email == "alice@example.com"
    assert normalized.sender.name == "Alice"
    assert normalized.recipients[0].email == "bob@example.com"
    assert normalized.subject == "Test subject"
    assert normalized.body_text == "Hello from Outlook."
    assert normalized.received_at is not None
    assert normalized.received_at.tzinfo is not None
    assert normalized.is_read is False
    assert normalized.has_attachments is True


def test_outlook_send_message():
    def handler(request):
        assert request.url.path == (
            "/v1.0/users/test@example.com/sendMail"
        )
        assert request.headers["Authorization"] == "Bearer test-token"

        payload = request.read()
        import json

        body = json.loads(payload)

        assert body["saveToSentItems"] is True

        message = body["message"]

        assert message["subject"] == "Test email"
        assert message["body"] == {
            "contentType": "Text",
            "content": "Hello from Outlook.",
        }

        assert message["toRecipients"] == [
            {
                "emailAddress": {
                    "address": "recipient@example.com"
                }
            }
        ]

        assert message["ccRecipients"] == [
            {
                "emailAddress": {
                    "address": "copy@example.com"
                }
            }
        ]

        assert message["bccRecipients"] == [
            {
                "emailAddress": {
                    "address": "blind@example.com"
                }
            }
        ]

        return httpx.Response(
            202,
            headers={"request-id": "outlook-request-001"},
        )

    provider = OutlookProvider(
        access_token="test-token",
        client=make_client(handler),
    )

    message_id = provider.send_message(
        account_id="test@example.com",
        message={
            "to": ["recipient@example.com"],
            "cc": ["copy@example.com"],
            "bcc": ["blind@example.com"],
            "subject": "Test email",
            "body": "Hello from Outlook.",
        },
    )

    assert message_id == "outlook-request-001"


def test_outlook_send_message_requires_recipient():
    provider = OutlookProvider(
        access_token="test-token",
        client=make_client(
            lambda request: httpx.Response(202)
        ),
    )

    import pytest

    with pytest.raises(
        ValueError,
        match="At least one recipient is required",
    ):
        provider.send_message(
            account_id="test@example.com",
            message={
                "subject": "No recipient",
                "body": "This must not be sent.",
            },
        )


def test_outlook_send_message_supports_attachment(tmp_path):
    attachment_file = tmp_path / "report.pdf"
    attachment_file.write_bytes(b"test report contents")

    def handler(request):
        payload = request.read()
        import json

        body = json.loads(payload)
        attachments = body["message"]["attachments"]

        assert len(attachments) == 1

        attachment = attachments[0]

        assert attachment["@odata.type"] == (
            "#microsoft.graph.fileAttachment"
        )
        assert attachment["name"] == "report.pdf"
        assert attachment["contentType"] == "application/pdf"
        assert attachment["contentBytes"]

        return httpx.Response(
            202,
            headers={"request-id": "outlook-request-002"},
        )

    from app.schemas.email_attachment import EmailAttachment

    provider = OutlookProvider(
        access_token="test-token",
        client=make_client(handler),
    )

    message_id = provider.send_message(
        account_id="test@example.com",
        message={
            "to": ["recipient@example.com"],
            "subject": "Report",
            "body": "Please find the report attached.",
            "attachments": [
                EmailAttachment(
                    filename="report.pdf",
                    content_type="application/pdf",
                    file_path=attachment_file,
                )
            ],
        },
    )

    assert message_id == "outlook-request-002"


def test_outlook_mark_read():
    def handler(request):
        assert request.method == "PATCH"
        assert request.url.path == (
            "/v1.0/users/test@example.com/messages/message-1"
        )
        assert request.headers["Authorization"] == "Bearer test-token"

        import json

        body = json.loads(request.read())

        assert body == {
            "isRead": True,
        }

        return httpx.Response(200)

    provider = OutlookProvider(
        access_token="test-token",
        client=make_client(handler),
    )

    result = provider.mark_read(
        account_id="test@example.com",
        message_id="message-1",
    )

    assert result is None


def test_outlook_archive_message():
    def handler(request):
        assert request.method == "POST"
        assert request.url.path == (
            "/v1.0/users/test@example.com/messages/message-1/move"
        )
        assert request.headers["Authorization"] == "Bearer test-token"

        import json

        body = json.loads(request.read())

        assert body == {
            "destinationId": "archive",
        }

        return httpx.Response(
            201,
            json={
                "id": "message-1",
            },
        )

    provider = OutlookProvider(
        access_token="test-token",
        client=make_client(handler),
    )

    result = provider.archive_message(
        account_id="test@example.com",
        message_id="message-1",
    )

    assert result is None
