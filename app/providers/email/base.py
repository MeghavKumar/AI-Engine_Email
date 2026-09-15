from abc import ABC, abstractmethod


class EmailProvider(ABC):
    """Common interface for all email providers."""

    @abstractmethod
    def list_messages(
        self,
        account_id: str,
        max_results: int = 25,
    ) -> list[dict]:
        """Return messages from the user's mailbox."""
        raise NotImplementedError

    @abstractmethod
    def get_message(
        self,
        account_id: str,
        message_id: str,
    ) -> dict:
        """Return a single message."""
        raise NotImplementedError

    @abstractmethod
    def send_message(
        self,
        account_id: str,
        message: dict,
    ) -> str:
        """Send a message and return its provider ID."""
        raise NotImplementedError

    @abstractmethod
    def mark_read(
        self,
        account_id: str,
        message_id: str,
    ) -> None:
        """Mark a message as read."""
        raise NotImplementedError

    @abstractmethod
    def archive_message(
        self,
        account_id: str,
        message_id: str,
    ) -> None:
        """Archive a message."""
        raise NotImplementedError

    @abstractmethod
    def get_thread(
        self,
        account_id: str,
        thread_id: str,
    ) -> list[dict]:
        """Return all messages in a thread."""
        raise NotImplementedError
