import base64
from datetime import datetime
from email.message import EmailMessage as MimeEmailMessage
from email.utils import parsedate_to_datetime

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from app.providers.email.base import EmailProvider
from app.schemas.provider import EmailAddress, EmailMessage


class GmailProvider(EmailProvider):
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
            has_attachments=self._has_attachments(
                raw_message.get("payload", {})
            ),
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
