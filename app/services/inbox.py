from app.providers.email.base import EmailProvider
from app.schemas.provider import EmailMessage


class InboxService:
    """Provider-independent service for reading inbox messages."""

    def __init__(self, provider: EmailProvider):
        self.provider = provider

    def get_inbox(
        self,
        account_id: str,
        max_results: int = 25,
    ) -> list[EmailMessage]:
        """Read and normalize messages from the user's inbox."""

        raw_messages = self.provider.list_messages(
            account_id=account_id,
            max_results=max_results,
        )

        messages: list[EmailMessage] = []

        for raw_message in raw_messages:
            message_id = raw_message["id"]

            full_message = self.provider.get_message(
                account_id=account_id,
                message_id=message_id,
            )

            if hasattr(self.provider, "normalize_message"):
                normalized = self.provider.normalize_message(
                    account_id=account_id,
                    raw_message=full_message,
                )
                messages.append(normalized)

        return messages
