from app.providers.email.base import EmailProvider
from app.schemas.attachment import (
    AttachmentVerificationResult,
    AttachmentVerificationStatus,
)
from app.schemas.email_attachment import EmailAttachment
from app.schemas.reminder import ReminderDraft, ReminderStatus


class ReminderSendService:
    """Safely send a human-approved reminder."""

    def __init__(self, provider: EmailProvider):
        self.provider = provider

    def send(
        self,
        reminder: ReminderDraft,
        account_id: str,
        attachment_verification: AttachmentVerificationResult | None = None,
        attachments: list[EmailAttachment] | None = None,
    ) -> str:
        attachments = attachments or []

        self._validate_ready_state(
            reminder=reminder,
            attachment_verification=attachment_verification,
            attachments=attachments,
        )

        message = {
            "to": [str(recipient) for recipient in reminder.to],
            "cc": [str(recipient) for recipient in reminder.cc],
            "subject": reminder.subject,
            "body": reminder.body,
            "attachments": attachments,
        }

        return self.provider.send_message(
            account_id=account_id,
            message=message,
        )

    def _validate_ready_state(
        self,
        reminder: ReminderDraft,
        attachment_verification: AttachmentVerificationResult | None,
        attachments: list[EmailAttachment],
    ) -> None:
        if reminder.status != ReminderStatus.APPROVED:
            raise ValueError(
                "Reminder is not approved for sending."
            )

        if not reminder.attachment_required:
            return

        if attachment_verification is None:
            raise ValueError(
                "Attachment verification is required before sending."
            )

        if (
            attachment_verification.status
            != AttachmentVerificationStatus.VERIFIED
        ):
            raise ValueError(
                "Required attachments are not verified for sending."
            )

        required_names = {
            name.strip().lower()
            for name in reminder.attachment_names
        }

        provided_names = {
            attachment.filename.strip().lower()
            for attachment in attachments
        }

        missing_names = required_names - provided_names

        if missing_names:
            missing_display = ", ".join(sorted(missing_names))
            raise ValueError(
                f"Required attachments are not included in the send: "
                f"{missing_display}"
            )
