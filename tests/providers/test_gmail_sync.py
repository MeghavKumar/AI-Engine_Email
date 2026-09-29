from app.providers.email.gmail import GmailProvider
from app.schemas.sync import SyncChanges, SyncPage


class FakeRequest:
    def __init__(self, response):
        self.response = response

    def execute(self):
        return self.response


class FakeMessagesResource:
    def __init__(self, expected_kwargs, response):
        self.expected_kwargs = expected_kwargs
        self.response = response
        self.actual_kwargs = None

    def list(self, **kwargs):
        self.actual_kwargs = kwargs
        return FakeRequest(self.response)


class FakeUsersResource:
    def __init__(self, messages_resource):
        self.messages_resource = messages_resource

    def messages(self):
        return self.messages_resource


class FakeService:
    def __init__(self, messages_resource):
        self.messages_resource = messages_resource

    def users(self):
        return FakeUsersResource(self.messages_resource)


def make_provider(expected_kwargs, response):
    messages_resource = FakeMessagesResource(
        expected_kwargs=expected_kwargs,
        response=response,
    )

    provider = GmailProvider.__new__(GmailProvider)
    provider.service = FakeService(messages_resource)

    return provider, messages_resource


def test_gmail_sync_page_initial_page():
    provider, messages_resource = make_provider(
        expected_kwargs={
            "userId": "me",
            "labelIds": ["INBOX"],
            "maxResults": 5,
        },
        response={
            "messages": [
                {
                    "id": "message-1",
                    "threadId": "thread-1",
                }
            ],
            "nextPageToken": "page-2",
        },
    )

    page = provider.sync_page(
        account_id="test@example.com",
        max_results=5,
    )

    assert isinstance(page, SyncPage)
    assert page.messages == [
        {
            "id": "message-1",
            "threadId": "thread-1",
        }
    ]
    assert page.next_cursor == "page-2"
    assert messages_resource.actual_kwargs == {
        "userId": "me",
        "labelIds": ["INBOX"],
        "maxResults": 5,
    }


def test_gmail_sync_page_uses_cursor():
    provider, messages_resource = make_provider(
        expected_kwargs={
            "userId": "me",
            "labelIds": ["INBOX"],
            "maxResults": 5,
            "pageToken": "page-2",
        },
        response={
            "messages": [
                {
                    "id": "message-2",
                    "threadId": "thread-1",
                }
            ],
        },
    )

    page = provider.sync_page(
        account_id="test@example.com",
        cursor="page-2",
        max_results=5,
    )

    assert page.messages == [
        {
            "id": "message-2",
            "threadId": "thread-1",
        }
    ]
    assert page.next_cursor is None
    assert messages_resource.actual_kwargs == {
        "userId": "me",
        "labelIds": ["INBOX"],
        "maxResults": 5,
        "pageToken": "page-2",
    }


def test_gmail_normalize_message_extracts_attachment_metadata():
    provider = GmailProvider.__new__(GmailProvider)

    raw_message = {
        "id": "message-attachment-1",
        "threadId": "thread-attachment-1",
        "labelIds": ["INBOX"],
        "payload": {
            "mimeType": "multipart/mixed",
            "headers": [
                {
                    "name": "From",
                    "value": "Sender <sender@example.com>",
                },
                {
                    "name": "To",
                    "value": "Recipient <recipient@example.com>",
                },
                {
                    "name": "Subject",
                    "value": "Document",
                },
            ],
            "parts": [
                {
                    "mimeType": "text/plain",
                    "filename": "",
                    "body": {
                        "data": "",
                    },
                },
                {
                    "mimeType": "application/pdf",
                    "filename": "report.pdf",
                    "body": {
                        "attachmentId": "attachment-1",
                        "size": 12345,
                    },
                },
            ],
        },
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


class FakeHistoryResource:
    def __init__(self, response):
        self.response = response
        self.actual_kwargs = None

    def list(self, **kwargs):
        self.actual_kwargs = kwargs
        return FakeRequest(self.response)


class FakeIncrementalUsersResource:
    def __init__(self, history_resource):
        self.history_resource = history_resource

    def history(self):
        return self.history_resource


class FakeIncrementalService:
    def __init__(self, history_resource):
        self.history_resource = history_resource

    def users(self):
        return FakeIncrementalUsersResource(self.history_resource)


def test_gmail_sync_changes_uses_history_cursor():
    history_resource = FakeHistoryResource(
        response={
            "history": [
                {
                    "id": "history-101",
                    "messagesAdded": [
                        {
                            "message": {
                                "id": "message-1",
                                "threadId": "thread-1",
                            }
                        }
                    ],
                }
            ],
            "nextPageToken": "history-page-2",
            "historyId": "history-102",
        }
    )

    provider = GmailProvider.__new__(GmailProvider)
    provider.service = FakeIncrementalService(history_resource)

    changes = provider.sync_changes(
        account_id="test@example.com",
        checkpoint_cursor="history-100",
        max_results=5,
    )

    assert isinstance(changes, SyncChanges)
    assert len(changes.changes) == 1
    assert changes.changes[0].change_type == "upsert"
    assert changes.changes[0].message_id == "message-1"
    assert changes.changes[0].message == {
        "id": "message-1",
        "threadId": "thread-1",
    }
    assert changes.next_cursor == "history-page-2"
    assert changes.checkpoint_cursor == "history-102"
    assert changes.has_more is True
    assert history_resource.actual_kwargs == {
        "userId": "me",
        "maxResults": 5,
        "startHistoryId": "history-100",
    }


def test_gmail_sync_changes_intermediate_page_does_not_advance_checkpoint():
    history_resource = FakeHistoryResource(
        response={
            "history": [
                {
                    "id": "history-101",
                    "messagesAdded": [
                        {
                            "message": {
                                "id": "message-1",
                                "threadId": "thread-1",
                            }
                        }
                    ],
                }
            ],
            "nextPageToken": "history-page-2",
        }
    )

    provider = GmailProvider.__new__(GmailProvider)
    provider.service = FakeIncrementalService(history_resource)

    changes = provider.sync_changes(
        account_id="test@example.com",
        checkpoint_cursor="history-100",
        max_results=5,
    )

    assert changes.next_cursor == "history-page-2"
    assert changes.checkpoint_cursor is None
    assert changes.has_more is True


def test_gmail_sync_changes_uses_page_cursor_for_continuation():
    history_resource = FakeHistoryResource(
        response={
            "history": [
                {
                    "id": "history-102",
                    "messagesAdded": [
                        {
                            "message": {
                                "id": "message-2",
                                "threadId": "thread-2",
                            }
                        }
                    ],
                }
            ],
            "historyId": "history-103",
        }
    )

    provider = GmailProvider.__new__(GmailProvider)
    provider.service = FakeIncrementalService(history_resource)

    changes = provider.sync_changes(
        account_id="test@example.com",
        checkpoint_cursor="history-100",
        page_cursor="history-page-2",
        max_results=5,
    )

    assert changes.changes[0].message_id == "message-2"
    assert changes.next_cursor is None
    assert changes.checkpoint_cursor == "history-103"
    assert changes.has_more is False

    assert history_resource.actual_kwargs == {
        "userId": "me",
        "maxResults": 5,
        "pageToken": "history-page-2",
    }
