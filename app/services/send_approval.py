from app.schemas.email import ApprovalRequest
from app.schemas.workflow import (
    EmailWorkflowState,
    EmailWorkflowStatus,
)
from app.services.approval import ApprovalService


class SendApprovalService:
    """Create human approval requests for email sending."""

    def __init__(
        self,
        approval_service: ApprovalService | None = None,
    ):
        self.approval_service = (
            approval_service or ApprovalService()
        )

    def create_request(
        self,
        state: EmailWorkflowState,
        request_id: str,
        requested_by: str,
    ) -> ApprovalRequest:
        """Create a send approval request for a validated workflow."""

        if state.status != EmailWorkflowStatus.SEND_APPROVAL:
            raise ValueError(
                "Email workflow must pass pre-send validation "
                "before requesting send approval."
            )

        if state.draft is None:
            raise ValueError(
                "Email draft is required before requesting send approval."
            )

        request = self.approval_service.create_request(
            request_id=request_id,
            requested_by=requested_by,
            reason=(
                "Email passed pre-send validation and requires "
                "human approval before sending."
            ),
        )

        state.send_approval_request = request

        return request
