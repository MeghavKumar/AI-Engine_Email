from app.schemas.reminder import ReminderDraft
from app.security.gateway import SecurityGateway


class ReminderSecurityService:
    """Run security checks before a reminder enters human approval."""

    def __init__(
        self,
        security_gateway: SecurityGateway | None = None,
    ):
        self.security_gateway = (
            security_gateway or SecurityGateway()
        )

    def inspect(
        self,
        reminder: ReminderDraft,
    ):
        text = f"{reminder.subject}\n\n{reminder.body}"

        return self.security_gateway.inspect_text(text)
