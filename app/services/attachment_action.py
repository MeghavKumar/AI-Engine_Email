from app.schemas.attachment import (
    AttachmentVerificationRequest,
    AttachmentVerificationResult,
    AttachmentVerificationStatus,
)


class AttachmentActionService:
    """Create human-action requests for missing attachments."""

    def create_request(
        self,
        request_id: str,
        verification_result: AttachmentVerificationResult,
    ) -> AttachmentVerificationRequest:
        """Create a human-action request when attachments are missing."""

        if verification_result.status != AttachmentVerificationStatus.MISSING:
            raise ValueError(
                "Human attachment action is only required when "
                "attachments are missing."
            )

        if not verification_result.missing_attachments:
            raise ValueError(
                "Missing attachment list cannot be empty."
            )

        return AttachmentVerificationRequest(
            request_id=request_id,
            attachment_names=verification_result.missing_attachments,
        )
