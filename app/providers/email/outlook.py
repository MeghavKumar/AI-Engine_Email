from app.providers.email.base import EmailProvider
from app.schemas.provider import EmailMessage


class OutlookProvider(EmailProvider):
    """
    Microsoft Graph implementation of EmailProvider.

    Authentication and live mailbox access will be added when
    a Microsoft mailbox is configured.
    """

    def __init__(self, access_token: str | None = None):
        self.access_token = access_token

    def list_messages(
        self,
        account_id: str,
        max_results: int = 25,
    ) -> list[dict]:
        raise NotImplementedError(
            "Outlook mailbox access requires Microsoft Graph authentication."
        )

    def get_message(
        self,
        account_id: str,
        message_id: str,
    ) -> dict:
        raise NotImplementedError(
            "Outlook mailbox access requires Microsoft Graph authentication."
        )

    def send_message(
        self,
        account_id: str,
        message: dict,
    ) -> str:
        raise NotImplementedError(
            "Outlook sending will be enabled after approval controls are implemented."
        )

    def mark_read(
        self,
        account_id: str,
        message_id: str,
    ) -> None:
        raise NotImplementedError(
            "Outlook write operations require Microsoft Graph authentication."
        )

    def archive_message(
        self,
        account_id: str,
        message_id: str,
    ) -> None:
        raise NotImplementedError(
            "Outlook write operations require Microsoft Graph authentication."
        )

    def get_thread(
        self,
        account_id: str,
        thread_id: str,
    ) -> list[dict]:
        raise NotImplementedError(
            "Outlook thread access requires Microsoft Graph authentication."
        )

    def normalize_message(
        self,
        account_id: str,
        raw_message: dict,
    ) -> EmailMessage:
        raise NotImplementedError(
            "Outlook normalization will be implemented with Microsoft Graph support."
        )
