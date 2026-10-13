from app.schemas.email import ApprovalRequest, ApprovalStatus
from app.schemas.workflow import EmailWorkflowState, EmailWorkflowStatus
from app.services.approval import ApprovalService
from app.services.draft_integrity import draft_fingerprint
from app.services.subject_change_approval import SubjectChangeApprovalService


class SendApprovalService:
    """Create human approval requests for email sending."""

    def __init__(self, approval_service: ApprovalService | None = None):
        self.approval_service = approval_service or ApprovalService()
        self.subject_approval = SubjectChangeApprovalService()

    def create_request(
        self,
        state: EmailWorkflowState,
        request_id: str,
        requested_by: str,
    ) -> ApprovalRequest:
        """Create a send request only after required subject approval."""

        if state.status != EmailWorkflowStatus.SEND_APPROVAL:
            raise ValueError(
                "Email workflow must pass pre-send validation "
                "before requesting send approval."
            )
        if state.draft is None:
            raise ValueError(
                "Email draft is required before requesting send approval."
            )

        if self.subject_approval.requires_approval(state):
            decision = state.subject_change_approval_decision
            fingerprint = state.subject_change_approval_fingerprint
            if (
                decision is None
                or decision.status != ApprovalStatus.APPROVED
                or fingerprint is None
                or fingerprint != draft_fingerprint(state)
            ):
                raise ValueError(
                    "Subject change requires explicit approval before send approval."
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
        state.send_approval_decision = None
        state.approved_draft_fingerprint = draft_fingerprint(state)
        return request
