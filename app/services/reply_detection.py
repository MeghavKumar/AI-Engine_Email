from email.utils import getaddresses, parseaddr

from app.providers.email.base import EmailProvider
from app.schemas.reply import ReplyDetectionResult


class ReplyDetectionService:
    """Detect inbound replies and determine a proposed reply audience."""

    def __init__(self, provider: EmailProvider):
        self.provider = provider

    def detect_reply(
        self,
        account_id: str,
        thread_id: str,
        account_email: str,
    ) -> ReplyDetectionResult:
        messages = self.provider.get_thread(
            account_id=account_id,
            thread_id=thread_id,
        )

        normalized_account_email = account_email.lower()

        for message in messages:
            sender = self._get_sender_email(message)

            if (
                sender
                and sender.lower() != normalized_account_email
            ):
                reply_to = self._get_addresses(message, "to")
                reply_cc = self._get_addresses(message, "cc")

                suggested_reply_to = [sender]
                suggested_reply_cc = [
                    address
                    for address in reply_cc
                    if address.lower() != normalized_account_email
                    and address.lower() != sender.lower()
                ]

                return ReplyDetectionResult(
                    replied=True,
                    reply_message_id=message.get("id"),
                    reply_from=sender,
                    reply_to=reply_to,
                    reply_cc=reply_cc,
                    suggested_reply_to=suggested_reply_to,
                    suggested_reply_cc=suggested_reply_cc,
                    requires_recipient_confirmation=True,
                )

        return ReplyDetectionResult(
            replied=False,
            requires_recipient_confirmation=True,
        )


    def _get_sender_email(self, message: dict) -> str | None:
        headers = self._get_headers(message)
        sender = headers.get("from")

        if sender:
            _, address = parseaddr(sender)
            if address:
                return address

        email_address = (
            message.get("from", {})
            .get("emailAddress", {})
            .get("address")
        )
        return email_address or None


    def _get_addresses(
        self,
        message: dict,
        header_name: str,
    ) -> list[str]:
        headers = self._get_headers(message)
        value = headers.get(header_name, "")

        if value:
            addresses = [
                address
                for _, address in getaddresses([value])
                if address
            ]
            if addresses:
                return addresses

        outlook_field = {
            "to": "toRecipients",
            "cc": "ccRecipients",
        }.get(header_name)

        if not outlook_field:
            return []

        return [
            address
            for recipient in message.get(outlook_field, [])
            if (
                address := recipient.get("emailAddress", {}).get("address")
            )
        ]

    def _get_headers(self, message: dict) -> dict[str, str]:
        return {
            header["name"].lower(): header["value"]
            for header in message.get("payload", {}).get("headers", [])
        }
