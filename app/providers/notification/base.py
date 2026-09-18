from abc import ABC, abstractmethod

from app.schemas.notification import Notification


class NotificationProvider(ABC):
    """Common interface for all notification providers."""

    @abstractmethod
    def send_notification(
        self,
        notification: Notification,
    ) -> str:
        """Deliver a notification and return its provider ID."""
        raise NotImplementedError
