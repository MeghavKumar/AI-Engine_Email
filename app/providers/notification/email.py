from app.providers.email.base import EmailProvider
from app.providers.notification.base import NotificationProvider
from app.schemas.notification import Notification


class EmailNotificationProvider(NotificationProvider):
    """Deliver notifications through an email provider."""

    def __init__(
        self,
        email_provider: EmailProvider,
        account_id: str,
        recipient_email: str,
    ):
        self.email_provider = email_provider
        self.account_id = account_id
        self.recipient_email = recipient_email

    def send_notification(
        self,
        notification: Notification,
    ) -> str:
        message = {
            "to": [self.recipient_email],
            "subject": notification.subject,
            "body": notification.message,
        }

        return self.email_provider.send_message(
            account_id=self.account_id,
            message=message,
        )
