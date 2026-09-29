import base64
from datetime import datetime
from pathlib import Path
from email.message import EmailMessage as MimeEmailMessage
from email.utils import parsedate_to_datetime

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from app.providers.email.base import EmailProvider
from app.providers.email.sync import IncrementalEmailSyncProvider
from app.schemas.provider import (
    EmailAddress,
    EmailAttachment,
    EmailMessage,
)
from app.schemas.sync import SyncChanges, SyncPage


class GmailProvider(EmailProvider, IncrementalEmailSyncProvider):
    """Gmail implementation of the EmailProvider interface."""

    def __init__(self, credentials: Credentials):
        self.credentials = credentials
        self.service = build(
            "gmail",
            "v1",
            credentials=credentials,
        )

    def list_messages(
        self,
        account_id: str,
        max_results: int = 25,
    ) -> list[dict]:
        response = (
            self.service.users()
            .messages()
            .list(
                userId="me",
                labelIds=["INBOX"],
                maxResults=max_results,
            )
            .execute()
        )

        return response.get("messages", [])

    def sync_page(
        self,
        account_id: str,
        cursor: str | None = None,
        max_results: int = 25,
    ) -> SyncPage:
        """Return one paginated inbox page from Gmail."""

        request = {
            "userId": "me",
            "labelIds": ["INBOX"],
            "maxResults": max_results,
        }

        if cursor is not None:
            request["pageToken"] = cursor

        response = (
            self.service.users()
            .messages()
            .list(**request)
            .execute()
        )

        return SyncPage(
            messages=response.get("messages", []),
            next_cursor=response.get("nextPageToken"),
        )

    def sync_changes(
        self,
        account_id: str,
        checkpoint_cursor: str | None = None,
        page_cursor: str | None = None,
        max_results: int = 25,
    ) -> SyncChanges:
        """Return Gmail history changes since the supplied history ID."""

        request = {
            "userId": "me",
            "maxResults": max_results,
        }

        if page_cursor is not None:
            request["pageToken"] = page_cursor
        elif checkpoint_cursor is not None:
            request["startHistoryId"] = checkpoint_cursor

        response = (
            self.service.users()
            .history()
            .list(**request)
            .execute()
        )

        changes = []

        for history_record in response.get("history", []):
            for item in history_record.get("messagesAdded", []):
                message = item.get("message", {})
                message_id = message.get("id")
                if message_id:
                    changes.append(
                        {
                            "change_type": "upsert",
                            "message_id": message_id,
                            "message": message,
                        }
                    )

            for item in history_record.get("labelsAdded", []):
                message = item.get("message", {})
                message_id = message.get("id")
                if message_id:
                    changes.append(
                        {
                            "change_type": "upsert",
                            "message_id": message_id,
                            "message": message,
                        }
                    )

            for item in history_record.get("labelsRemoved", []):
                message = item.get("message", {})
                message_id = message.get("id")
                if message_id:
                    changes.append(
                        {
                            "change_type": "upsert",
                            "message_id": message_id,
                            "message": message,
                        }
                    )

            for item in history_record.get("messagesDeleted", []):
                message = item.get("message", {})
                message_id = message.get("id")
                if message_id:
                    changes.append(
                        {
                            "change_type": "delete",
                            "message_id": message_id,
                        }
                    )

        return SyncChanges(
            changes=changes,
            next_cursor=response.get("nextPageToken"),
            checkpoint_cursor=response.get("historyId"),
            has_more=bool(response.get("nextPageToken")),
        )

    def get_message(
        self,
        account_id: str,
        message_id: str,
    ) -> dict:
        return (
            self.service.users()
            .messages()
            .get(
                userId="me",
                id=message_id,
                format="full",
            )
            .execute()
        )

    def normalize_message(
        self,
        account_id: str,
        raw_message: dict,
    ) -> EmailMessage:
        headers = {
            header["name"].lower(): header["value"]
            for header in raw_message
            .get("payload", {})
            .get("headers", [])
        }

        sender = self._parse_address(
            headers.get("from", "")
        )

        recipients = self._parse_addresses(
            headers.get("to", "")
        )

        cc = self._parse_addresses(
            headers.get("cc", "")
        )

        body_text = self._extract_text(
            raw_message.get("payload", {})
        )

        received_at = self._parse_date(
            headers.get("date")
        )

        labels = raw_message.get("labelIds", [])
        attachments = self._extract_attachments(
            raw_message.get("payload", {})
        )

        return EmailMessage(
            provider="gmail",
            account_id=account_id,
            message_id=raw_message["id"],
            thread_id=raw_message.get("threadId"),
            sender=sender,
            recipients=recipients,
            cc=cc,
            subject=headers.get("subject", ""),
            body_text=body_text,
            received_at=received_at,
            is_read="UNREAD" not in labels,
            has_attachments=bool(attachments),
            attachments=attachments,
            labels=labels,
        )

    def _parse_address(
        self,
        value: str,
    ) -> EmailAddress:
        from email.utils import parseaddr

        name, address = parseaddr(value)

        return EmailAddress(
            name=name or None,
            email=address,
        )

    def _parse_addresses(
        self,
        value: str,
    ) -> list[EmailAddress]:
        from email.utils import getaddresses

        return [
            EmailAddress(
                name=name or None,
                email=address,
            )
            for name, address in getaddresses(
                [value]
            )
            if address
        ]

    def _extract_text(
        self,
        payload: dict,
    ) -> str:
        mime_type = payload.get("mimeType", "")

        if mime_type == "text/plain":
            data = payload.get("body", {}).get("data")

            if data:
                return base64.urlsafe_b64decode(
                    data
                ).decode(
                    "utf-8",
                    errors="replace",
                )

        for part in payload.get("parts", []):
            text = self._extract_text(part)

            if text:
                return text

        return ""

    def _parse_date(
        self,
        value: str | None,
    ) -> datetime | None:
        if not value:
            return None

        try:
            return parsedate_to_datetime(value)
        except (TypeError, ValueError):
            return None

    def _extract_attachments(
        self,
        payload: dict,
    ) -> list[EmailAttachment]:
        attachments: list[EmailAttachment] = []

        filename = payload.get("filename", "")
        body = payload.get("body", {})

        if filename:
            attachment_id = body.get("attachmentId")

            if attachment_id:
                attachments.append(
                    EmailAttachment(
                        provider_attachment_id=attachment_id,
                        filename=filename,
                        content_type=payload.get("mimeType"),
                        size_bytes=body.get("size"),
                        is_inline=payload.get(
                            "disposition",
                            "",
                        ).lower()
                        == "inline",
                    )
                )

        for part in payload.get("parts", []):
            attachments.extend(
                self._extract_attachments(part)
            )

        return attachments

    def _has_attachments(
        self,
        payload: dict,
    ) -> bool:
        if payload.get("filename"):
            return True

        return any(
            self._has_attachments(part)
            for part in payload.get("parts", [])
        )

    def send_message(
        self,
        account_id: str,
        message: dict,
    ) -> str:
        """Send a plain-text email through Gmail."""
        mime_message = MimeEmailMessage()

        to = message.get("to", [])
        cc = message.get("cc", [])
        bcc = message.get("bcc", [])

        if not to:
            raise ValueError("At least one recipient is required.")

        mime_message["To"] = ", ".join(to)

        if cc:
            mime_message["Cc"] = ", ".join(cc)

        if bcc:
            mime_message["Bcc"] = ", ".join(bcc)

        mime_message["Subject"] = message.get("subject", "")
        mime_message.set_content(message.get("body", ""))

        attachments = message.get("attachments", [])

        for attachment in attachments:
            file_path = Path(attachment.file_path)

            if not file_path.is_file():
                raise ValueError(
                    f"Attachment file does not exist: {file_path}"
                )

            content_type = attachment.content_type

            if "/" not in content_type:
                raise ValueError(
                    f"Invalid attachment content type: {content_type}"
                )

            maintype, subtype = content_type.split("/", 1)

            mime_message.add_attachment(
                file_path.read_bytes(),
                maintype=maintype,
                subtype=subtype,
                filename=attachment.filename,
            )

        encoded_message = base64.urlsafe_b64encode(
            mime_message.as_bytes()
        ).decode("utf-8")

        response = (
            self.service.users()
            .messages()
            .send(
                userId="me",
                body={"raw": encoded_message},
            )
            .execute()
        )

        return response["id"]

    def mark_read(
        self,
        account_id: str,
        message_id: str,
    ) -> None:
        raise NotImplementedError(
            "Gmail write operations are disabled in the read-only phase."
        )

    def archive_message(
        self,
        account_id: str,
        message_id: str,
    ) -> None:
        raise NotImplementedError(
            "Gmail write operations are disabled in the read-only phase."
        )

    def get_thread(
        self,
        account_id: str,
        thread_id: str,
    ) -> list[dict]:
        response = (
            self.service.users()
            .threads()
            .get(
                userId="me",
                id=thread_id,
                format="full",
            )
            .execute()
        )

        return response.get("messages", [])
