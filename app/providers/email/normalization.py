from abc import ABC, abstractmethod

from app.schemas.provider import EmailMessage


class NormalizedEmailProvider(ABC):
    """Optional capability for retrieving and normalizing email messages."""

    @abstractmethod
    def get_message(
        self,
        account_id: str,
        message_id: str,
    ) -> dict:
        """Return one raw provider message."""
        raise NotImplementedError

    @abstractmethod
    def normalize_message(
        self,
        account_id: str,
        raw_message: dict,
    ) -> EmailMessage:
        """Convert a provider message into the shared schema."""
        raise NotImplementedError
