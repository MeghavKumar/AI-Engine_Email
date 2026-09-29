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


def test_outlook_sync_page_initial_page():
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
                    {
                        "id": "message-1",
                        "conversationId": "conversation-1",
                    }
                ],
                "@odata.nextLink": (
                    "https://graph.microsoft.com/v1.0/"
                    "users/test@example.com/mailFolders/inbox/messages"
                    "?$skiptoken=page-2"
                ),
            },
        )

    provider = OutlookProvider(
        access_token="test-token",
        client=make_client(handler),
    )

    page = provider.sync_page(
        account_id="test@example.com",
        max_results=5,
    )

    assert page.messages == [
        {
            "id": "message-1",
            "conversationId": "conversation-1",
        }
    ]
    assert page.next_cursor == (
        "https://graph.microsoft.com/v1.0/"
        "users/test@example.com/mailFolders/inbox/messages"
        "?$skiptoken=page-2"
    )


def test_outlook_sync_page_uses_next_link():
    next_link = (
        "https://graph.microsoft.com/v1.0/"
        "users/test@example.com/mailFolders/inbox/messages"
        "?$skiptoken=page-2"
    )

    def handler(request):
        assert request.url.path == (
            "/v1.0/users/test@example.com/mailFolders/inbox/messages"
        )
        assert request.url.params["$skiptoken"] == "page-2"
        assert request.headers["Authorization"] == "Bearer test-token"

        return httpx.Response(
            200,
            json={
                "value": [
                    {
                        "id": "message-2",
                        "conversationId": "conversation-1",
                    }
                ]
            },
        )

    provider = OutlookProvider(
        access_token="test-token",
        client=make_client(handler),
    )

    page = provider.sync_page(
        account_id="test@example.com",
        cursor=next_link,
        max_results=5,
    )

    assert page.messages == [
        {
            "id": "message-2",
            "conversationId": "conversation-1",
        }
    ]
    assert page.next_cursor is None


def test_outlook_message_normalization_extracts_attachment_metadata():
    provider = OutlookProvider.__new__(OutlookProvider)

    raw_message = {
        "id": "message-attachment-1",
        "conversationId": "conversation-attachment-1",
        "from": {
            "emailAddress": {
                "name": "Sender",
                "address": "sender@example.com",
            }
        },
        "toRecipients": [
            {
                "emailAddress": {
                    "name": "Recipient",
                    "address": "recipient@example.com",
                }
            }
        ],
        "subject": "Document",
        "body": {
            "content": "Please see the attached document.",
        },
        "receivedDateTime": "2026-09-26T12:00:00Z",
        "isRead": False,
        "hasAttachments": True,
        "attachments": [
            {
                "id": "attachment-1",
                "name": "report.pdf",
                "contentType": "application/pdf",
                "size": 12345,
                "isInline": False,
            }
        ],
    }

    message = provider.normalize_message(
        account_id="test@example.com",
        raw_message=raw_message,
    )

    assert message.has_attachments is True
    assert len(message.attachments) == 1

    attachment = message.attachments[0]

    assert attachment.provider_attachment_id == "attachment-1"
    assert attachment.filename == "report.pdf"
    assert attachment.content_type == "application/pdf"
    assert attachment.size_bytes == 12345
    assert attachment.is_inline is False


def test_outlook_sync_changes_initial_delta_page():
    def handler(request):
        assert request.url.path == "/v1.0/users/test@example.com/mailFolders/inbox/messages/delta"
        assert request.url.params["$top"] == "5"
        assert request.headers["Authorization"] == "Bearer test-token"

        return httpx.Response(
            200,
            json={
                "value": [{"id": "message-1", "conversationId": "conversation-1"}],
                "@odata.nextLink": "https://graph.microsoft.com/v1.0/users/test@example.com/mailFolders/inbox/messages/delta?$skiptoken=delta-page-2",
                "@odata.deltaLink": "https://graph.microsoft.com/v1.0/users/test@example.com/mailFolders/inbox/messages/delta?$deltatoken=delta-100",
            },
        )

    provider = OutlookProvider(
        access_token="test-token",
        client=make_client(handler),
    )

    changes = provider.sync_changes(
        account_id="test@example.com",
        max_results=5,
    )

    assert len(changes.changes) == 1
    assert changes.changes[0].change_type == "upsert"
    assert changes.changes[0].message_id == "message-1"
    assert changes.changes[0].message == {
        "id": "message-1",
        "conversationId": "conversation-1",
    }
    assert changes.next_cursor == "https://graph.microsoft.com/v1.0/users/test@example.com/mailFolders/inbox/messages/delta?$skiptoken=delta-page-2"
    assert changes.checkpoint_cursor == "https://graph.microsoft.com/v1.0/users/test@example.com/mailFolders/inbox/messages/delta?$deltatoken=delta-100"
    assert changes.has_more is True


def test_outlook_sync_changes_uses_next_link_for_continuation():
    next_link = "https://graph.microsoft.com/v1.0/users/test@example.com/mailFolders/inbox/messages/delta?$skiptoken=delta-page-2"

    def handler(request):
        assert request.url.path == (
            "/v1.0/users/test@example.com/mailFolders/inbox/messages/delta"
        )
        assert request.url.params["$skiptoken"] == "delta-page-2"
        assert request.headers["Authorization"] == "Bearer test-token"

        return httpx.Response(
            200,
            json={
                "value": [
                    {
                        "id": "message-2",
                        "conversationId": "conversation-1",
                    }
                ],
                "@odata.deltaLink": "https://graph.microsoft.com/v1.0/users/test@example.com/mailFolders/inbox/messages/delta?$deltatoken=delta-100",
            },
        )

    provider = OutlookProvider(
        access_token="test-token",
        client=make_client(handler),
    )

    changes = provider.sync_changes(
        account_id="test@example.com",
        page_cursor=next_link,
        max_results=5,
    )

    assert len(changes.changes) == 1
    assert changes.changes[0].change_type == "upsert"
    assert changes.changes[0].message_id == "message-2"
    assert changes.changes[0].message == {
        "id": "message-2",
        "conversationId": "conversation-1",
    }
    assert changes.next_cursor is None
    assert changes.checkpoint_cursor == "https://graph.microsoft.com/v1.0/users/test@example.com/mailFolders/inbox/messages/delta?$deltatoken=delta-100"
    assert changes.has_more is False


def test_outlook_sync_changes_intermediate_page_does_not_advance_checkpoint():
    next_link = "https://graph.microsoft.com/v1.0/users/test@example.com/mailFolders/inbox/messages/delta?$skiptoken=delta-page-2"

    def handler(request):
        assert request.url.params["$skiptoken"] == "delta-page-2"

        return httpx.Response(
            200,
            json={
                "value": [
                    {
                        "id": "message-2",
                        "conversationId": "conversation-1",
                    }
                ],
                "@odata.nextLink": next_link + "-3",
            },
        )

    provider = OutlookProvider(
        access_token="test-token",
        client=make_client(handler),
    )

    changes = provider.sync_changes(
        account_id="test@example.com",
        page_cursor=next_link,
        max_results=5,
    )

    assert changes.next_cursor == next_link + "-3"
    assert changes.checkpoint_cursor is None
    assert changes.has_more is True


def test_outlook_sync_changes_maps_removed_message_to_delete():
    def handler(request):
        return httpx.Response(
            200,
            json={
                "value": [
                    {
                        "id": "message-deleted",
                        "@removed": {
                            "reason": "deleted",
                        },
                    }
                ],
                "@odata.deltaLink": "https://graph.microsoft.com/v1.0/users/test@example.com/mailFolders/inbox/messages/delta?$deltatoken=delta-101",
            },
        )

    provider = OutlookProvider(
        access_token="test-token",
        client=make_client(handler),
    )

    changes = provider.sync_changes(
        account_id="test@example.com",
        max_results=5,
    )

    assert len(changes.changes) == 1
    assert changes.changes[0].change_type == "delete"
    assert changes.changes[0].message_id == "message-deleted"
    assert changes.changes[0].message is None
