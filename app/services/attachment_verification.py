from app.schemas.attachment import (
    AttachmentVerificationResult,
    AttachmentVerificationStatus,
)


class AttachmentVerificationService:
    """Verify that required email attachments are available."""

    def verify(
        self,
        required: bool,
        required_attachments: list[str] | None = None,
        available_attachments: list[str] | None = None,
    ) -> AttachmentVerificationResult:
        """Check whether all required attachments are present."""

        required_attachments = required_attachments or []
        available_attachments = available_attachments or []

        if not required:
            return AttachmentVerificationResult(
                status=AttachmentVerificationStatus.NOT_REQUIRED,
                required=False,
                reason="No attachment is required.",
            )

        available_normalized = {
            name.strip().lower()
            for name in available_attachments
        }

        missing_attachments = [
            name
            for name in required_attachments
            if name.strip().lower() not in available_normalized
        ]

        if missing_attachments:
            return AttachmentVerificationResult(
                status=AttachmentVerificationStatus.MISSING,
                required=True,
                attachment_names=required_attachments,
                missing_attachments=missing_attachments,
                reason="One or more required attachments are missing.",
            )

        return AttachmentVerificationResult(
            status=AttachmentVerificationStatus.VERIFIED,
            required=True,
            attachment_names=required_attachments,
            reason="All required attachments are present.",
        )
