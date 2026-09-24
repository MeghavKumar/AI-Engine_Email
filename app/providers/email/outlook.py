from datetime import datetime
from pathlib import Path

import httpx

from app.providers.email.base import EmailProvider
from app.schemas.provider import EmailMessage


class OutlookProvider(EmailProvider):
    """
    Microsoft Graph implementation of EmailProvider.

    The HTTP client can be injected for tests, allowing the provider
    to be developed without connecting to a real Microsoft mailbox.
    """

    GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"

    def __init__(
        self,
        access_token: str | None = None,
        client: httpx.Client | None = None,
    ):
        self.access_token = access_token
        self.client = client or httpx.Client(
            base_url=self.GRAPH_BASE_URL,
            timeout=30,
        )

    def _headers(self) -> dict[str, str]:
        if not self.access_token:
            return {}

        return {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
        }

    def list_messages(
        self,
        account_id: str,
        max_results: int = 25,
    ) -> list[dict]:
        response = self.client.get(
            f"/users/{account_id}/mailFolders/inbox/messages",
            headers=self._headers(),
            params={
                "$top": max_results,
                "$orderby": "receivedDateTime DESC",
            },
        )
        response.raise_for_status()

        data = response.json()
        return data.get("value", [])

    def get_message(
        self,
        account_id: str,
        message_id: str,
    ) -> dict:
        response = self.client.get(
            f"/users/{account_id}/messages/{message_id}",
            headers=self._headers(),
        )
        response.raise_for_status()
        return response.json()

    def send_message(
        self,
        account_id: str,
        message: dict,
    ) -> str:
        """Send an email through Microsoft Graph."""
        import base64

        to = message.get("to", [])
        cc = message.get("cc", [])
        bcc = message.get("bcc", [])

        if not to:
            raise ValueError("At least one recipient is required.")

        def recipient(address: str) -> dict:
            return {
                "emailAddress": {
                    "address": address,
                }
            }

        graph_message = {
            "subject": message.get("subject", ""),
            "body": {
                "contentType": "Text",
                "content": message.get("body", ""),
            },
            "toRecipients": [
                recipient(address)
                for address in to
            ],
        }

        if cc:
            graph_message["ccRecipients"] = [
                recipient(address)
                for address in cc
            ]

        if bcc:
            graph_message["bccRecipients"] = [
                recipient(address)
                for address in bcc
            ]

        attachments = message.get("attachments", [])

        if attachments:
            graph_message["attachments"] = []

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

                graph_message["attachments"].append(
                    {
                        "@odata.type": "#microsoft.graph.fileAttachment",
                        "name": attachment.filename,
                        "contentType": content_type,
                        "contentBytes": base64.b64encode(
                            file_path.read_bytes()
                        ).decode("ascii"),
                    }
                )

        response = self.client.post(
            f"/users/{account_id}/sendMail",
            headers={
                **self._headers(),
                "Content-Type": "application/json",
            },
            json={
                "message": graph_message,
                "saveToSentItems": True,
            },
        )
        response.raise_for_status()

        return response.headers.get(
            "request-id",
            "outlook-send-request",
        )

    def mark_read(
        self,
        account_id: str,
        message_id: str,
    ) -> None:
        response = self.client.patch(
            f"/users/{account_id}/messages/{message_id}",
            headers={
                **self._headers(),
                "Content-Type": "application/json",
            },
            json={
                "isRead": True,
            },
        )
        response.raise_for_status()

    def archive_message(
        self,
        account_id: str,
        message_id: str,
    ) -> None:
        response = self.client.post(
            f"/users/{account_id}/messages/{message_id}/move",
            headers={
                **self._headers(),
                "Content-Type": "application/json",
            },
            json={
                "destinationId": "archive",
            },
        )
        response.raise_for_status()

    def get_thread(
        self,
        account_id: str,
        thread_id: str,
    ) -> list[dict]:
        response = self.client.get(
            f"/users/{account_id}/messages",
            headers=self._headers(),
            params={
                "$filter": f"conversationId eq '{thread_id}'",
                "$orderby": "receivedDateTime ASC",
            },
        )
        response.raise_for_status()

        data = response.json()
        return data.get("value", [])

    @staticmethod
    def _parse_address(value: dict | None) -> dict:
        email_address = (value or {}).get("emailAddress", {})
        return {
            "name": email_address.get("name"),
            "email": email_address.get("address", ""),
        }

    @classmethod
    def _parse_addresses(cls, values: list[dict] | None) -> list[dict]:
        return [
            cls._parse_address(value)
            for value in (values or [])
        ]

    @staticmethod
    def _extract_body_text(raw_message: dict) -> str:
        body = raw_message.get("body") or {}
        return body.get("content") or ""

    @staticmethod
    def _parse_datetime(value: str | None) -> datetime | None:
        if not value:
            return None

        return datetime.fromisoformat(value.replace("Z", "+00:00"))

    def normalize_message(
        self,
        account_id: str,
        raw_message: dict,
    ) -> EmailMessage:
        sender = self._parse_address(raw_message.get("from"))
        recipients = self._parse_addresses(
            raw_message.get("toRecipients")
        )
        cc = self._parse_addresses(
            raw_message.get("ccRecipients")
        )

        return EmailMessage(
            provider="outlook",
            account_id=account_id,
            message_id=raw_message.get("id", ""),
            thread_id=raw_message.get("conversationId"),
            sender=sender,
            recipients=recipients,
            cc=cc,
            subject=raw_message.get("subject") or "",
            body_text=self._extract_body_text(raw_message),
            received_at=self._parse_datetime(
                raw_message.get("receivedDateTime")
            ),
            is_read=bool(raw_message.get("isRead", False)),
            has_attachments=bool(
                raw_message.get("hasAttachments", False)
            ),
            labels=[],
        )
