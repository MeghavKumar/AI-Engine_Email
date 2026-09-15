from app.schemas.recipient import (
    RecipientCandidate,
    RecipientVerificationDecision,
    RecipientVerificationRequest,
    RecipientVerificationStatus,
)


class RecipientVerificationService:
    """Manage human verification of discovered recipients."""

    def create_request(
        self,
        request_id: str,
        recipients: list[RecipientCandidate],
        requested_by: str,
    ) -> RecipientVerificationRequest:
        """Create a pending recipient verification request."""

        return RecipientVerificationRequest(
            request_id=request_id,
            recipients=recipients,
            requested_by=requested_by,
        )

    def approve(
        self,
        request: RecipientVerificationRequest,
        decided_by: str,
        approved_recipients: list[RecipientCandidate],
        comment: str | None = None,
    ) -> RecipientVerificationDecision:
        """Approve a recipient list after human verification."""

        return RecipientVerificationDecision(
            request_id=request.request_id,
            status=RecipientVerificationStatus.APPROVED,
            decided_by=decided_by,
            approved_recipients=approved_recipients,
            comment=comment,
        )

    def reject(
        self,
        request: RecipientVerificationRequest,
        decided_by: str,
        comment: str | None = None,
    ) -> RecipientVerificationDecision:
        """Reject a recipient verification request."""

        return RecipientVerificationDecision(
            request_id=request.request_id,
            status=RecipientVerificationStatus.REJECTED,
            decided_by=decided_by,
            approved_recipients=[],
            comment=comment,
        )
